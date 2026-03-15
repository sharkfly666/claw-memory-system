from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


EXPECTED_TOOL_NAMES = {
    "claw_memory_bootstrap",
    "claw_memory_build_index",
    "claw_memory_search_index",
    "claw_memory_facts_list",
    "claw_memory_facts_get",
    "claw_memory_integration_check",
    "claw_memory_deep_integration_check",
    "claw_memory_batch_governance",
    "claw_memory_classify_turn",
    "claw_memory_queue_turn_candidates",
}


class OpenClawPluginPackageTest(unittest.TestCase):
    def test_plugin_manifest_declares_tool_plugin(self) -> None:
        manifest_path = ROOT / "openclaw.plugin.json"
        self.assertTrue(manifest_path.exists(), "openclaw.plugin.json should exist")

        payload = json.loads(manifest_path.read_text())
        self.assertEqual(payload["id"], "claw-memory-system")
        self.assertEqual(payload["kind"], "tool")
        self.assertEqual(payload["version"], "0.1.0")

    def test_package_json_declares_openclaw_extension(self) -> None:
        package_path = ROOT / "package.json"
        self.assertTrue(package_path.exists(), "package.json should exist")

        payload = json.loads(package_path.read_text())
        self.assertEqual(payload["name"], "claw-memory-system")
        self.assertEqual(payload["version"], "0.1.0")
        self.assertEqual(payload["openclaw"]["extensions"], ["./index.ts"])

    def test_package_json_includes_webapp_console_asset(self) -> None:
        payload = json.loads((ROOT / "package.json").read_text())
        self.assertIn("webapp/index.html", payload["files"])

    def test_package_json_includes_runtime_schemas_for_bootstrap(self) -> None:
        payload = json.loads((ROOT / "package.json").read_text())
        self.assertIn("schemas/*.json", payload["files"])

    def test_package_and_manifest_versions_stay_in_sync(self) -> None:
        package = json.loads((ROOT / "package.json").read_text())
        manifest = json.loads((ROOT / "openclaw.plugin.json").read_text())
        self.assertEqual(package["version"], manifest["version"])

    def test_plugin_manifest_exposes_admin_console_runtime_config(self) -> None:
        manifest = json.loads((ROOT / "openclaw.plugin.json").read_text())
        properties = manifest["configSchema"]["properties"]

        self.assertEqual(properties["adminHost"]["default"], "127.0.0.1")
        self.assertEqual(properties["adminPort"]["default"], 8765)
        self.assertEqual(properties["autoStartAdmin"]["default"], True)

    def test_typescript_entrypoint_mentions_expected_tools(self) -> None:
        entrypoint = ROOT / "index.ts"
        self.assertTrue(entrypoint.exists(), "index.ts should exist")

        source = entrypoint.read_text()
        self.assertIn('kind: "tool"', source)
        self.assertIn("claw_memory_system.openclaw_plugin_bridge", source)
        for tool_name in EXPECTED_TOOL_NAMES:
            self.assertIn(tool_name, source)

    def test_typescript_entrypoint_registers_admin_service_and_console_route(self) -> None:
        source = (ROOT / "index.ts").read_text()

        self.assertIn("api.registerService({", source)
        self.assertIn('id: "claw-memory-system-admin"', source)
        self.assertIn("run_admin_http.py", source)
        self.assertIn("api.registerHttpRoute({", source)
        self.assertIn('path: "/plugins/claw-memory-system"', source)
        self.assertIn('"/plugins/claw-memory-system/api"', source)

    def test_typescript_entrypoint_uses_dedicated_proxy_timeout_for_admin_requests(self) -> None:
        source = (ROOT / "index.ts").read_text()

        self.assertIn("const ADMIN_REQUEST_TIMEOUT_MS =", source)
        self.assertIn("signal: AbortSignal.timeout(ADMIN_REQUEST_TIMEOUT_MS)", source)


class OpenClawPluginBridgeModuleTest(unittest.TestCase):
    def test_python_bridge_exports_expected_tool_names(self) -> None:
        from claw_memory_system.openclaw_plugin_bridge import TOOL_SPECS

        self.assertEqual(set(TOOL_SPECS), EXPECTED_TOOL_NAMES)

    def test_build_index_action_uses_workspace_runtime_paths(self) -> None:
        from claw_memory_system.openclaw_plugin_bridge import build_bridge_command

        command = build_bridge_command(
            "claw_memory_build_index",
            repo=ROOT,
            workspace=Path("/tmp/plugin-workspace"),
        )

        self.assertEqual(command.argv[0], "python3")
        self.assertEqual(command.argv[1:3], ["-m", "claw_memory_system.build_pageindex"])
        self.assertEqual(
            command.argv[3:],
            [
                "--root",
                "/tmp/plugin-workspace",
                "--db",
                "/tmp/plugin-workspace/memory-system/index/pageindex.sqlite",
                "--facts",
                "/tmp/plugin-workspace/memory-system/facts/facts.json",
            ],
        )
        self.assertEqual(command.cwd, ROOT)
        self.assertEqual(command.env["PYTHONPATH"], str(ROOT / "src"))

    def test_search_index_action_requires_query_and_targets_runtime_db(self) -> None:
        from claw_memory_system.openclaw_plugin_bridge import build_bridge_command

        command = build_bridge_command(
            "claw_memory_search_index",
            repo=ROOT,
            workspace=Path("/tmp/plugin-workspace"),
            query="primary model",
        )

        self.assertEqual(
            command.argv,
            [
                "python3",
                "-m",
                "claw_memory_system.search_pageindex",
                "--db",
                "/tmp/plugin-workspace/memory-system/index/pageindex.sqlite",
                "primary model",
            ],
        )

    def test_deep_integration_action_targets_repo_script(self) -> None:
        from claw_memory_system.openclaw_plugin_bridge import build_bridge_command

        command = build_bridge_command(
            "claw_memory_deep_integration_check",
            repo=ROOT,
            openclaw_home=Path("/tmp/.openclaw"),
            openclaw_bin="openclaw",
        )

        self.assertEqual(
            command.argv,
            [
                "python3",
                str(ROOT / "scripts" / "run_openclaw_deep_integration.py"),
                "--repo",
                str(ROOT),
                "--openclaw-home",
                "/tmp/.openclaw",
                "--openclaw-bin",
                "openclaw",
            ],
        )


if __name__ == "__main__":
    unittest.main()
