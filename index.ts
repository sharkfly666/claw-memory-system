import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import type { IncomingMessage, ServerResponse } from "node:http";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

type PluginConfig = {
  pythonBin?: string;
  repoPath?: string;
  workspaceDir?: string;
  openclawHome?: string;
  openclawBin?: string;
  adminHost?: string;
  adminPort?: number | string;
  autoStartAdmin?: boolean;
  autoTurnCapture?: boolean;
  autoTurnQueueOnly?: boolean;
  turnCaptureMinConfidence?: number;
  batchGovernanceEnabled?: boolean;
  batchGovernanceEvery?: string;
};

type BridgePayload = {
  ok?: boolean;
  returncode?: number;
  stdout?: string;
  stderr?: string;
  parsed_stdout?: unknown;
  command?: string[];
};

type ChildResult = {
  stdout: string;
  stderr: string;
  returncode: number;
};

type AdminRuntimeManager = {
  baseUrl: string;
  ensureReady: () => Promise<void>;
  start: () => Promise<void>;
  stop: () => Promise<void>;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DEFAULT_WORKSPACE = "~/.openclaw/workspace";
const DEFAULT_OPENCLAW_HOME = "~/.openclaw";
const DEFAULT_ADMIN_HOST = "127.0.0.1";
const DEFAULT_ADMIN_PORT = 8765;
const CONSOLE_ROUTE_PREFIX = "/plugins/claw-memory-system";
const CONSOLE_API_PREFIX = "/plugins/claw-memory-system/api";
const ADMIN_READY_PATH = "/api/summary";
const ADMIN_READY_TIMEOUT_MS = 1_000;
const ADMIN_STARTUP_TIMEOUT_MS = 5_000;
const ADMIN_REQUEST_TIMEOUT_MS = 45_000;
const ADMIN_SHUTDOWN_TIMEOUT_MS = 2_000;
const ADMIN_POLL_INTERVAL_MS = 200;
const BLOCKED_PROXY_REQUEST_HEADERS = new Set(["host", "content-length"]);
const BLOCKED_PROXY_RESPONSE_HEADERS = new Set(["connection", "content-length", "keep-alive", "transfer-encoding"]);

function resolveDefaultOpenClawBin(): string {
  const executable = process.platform === "win32" ? "openclaw.cmd" : "openclaw";
  const candidate = join(dirname(process.execPath), executable);
  return existsSync(candidate) ? candidate : "openclaw";
}

function parseAdminPort(value: unknown): number {
  if (typeof value === "number" && Number.isInteger(value) && value > 0) {
    return value;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number.parseInt(value, 10);
    if (Number.isInteger(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return DEFAULT_ADMIN_PORT;
}

function resolvePluginConfig(api: OpenClawPluginApi): Required<PluginConfig> {
  const config = (api.pluginConfig ?? {}) as PluginConfig;
  return {
    pythonBin: (typeof config.pythonBin === "string" && config.pythonBin.trim()) || "python3",
    repoPath:
      (typeof config.repoPath === "string" && config.repoPath.trim() && api.resolvePath(config.repoPath)) ||
      __dirname,
    workspaceDir:
      (typeof config.workspaceDir === "string" && config.workspaceDir.trim() && api.resolvePath(config.workspaceDir)) ||
      api.resolvePath(DEFAULT_WORKSPACE),
    openclawHome:
      (typeof config.openclawHome === "string" && config.openclawHome.trim() && api.resolvePath(config.openclawHome)) ||
      api.resolvePath(DEFAULT_OPENCLAW_HOME),
    openclawBin: (typeof config.openclawBin === "string" && config.openclawBin.trim()) || resolveDefaultOpenClawBin(),
    adminHost: (typeof config.adminHost === "string" && config.adminHost.trim()) || DEFAULT_ADMIN_HOST,
    adminPort: parseAdminPort(config.adminPort),
    autoStartAdmin: config.autoStartAdmin !== false,
    autoTurnCapture: config.autoTurnCapture === true,
    autoTurnQueueOnly: config.autoTurnQueueOnly !== false,
    turnCaptureMinConfidence: typeof config.turnCaptureMinConfidence === "number" ? config.turnCaptureMinConfidence : 0.88,
    batchGovernanceEnabled: config.batchGovernanceEnabled !== false,
    batchGovernanceEvery: (typeof config.batchGovernanceEvery === "string" && config.batchGovernanceEvery.trim()) || "6h",
  };
}

function appendPyPath(repoPath: string): string {
  const current = process.env.PYTHONPATH?.trim();
  const repoSrc = join(repoPath, "src");
  return current ? `${repoSrc}${process.platform === "win32" ? ";" : ":"}${current}` : repoSrc;
}

function prependExecBinToPath(): string {
  const execDir = dirname(process.execPath);
  const current = process.env.PATH?.trim();
  return current ? `${execDir}${process.platform === "win32" ? ";" : ":"}${current}` : execDir;
}

function sanitizeLogChunk(chunk: string): string[] {
  return chunk
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter(Boolean);
}

function attachChildLogging(
  api: OpenClawPluginApi,
  label: string,
  child: ChildProcessWithoutNullStreams,
): void {
  child.stdout.on("data", (chunk) => {
    for (const line of sanitizeLogChunk(String(chunk))) {
      api.logger.info(`${label}: ${line}`);
    }
  });
  child.stderr.on("data", (chunk) => {
    for (const line of sanitizeLogChunk(String(chunk))) {
      api.logger.warn(`${label}: ${line}`);
    }
  });
}

function runBridgeCommand(
  repoPath: string,
  pythonBin: string,
  args: string[],
): Promise<ChildResult> {
  return new Promise((resolve) => {
    const child = spawn(pythonBin, args, {
      cwd: repoPath,
      env: {
        ...process.env,
        PYTHONPATH: appendPyPath(repoPath),
      },
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("close", (code) => {
      resolve({
        stdout,
        stderr,
        returncode: code ?? 1,
      });
    });
    child.on("error", (error) => {
      resolve({
        stdout,
        stderr: `${stderr}${stderr ? "\n" : ""}${String(error)}`,
        returncode: 1,
      });
    });
  });
}

function parseBridgePayload(stdout: string, stderr: string, returncode: number): BridgePayload {
  const trimmed = stdout.trim();
  if (!trimmed) {
    return {
      ok: returncode === 0,
      returncode,
      stdout,
      stderr,
      parsed_stdout: null,
    };
  }

  try {
    return JSON.parse(trimmed) as BridgePayload;
  } catch {
    return {
      ok: returncode === 0,
      returncode,
      stdout,
      stderr,
      parsed_stdout: null,
    };
  }
}

function renderBridgeText(toolName: string, payload: BridgePayload): string {
  if (payload.parsed_stdout !== undefined && payload.parsed_stdout !== null) {
    return `${toolName} completed.\n${JSON.stringify(payload.parsed_stdout, null, 2)}`;
  }
  if (typeof payload.stdout === "string" && payload.stdout.trim()) {
    return `${toolName} completed.\n${payload.stdout.trim()}`;
  }
  if (typeof payload.stderr === "string" && payload.stderr.trim()) {
    return `${toolName} failed.\n${payload.stderr.trim()}`;
  }
  return `${toolName} finished with return code ${payload.returncode ?? "unknown"}.`;
}

function registerBridgeTool(
  api: OpenClawPluginApi,
  definition: {
    name: string;
    label: string;
    description: string;
    parameters: Record<string, unknown>;
    buildArgs: (params: Record<string, unknown>, config: Required<PluginConfig>) => string[];
  },
): void {
  api.registerTool({
    name: definition.name,
    label: definition.label,
    description: definition.description,
    parameters: definition.parameters,
    async execute(_toolCallId, rawParams) {
      const params = (rawParams ?? {}) as Record<string, unknown>;
      const config = resolvePluginConfig(api);
      const args = definition.buildArgs(params, config);
      const result = await runBridgeCommand(config.repoPath, config.pythonBin, args);
      const payload = parseBridgePayload(result.stdout, result.stderr, result.returncode);
      return {
        content: [
          {
            type: "text",
            text: renderBridgeText(definition.name, payload),
          },
        ],
        details: payload,
      };
    },
  });
}

function buildBootstrapArgs(config: Required<PluginConfig>): string[] {
  return [
    "-m",
    "claw_memory_system.openclaw_plugin_bridge",
    "claw_memory_bootstrap",
    "--repo",
    config.repoPath,
    "--python-bin",
    config.pythonBin,
    "--workspace",
    config.workspaceDir,
  ];
}

async function ensureWorkspaceBootstrap(config: Required<PluginConfig>): Promise<void> {
  const result = await runBridgeCommand(config.repoPath, config.pythonBin, buildBootstrapArgs(config));
  if (result.returncode === 0) {
    return;
  }
  const detail = result.stderr.trim() || result.stdout.trim() || `exit code ${String(result.returncode)}`;
  throw new Error(`workspace bootstrap failed: ${detail}`);
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function parseRequestUrl(rawUrl?: string): URL | null {
  if (!rawUrl) {
    return null;
  }
  try {
    return new URL(rawUrl, "http://127.0.0.1");
  } catch {
    return null;
  }
}

function makeAdminBaseUrl(config: Required<PluginConfig>): string {
  return `http://${config.adminHost}:${String(config.adminPort)}`;
}

async function isAdminAvailable(baseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl}${ADMIN_READY_PATH}`, {
      signal: AbortSignal.timeout(ADMIN_READY_TIMEOUT_MS),
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForAdminAvailability(baseUrl: string, timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isAdminAvailable(baseUrl)) {
      return;
    }
    await delay(ADMIN_POLL_INTERVAL_MS);
  }
  throw new Error(`admin HTTP did not become ready at ${baseUrl}${ADMIN_READY_PATH}`);
}

async function terminateChildProcess(child: ChildProcessWithoutNullStreams): Promise<void> {
  if (child.exitCode !== null) {
    return;
  }

  await new Promise<void>((resolve) => {
    let settled = false;
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      child.removeListener("exit", onExit);
      resolve();
    };
    const onExit = () => {
      finish();
    };
    const timeout = setTimeout(() => {
      if (child.exitCode === null) {
        child.kill("SIGKILL");
      }
      finish();
    }, ADMIN_SHUTDOWN_TIMEOUT_MS);

    child.once("exit", onExit);
    child.kill("SIGTERM");
  });
}

function renderConsoleHtml(repoPath: string): string {
  const html = readFileSync(join(repoPath, "webapp", "index.html"), "utf8");
  const injectedBase = `<script>window.API_BASE = ${JSON.stringify(CONSOLE_ROUTE_PREFIX)};</script>\n  <script>`;
  return html.replace("<script>", injectedBase);
}

function setSharedHeaders(res: ServerResponse, contentType: string): void {
  res.setHeader("cache-control", "no-store, max-age=0");
  res.setHeader("content-type", contentType);
  res.setHeader("x-content-type-options", "nosniff");
  res.setHeader("referrer-policy", "no-referrer");
}

function respondText(res: ServerResponse, statusCode: number, body: string): void {
  res.statusCode = statusCode;
  setSharedHeaders(res, "text/plain; charset=utf-8");
  res.end(body);
}

async function readRequestBody(req: IncomingMessage): Promise<Buffer | undefined> {
  if (req.method === "GET" || req.method === "HEAD") {
    return undefined;
  }

  return await new Promise<Buffer>((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk) => {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(String(chunk)));
    });
    req.on("end", () => {
      resolve(chunks.length > 0 ? Buffer.concat(chunks) : Buffer.alloc(0));
    });
    req.on("error", reject);
  });
}

function buildForwardHeaders(req: IncomingMessage): Headers {
  const headers = new Headers();
  for (const [name, value] of Object.entries(req.headers ?? {})) {
    const normalized = name.toLowerCase();
    if (BLOCKED_PROXY_REQUEST_HEADERS.has(normalized) || value == null) {
      continue;
    }
    if (Array.isArray(value)) {
      headers.set(name, value.join(", "));
    } else {
      headers.set(name, value);
    }
  }
  return headers;
}

async function proxyAdminRequest(
  req: IncomingMessage,
  res: ServerResponse,
  baseUrl: string,
  targetPathWithQuery: string,
  api: OpenClawPluginApi,
): Promise<boolean> {
  try {
    const method = req.method ?? "GET";
    const body = await readRequestBody(req);
    const upstream = await fetch(`${baseUrl}${targetPathWithQuery}`, {
      method,
      headers: buildForwardHeaders(req),
      body,
      signal: AbortSignal.timeout(ADMIN_REQUEST_TIMEOUT_MS),
    });

    res.statusCode = upstream.status;
    for (const [name, value] of upstream.headers) {
      if (BLOCKED_PROXY_RESPONSE_HEADERS.has(name.toLowerCase())) {
        continue;
      }
      res.setHeader(name, value);
    }
    if (!res.hasHeader("x-content-type-options")) {
      res.setHeader("x-content-type-options", "nosniff");
    }

    if (method === "HEAD") {
      res.end();
      return true;
    }

    const payload = Buffer.from(await upstream.arrayBuffer());
    res.setHeader("content-length", String(payload.length));
    res.end(payload);
    return true;
  } catch (error) {
    api.logger.warn(`claw-memory-system: admin proxy failed: ${String(error)}`);
    respondText(res, 502, "Admin backend unavailable");
    return true;
  }
}

function createAdminRuntimeManager(
  api: OpenClawPluginApi,
  config: Required<PluginConfig>,
): AdminRuntimeManager {
  const state: {
    child: ChildProcessWithoutNullStreams | null;
    startup: Promise<void> | null;
  } = {
    child: null,
    startup: null,
  };
  const stoppingChildren = new WeakSet<ChildProcessWithoutNullStreams>();
  const baseUrl = makeAdminBaseUrl(config);

  const spawnAdminProcess = (): ChildProcessWithoutNullStreams => {
    const child = spawn(
      config.pythonBin,
      [
        join(config.repoPath, "scripts", "run_admin_http.py"),
        "--workspace",
        config.workspaceDir,
        "--host",
        config.adminHost,
        "--port",
        String(config.adminPort),
      ],
      {
        cwd: config.repoPath,
        env: {
          ...process.env,
          OPENCLAW_BIN: config.openclawBin,
          PATH: prependExecBinToPath(),
          PYTHONPATH: appendPyPath(config.repoPath),
        },
        stdio: ["ignore", "pipe", "pipe"],
      },
    );

    attachChildLogging(api, "claw-memory-system admin", child);
    child.once("exit", (code, signal) => {
      if (state.child === child) {
        state.child = null;
      }
      const reason = signal ? `signal ${signal}` : `code ${String(code ?? 1)}`;
      if (stoppingChildren.has(child)) {
        api.logger.info(`claw-memory-system: admin HTTP stopped (${reason})`);
      } else {
        api.logger.warn(`claw-memory-system: admin HTTP exited unexpectedly (${reason})`);
      }
    });
    child.once("error", (error) => {
      api.logger.error(`claw-memory-system: admin HTTP process error: ${String(error)}`);
    });

    return child;
  };

  const start = async (): Promise<void> => {
    if (state.startup) {
      return await state.startup;
    }

    state.startup = (async () => {
      await ensureWorkspaceBootstrap(config);

      if (await isAdminAvailable(baseUrl)) {
        api.logger.info(`claw-memory-system: admin HTTP already available at ${baseUrl}`);
        return;
      }

      if (!config.autoStartAdmin) {
        throw new Error(`admin auto-start disabled and no admin HTTP is listening at ${baseUrl}`);
      }

      const child = spawnAdminProcess();
      state.child = child;

      try {
        await waitForAdminAvailability(baseUrl, ADMIN_STARTUP_TIMEOUT_MS);
        api.logger.info(`claw-memory-system: admin console available at ${CONSOLE_ROUTE_PREFIX}`);
      } catch (error) {
        stoppingChildren.add(child);
        if (state.child === child) {
          state.child = null;
        }
        await terminateChildProcess(child);
        throw error;
      }
    })().finally(() => {
      state.startup = null;
    });

    return await state.startup;
  };

  return {
    baseUrl,
    async ensureReady() {
      if (await isAdminAvailable(baseUrl)) {
        return;
      }
      await start();
      if (!(await isAdminAvailable(baseUrl))) {
        throw new Error(`admin HTTP unavailable at ${baseUrl}`);
      }
    },
    start,
    async stop() {
      const child = state.child;
      if (!child) {
        return;
      }
      stoppingChildren.add(child);
      if (state.child === child) {
        state.child = null;
      }
      await terminateChildProcess(child);
    },
  };
}

function createConsoleHttpHandler(
  api: OpenClawPluginApi,
  config: Required<PluginConfig>,
  adminRuntime: AdminRuntimeManager,
) {
  return async (req: IncomingMessage, res: ServerResponse): Promise<boolean> => {
    const parsed = parseRequestUrl(req.url);
    if (!parsed || !parsed.pathname.startsWith(CONSOLE_ROUTE_PREFIX)) {
      return false;
    }

    const method = req.method ?? "GET";
    if (parsed.pathname === CONSOLE_API_PREFIX || parsed.pathname.startsWith(`${CONSOLE_API_PREFIX}/`)) {
      try {
        await adminRuntime.ensureReady();
      } catch (error) {
        api.logger.warn(`claw-memory-system: admin route unavailable: ${String(error)}`);
        respondText(res, 503, "Admin backend unavailable");
        return true;
      }
      const targetPath = `${parsed.pathname.slice(CONSOLE_ROUTE_PREFIX.length)}${parsed.search}`;
      return await proxyAdminRequest(req, res, adminRuntime.baseUrl, targetPath, api);
    }

    if (
      parsed.pathname !== CONSOLE_ROUTE_PREFIX &&
      parsed.pathname !== `${CONSOLE_ROUTE_PREFIX}/` &&
      parsed.pathname !== `${CONSOLE_ROUTE_PREFIX}/index.html`
    ) {
      respondText(res, 404, "Not Found");
      return true;
    }

    if (method !== "GET" && method !== "HEAD") {
      respondText(res, 405, "Method not allowed");
      return true;
    }

    try {
      const body = Buffer.from(renderConsoleHtml(config.repoPath), "utf8");
      res.statusCode = 200;
      setSharedHeaders(res, "text/html; charset=utf-8");
      res.setHeader("content-length", String(body.length));
      if (method === "HEAD") {
        res.end();
      } else {
        res.end(body);
      }
      return true;
    } catch (error) {
      api.logger.warn(`claw-memory-system: failed to load console HTML: ${String(error)}`);
      respondText(res, 500, "Failed to load console");
      return true;
    }
  };
}

function extractTurnTextsFromMessages(messages: unknown[]): { userText: string; assistantText: string; toolSummary: string } {
  const readText = (message: unknown): string => {
    if (!message || typeof message !== "object") {
      return "";
    }
    const record = message as Record<string, unknown>;
    if (typeof record.content === "string") {
      return record.content.trim();
    }
    if (Array.isArray(record.content)) {
      return record.content
        .map((item) => (item && typeof item === "object" && typeof (item as Record<string, unknown>).text === "string" ? String((item as Record<string, unknown>).text).trim() : ""))
        .filter(Boolean)
        .join("\n");
    }
    if (typeof record.text === "string") {
      return record.text.trim();
    }
    return "";
  };

  const userParts: string[] = [];
  const assistantParts: string[] = [];
  const toolParts: string[] = [];
  for (const message of messages) {
    const record = message && typeof message === "object" ? (message as Record<string, unknown>) : null;
    const role = typeof record?.role === "string" ? record.role.toLowerCase() : typeof record?.type === "string" ? record.type.toLowerCase() : "";
    const text = readText(message);
    if (!text) continue;
    if (role === "user") userParts.push(text);
    else if (role === "assistant") assistantParts.push(text);
    else if (role === "tool") toolParts.push(text);
  }
  return {
    userText: userParts.join("\n").trim(),
    assistantText: assistantParts.join("\n").trim(),
    toolSummary: toolParts.join("\n").trim(),
  };
}

function registerBridgeTools(api: OpenClawPluginApi): void {
  registerBridgeTool(api, {
    name: "claw_memory_bootstrap",
    label: "Claw Memory Bootstrap",
    description: "Bootstrap claw-memory-system runtime files into an OpenClaw workspace.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_bootstrap",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_build_index",
    label: "Build Exact Index",
    description: "Build the exact-search index for the current OpenClaw workspace.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_build_index",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_search_index",
    label: "Search Exact Index",
    description: "Search the exact-search index for deterministic matches in MEMORY.md or fact-derived content.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["query"],
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
        query: {
          type: "string",
          description: "FTS query string to search in the exact index.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_search_index",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
      "--query",
      String(params.query ?? ""),
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_facts_list",
    label: "List Facts",
    description: "List structured facts stored in the current claw-memory-system runtime.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_facts_list",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_facts_get",
    label: "Get Fact",
    description: "Get one structured fact by key from the current claw-memory-system runtime.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["key"],
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
        key: {
          type: "string",
          description: "Fact key to read.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_facts_get",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
      "--key",
      String(params.key ?? ""),
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_integration_check",
    label: "Integration Check",
    description: "Run the repo-owned OpenClaw integration check. Browser smoke is skipped by default.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
        skipSmoke: {
          type: "boolean",
          description: "Whether to skip the browser smoke test. Defaults to true.",
        },
      },
    },
    buildArgs: (params, config) => {
      const args = [
        "-m",
        "claw_memory_system.openclaw_plugin_bridge",
        "claw_memory_integration_check",
        "--repo",
        config.repoPath,
        "--python-bin",
        config.pythonBin,
        "--workspace",
        (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
      ];
      if (params.skipSmoke !== false) {
        args.push("--skip-smoke");
      }
      return args;
    },
  });

  registerBridgeTool(api, {
    name: "claw_memory_deep_integration_check",
    label: "Deep Integration Check",
    description: "Run the deep local OpenClaw integration and migration checks against a real installation.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace override.",
        },
        openclawHome: {
          type: "string",
          description: "Optional OpenClaw home override. Defaults to the plugin openclawHome config.",
        },
        openclawBin: {
          type: "string",
          description: "Optional OpenClaw executable override.",
        },
        strict: {
          type: "boolean",
          description: "Exit non-zero when the runtime is not ready.",
        },
      },
    },
    buildArgs: (params, config) => {
      const args = [
        "-m",
        "claw_memory_system.openclaw_plugin_bridge",
        "claw_memory_deep_integration_check",
        "--repo",
        config.repoPath,
        "--python-bin",
        config.pythonBin,
        "--openclaw-home",
        (typeof params.openclawHome === "string" && params.openclawHome.trim()) || config.openclawHome,
        "--openclaw-bin",
        (typeof params.openclawBin === "string" && params.openclawBin.trim()) || config.openclawBin,
      ];
      const workspace = typeof params.workspace === "string" && params.workspace.trim();
      if (workspace) {
        args.push("--workspace", workspace);
      }
      if (params.strict === true) {
        args.push("--strict");
      }
      return args;
    },
  });

  registerBridgeTool(api, {
    name: "claw_memory_batch_governance",
    label: "Batch Governance",
    description: "Run the claw-memory-system batch governance workflow and write a report.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_batch_governance",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_classify_turn",
    label: "Classify Turn",
    description: "Classify a turn for autonomous memory handling decisions.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["query"],
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
        query: {
          type: "string",
          description: "User turn text to classify.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_classify_turn",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
      "--query",
      String(params.query ?? ""),
    ],
  });

  registerBridgeTool(api, {
    name: "claw_memory_queue_turn_candidates",
    label: "Queue Turn Candidates",
    description: "Classify a turn and queue portable pending memory candidates.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["query"],
      properties: {
        workspace: {
          type: "string",
          description: "Optional OpenClaw workspace path. Defaults to the plugin workspaceDir config.",
        },
        query: {
          type: "string",
          description: "User turn text to classify and queue.",
        },
      },
    },
    buildArgs: (params, config) => [
      "-m",
      "claw_memory_system.openclaw_plugin_bridge",
      "claw_memory_queue_turn_candidates",
      "--repo",
      config.repoPath,
      "--python-bin",
      config.pythonBin,
      "--workspace",
      (typeof params.workspace === "string" && params.workspace.trim()) || config.workspaceDir,
      "--query",
      String(params.query ?? ""),
    ],
  });
}

const clawMemoryPlugin = {
  id: "claw-memory-system",
  name: "Claw Memory System",
  description: "OpenClaw tool bridge for facts, exact search, bootstrap, and integration checks.",
  kind: "tool" as const,

  register(api: OpenClawPluginApi) {
    const config = resolvePluginConfig(api);
    const adminRuntime = createAdminRuntimeManager(api, config);

    api.registerService({
      id: "claw-memory-system-admin",
      start: async () => {
        if (!config.autoStartAdmin) {
          api.logger.info("claw-memory-system: admin auto-start disabled");
          return;
        }
        await adminRuntime.start();
      },
      stop: async () => {
        await adminRuntime.stop();
      },
    });

    api.registerHttpRoute({
      path: "/plugins/claw-memory-system",
      auth: "plugin",
      match: "prefix",
      handler: createConsoleHttpHandler(api, config, adminRuntime),
    });

    registerBridgeTools(api);

    api.on("agent_end", async (event, ctx) => {
      const latestConfig = resolvePluginConfig(api);
      if (!latestConfig.autoTurnCapture || !latestConfig.autoTurnQueueOnly) {
        return;
      }
      const workspace = (ctx.workspaceDir && api.resolvePath(ctx.workspaceDir)) || latestConfig.workspaceDir;
      if (!workspace) {
        return;
      }
      const texts = extractTurnTextsFromMessages(Array.isArray(event.messages) ? event.messages : []);
      if (!texts.userText && !texts.assistantText && !texts.toolSummary) {
        return;
      }
      try {
        const args = [
          "-m",
          "claw_memory_system.openclaw_plugin_bridge",
          "claw_memory_queue_turn_candidates",
          "--repo",
          latestConfig.repoPath,
          "--python-bin",
          latestConfig.pythonBin,
          "--workspace",
          workspace,
          "--user-text",
          texts.userText,
          "--assistant-text",
          texts.assistantText,
          "--tool-summary",
          texts.toolSummary,
        ];
        await runBridgeCommand(latestConfig.repoPath, latestConfig.pythonBin, args);
      } catch (error) {
        api.logger.warn(`claw-memory-system: auto turn capture failed: ${String(error)}`);
      }
    });

    api.logger.info(`claw-memory-system: plugin bridge registered (console: ${CONSOLE_ROUTE_PREFIX})`);
  },
};

export default clawMemoryPlugin;
