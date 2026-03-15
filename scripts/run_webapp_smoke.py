from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Iterator
import argparse
import json
import os
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BROWSER = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local OpenClaw Memory webapp smoke test.")
    parser.add_argument("--workspace", required=True, help="Bootstrapped OpenClaw workspace path")
    parser.add_argument("--host", default="127.0.0.1", help="Host for local admin HTTP and static frontend servers")
    parser.add_argument("--api-port", type=int, default=8765, help="Port for the admin HTTP server")
    parser.add_argument("--frontend-port", type=int, default=18080, help="Port for the static frontend server")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "output" / "playwright"),
        help="Directory for smoke screenshots and artifacts",
    )
    parser.add_argument(
        "--browser-executable",
        default="",
        help="Optional browser executable path. Defaults to local Google Chrome if present, else Playwright bundled Chromium.",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for server startup and browser expectations")
    parser.add_argument("--headed", action="store_true", help="Launch the browser with a visible window")
    return parser.parse_args()


def wait_for_port(host: str, port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {host}:{port}")


@contextmanager
def managed_process(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> Iterator[subprocess.Popen[str]]:
    process = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def resolve_browser_executable(raw_value: str) -> str | None:
    if raw_value:
        candidate = Path(raw_value).expanduser()
        if not candidate.exists():
            raise FileNotFoundError(f"Browser executable not found: {candidate}")
        return str(candidate)
    if DEFAULT_BROWSER.exists():
        return str(DEFAULT_BROWSER)
    return None


def build_api_base(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def build_frontend_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def run_browser_smoke(
    *,
    frontend_url: str,
    api_base: str,
    output_dir: Path,
    browser_executable: str | None,
    timeout: float,
    headed: bool,
) -> dict:
    from playwright.sync_api import expect, sync_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(int(time.time()))
    pref_key = f"smoke.preference.{run_id}"
    task_id = f"task-smoke-{run_id}"
    episode_id = f"ep-smoke-{run_id}"
    screenshot_path = output_dir / f"memory-console-smoke-{run_id}.png"

    console_errors: list[str] = []
    page_errors: list[str] = []
    request_failures: list[str] = []
    http_failures: list[str] = []

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": not headed,
        }
        if browser_executable:
            launch_kwargs["executable_path"] = browser_executable
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.set_default_timeout(timeout * 1000)
        page.add_init_script(f"window.API_BASE = {json.dumps(api_base)};")

        page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("requestfailed", lambda req: request_failures.append(f"{req.method} {req.url}: {req.failure or 'unknown'}"))
        page.on(
            "response",
            lambda response: http_failures.append(f"{response.request.method} {response.url} -> {response.status}")
            if response.status >= 400
            else None,
        )

        page.goto(frontend_url, wait_until="load")
        page.wait_for_load_state("networkidle")
        expect(page.locator("#summaryCards .metric").first).to_be_visible()

        page.click("button[data-i18n='nav.explorer']")
        expect(page.locator("#section-explorer")).to_be_visible()

        page.select_option("#layerName", "preferences")
        page.fill("#prefKey", pref_key)
        page.fill("#prefValue", "42.5")
        page.select_option("#prefValueType", "number")
        page.fill("#prefNotes", "Repo smoke test numeric preference.")
        page.fill("#prefStrength", "0.75")
        page.fill("#prefAliases", "smoke,browser")
        page.fill("#prefTags", "beta,smoke")
        with page.expect_response(lambda r: r.url.endswith("/api/preference") and r.request.method == "POST") as pref_response_info:
            page.click("button[data-i18n='actions.createPreference']")
        pref_response = pref_response_info.value
        if not pref_response.ok:
            raise AssertionError(f"Preference create failed with {pref_response.status}")
        expect(page.locator("#prefCreateResult")).to_contain_text('"value": 42.5')
        expect(page.locator("#layerList")).to_contain_text(pref_key)
        page.locator("#layerList .list-item", has_text=pref_key).click()
        expect(page.locator("#layerDetail")).to_contain_text(pref_key)

        page.select_option("#layerName", "tasks")
        page.fill("#taskId", task_id)
        page.fill("#taskTitle", "Repo smoke test task")
        page.fill("#taskSummary", "Validate the Beta console task flow in a reusable repo smoke command.")
        page.fill("#taskNextAction", "Keep Beta stabilization moving.")
        page.select_option("#taskPriority", "high")
        page.select_option("#taskState", "active")
        page.select_option("#taskImportance", "high")
        page.fill("#taskEntities", "smoke,beta,webapp")
        with page.expect_response(lambda r: r.url.endswith("/api/task") and r.request.method == "POST") as task_response_info:
            page.click("button[data-i18n='actions.createTask']")
        task_response = task_response_info.value
        if not task_response.ok:
            raise AssertionError(f"Task create failed with {task_response.status}")
        expect(page.locator("#taskCreateResult")).to_contain_text(task_id)
        expect(page.locator("#layerList")).to_contain_text(task_id)
        page.locator("#layerList .list-item", has_text=task_id).click()
        expect(page.locator("#layerDetail")).to_contain_text(task_id)

        page.select_option("#layerName", "episodes")
        page.fill("#episodeId", episode_id)
        page.fill("#episodeTitle", "Repo smoke test episode")
        page.fill("#episodeSummary", "Validate the Beta console episode flow in a reusable repo smoke command.")
        page.select_option("#episodeStatus", "active")
        page.fill("#episodeTaskIds", task_id)
        page.select_option("#episodeImportance", "high")
        with page.expect_response(lambda r: r.url.endswith("/api/episode") and r.request.method == "POST") as episode_response_info:
            page.click("button[data-i18n='actions.createEpisode']")
        episode_response = episode_response_info.value
        if not episode_response.ok:
            raise AssertionError(f"Episode create failed with {episode_response.status}")
        expect(page.locator("#episodeCreateResult")).to_contain_text(episode_id)
        expect(page.locator("#layerList")).to_contain_text(episode_id)
        page.locator("#layerList .list-item", has_text=episode_id).click()
        expect(page.locator("#layerDetail")).to_contain_text(episode_id)

        page.screenshot(path=str(screenshot_path), full_page=True)
        browser.close()

    if console_errors:
        raise AssertionError(f"Unexpected console errors: {console_errors}")
    if page_errors:
        raise AssertionError(f"Unexpected page errors: {page_errors}")
    if request_failures:
        raise AssertionError(f"Unexpected request failures: {request_failures}")
    if http_failures:
        raise AssertionError(f"Unexpected HTTP failures: {http_failures}")

    return {
        "ok": True,
        "url": frontend_url,
        "created": {
            "preference": pref_key,
            "task": task_id,
            "episode": episode_id,
        },
        "artifacts": {
            "screenshot": str(screenshot_path),
        },
        "browser": {
            "executable": browser_executable or "bundled",
        },
        "console_errors": console_errors,
        "page_errors": page_errors,
        "request_failures": request_failures,
        "http_failures": http_failures,
    }


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.exists():
        print(json.dumps({"ok": False, "error": f"Workspace not found: {workspace}"}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve()
    api_base = build_api_base(args.host, args.api_port)
    frontend_url = build_frontend_url(args.host, args.frontend_port)
    browser_executable = resolve_browser_executable(args.browser_executable)

    admin_env = os.environ.copy()
    admin_env["PYTHONPATH"] = str(ROOT / "src") + (f":{admin_env['PYTHONPATH']}" if admin_env.get("PYTHONPATH") else "")

    admin_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_admin_http.py"),
        "--workspace",
        str(workspace),
        "--host",
        args.host,
        "--port",
        str(args.api_port),
    ]
    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(args.frontend_port),
        "--bind",
        args.host,
        "--directory",
        str(ROOT / "webapp"),
    ]

    try:
        with ExitStack() as stack:
            stack.enter_context(managed_process(admin_cmd, cwd=ROOT, env=admin_env))
            wait_for_port(args.host, args.api_port, args.timeout)
            stack.enter_context(managed_process(frontend_cmd, cwd=ROOT))
            wait_for_port(args.host, args.frontend_port, args.timeout)

            result = run_browser_smoke(
                frontend_url=frontend_url,
                api_base=api_base,
                output_dir=output_dir,
                browser_executable=browser_executable,
                timeout=args.timeout,
                headed=args.headed,
            )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
