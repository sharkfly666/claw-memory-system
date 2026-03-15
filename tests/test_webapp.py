from __future__ import annotations

from pathlib import Path
import re
import json
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
WEBAPP = ROOT / "webapp" / "index.html"


class WebappMarkupTest(unittest.TestCase):
    def test_bootstrap_avoids_startup_report_fetch_and_embeds_favicon(self) -> None:
        html = WEBAPP.read_text()

        self.assertRegex(html, r'<link rel="icon" href="data:image/svg\+xml,')
        self.assertNotRegex(html, r"^\s*loadReport\(\);\s*$", re.MULTILINE)

    def test_memory_explorer_contains_preference_task_episode_write_forms(self) -> None:
        html = WEBAPP.read_text()

        required_ids = [
            "prefKey",
            "prefValue",
            "prefValueType",
            "prefNotes",
            "prefStrength",
            "prefAliases",
            "prefTags",
            "prefCreateResult",
            "taskId",
            "taskTitle",
            "taskSummary",
            "taskNextAction",
            "taskPriority",
            "taskState",
            "taskImportance",
            "taskEntities",
            "taskCreateResult",
            "episodeId",
            "episodeTitle",
            "episodeSummary",
            "episodeStatus",
            "episodeTaskIds",
            "episodeImportance",
            "episodeCreateResult",
        ]

        for element_id in required_ids:
            self.assertRegex(html, rf'id="{element_id}"')

        self.assertRegex(html, r'onclick="createPreference\(\)"')
        self.assertRegex(html, r'onclick="createTask\(\)"')
        self.assertRegex(html, r'onclick="createEpisode\(\)"')

    def test_dashboard_contains_semantic_memory_panel_and_recent_preview(self) -> None:
        html = WEBAPP.read_text()

        required_ids = [
            "semanticStatus",
            "semanticSummaryCards",
            "semanticScopeDetail",
            "semanticCategoryDetail",
            "semanticRecentList",
            "semanticRecentDetail",
        ]

        for element_id in required_ids:
            self.assertRegex(html, rf'id="{element_id}"')

        self.assertIn("/api/semantic-overview", html)

    def test_graph_section_contains_rebuild_action_and_status(self) -> None:
        html = WEBAPP.read_text()

        self.assertRegex(html, r'id="graphRefreshStatus"')
        self.assertRegex(html, r'onclick="refreshGraph\(\)"')

    def test_graph_section_contains_visual_canvas_controls_and_stats(self) -> None:
        html = WEBAPP.read_text()

        required_ids = [
            "graphSearchInput",
            "graphTypeFilter",
            "graphCanvas",
            "graphScene",
            "graphLegend",
            "graphRelationSummary",
            "graphStatNodes",
            "graphStatEdges",
            "graphStatVisibleNodes",
            "graphStatVisibleEdges",
            "graphZoomIn",
            "graphZoomOut",
            "graphZoomFit",
            "graphZoomReset",
            "graphViewportScale",
        ]
        for element_id in required_ids:
            self.assertRegex(html, rf'id="{element_id}"')

        self.assertRegex(html, r'oninput="applyGraphFilters\(\)"')
        self.assertRegex(html, r'onchange="applyGraphFilters\(\)"')
        self.assertRegex(html, r'onclick="zoomGraphIn\(\)"')
        self.assertRegex(html, r'onclick="zoomGraphOut\(\)"')
        self.assertRegex(html, r'onclick="fitGraphViewport\(\)"')
        self.assertRegex(html, r'onclick="resetGraphViewport\(\)"')

    def test_load_summary_fetches_structured_and_semantic_overview(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"async function loadSummary\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "loadSummary function not found")

        script = f"""
const calls = [];
let structuredData = null;
let semanticPayload = null;
global.getJson = async (path) => {{
  calls.push(path);
  if (path === '/api/summary') return {{ data: {{ facts: 24 }} }};
  if (path === '/api/semantic-overview') return {{ ok: true, data: {{ provider: 'memory-lancedb-pro', total_count: 309 }} }};
  throw new Error('Unexpected path: ' + path);
}};
global.renderSummaryCards = (data) => {{
  structuredData = data;
}};
global.renderSemanticOverview = (payload) => {{
  semanticPayload = payload;
}};
{match.group(0)}

loadSummary()
  .then(() => {{
    console.log(JSON.stringify({{
      calls,
      structuredData,
      semanticPayload,
    }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["calls"], ["/api/summary", "/api/semantic-overview"])
        self.assertEqual(payload["structuredData"]["facts"], 24)
        self.assertEqual(payload["semanticPayload"]["data"]["total_count"], 309)

    def test_get_json_normalizes_console_api_base_without_double_api_prefix(self) -> None:
        html = WEBAPP.read_text()
        api_base_match = re.search(r"const API_BASE = .*?;\n", html)
        build_url_match = re.search(r"function buildApiUrl\(path\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        get_json_match = re.search(r"async function getJson\(path\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)

        self.assertIsNotNone(api_base_match, "API_BASE constant not found")
        self.assertIsNotNone(build_url_match, "buildApiUrl function not found")
        self.assertIsNotNone(get_json_match, "getJson function not found")

        script = f"""
global.window = {{
  API_BASE: '/plugins/claw-memory-system/api'
}};
let requestedUrl = null;
global.fetch = async (url) => {{
  requestedUrl = url;
  return {{
    async json() {{
      return {{ ok: true }};
    }},
  }};
}};
{api_base_match.group(0)}
{build_url_match.group(0)}
{get_json_match.group(0)}

getJson('/api/summary')
  .then(() => {{
    console.log(JSON.stringify({{ requestedUrl }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["requestedUrl"], "/plugins/claw-memory-system/api/summary")

    def test_create_preference_serializes_number_values_before_posting(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"async function createPreference\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "createPreference function not found")

        script = f"""
const elements = {{
  prefAliases: {{ value: 'alpha,beta' }},
  prefTags: {{ value: 'memory,beta' }},
  prefValue: {{ value: '42.5' }},
  prefValueType: {{ value: 'number' }},
  prefKey: {{ value: 'user.score.threshold' }},
  prefNotes: {{ value: 'numeric threshold' }},
  prefStrength: {{ value: '0.75' }},
  prefCreateResult: {{ textContent: '' }},
  layerName: {{ value: 'facts' }},
}};
let captured = null;
global.document = {{
  getElementById(id) {{
    if (!elements[id]) {{
      throw new Error('Missing mock element: ' + id);
    }}
    return elements[id];
  }},
}};
global.postJson = async (path, body) => {{
  captured = {{ path, body }};
  return {{ ok: true, data: body }};
}};
global.loadSummary = async () => {{}};
global.loadLayerList = async () => {{}};
{match.group(0)}

createPreference()
  .then(() => {{
    console.log(JSON.stringify({{
      captured,
      resultText: elements.prefCreateResult.textContent,
    }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())

        self.assertEqual(payload["captured"]["path"], "/api/preference")
        self.assertEqual(payload["captured"]["body"]["key"], "user.score.threshold")
        self.assertEqual(payload["captured"]["body"]["value_type"], "number")
        self.assertEqual(payload["captured"]["body"]["value"], 42.5)
        self.assertEqual(payload["captured"]["body"]["strength"], 0.75)
        self.assertEqual(payload["captured"]["body"]["aliases"], ["alpha", "beta"])
        self.assertEqual(payload["captured"]["body"]["tags"], ["memory", "beta"])
        self.assertIn('"value": 42.5', payload["resultText"])

    def test_refresh_graph_posts_refresh_then_reloads_graph(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"async function refreshGraph\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "refreshGraph function not found")

        script = f"""
const elements = {{
  graphRefreshStatus: {{ textContent: '' }},
}};
const calls = [];
let loadGraphCalls = 0;
global.document = {{
  getElementById(id) {{
    if (!elements[id]) {{
      throw new Error('Missing mock element: ' + id);
    }}
    return elements[id];
  }},
}};
global.postJson = async (path, body) => {{
  calls.push({{ path, body }});
  return {{
    ok: true,
    data: {{
      graph_nodes: 7,
      graph_edges: 9,
    }},
  }};
}};
global.loadGraph = async () => {{
  loadGraphCalls += 1;
}};
{match.group(0)}

refreshGraph()
  .then(() => {{
    console.log(JSON.stringify({{
      calls,
      loadGraphCalls,
      statusText: elements.graphRefreshStatus.textContent,
    }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["calls"], [{"path": "/api/graph/refresh", "body": {}}])
        self.assertEqual(payload["loadGraphCalls"], 1)
        self.assertIn("7", payload["statusText"])
        self.assertIn("9", payload["statusText"])

    def test_build_graph_view_model_computes_metrics_and_neighbor_visibility(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"function buildGraphViewModel\(nodesMap, edgesList, options = \{\}\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "buildGraphViewModel function not found")

        script = f"""
{match.group(0)}

const viewModel = buildGraphViewModel(
  {{
    'fact:agent.name': {{ node_type: 'fact', label: 'agent.name', layer: 'facts' }},
    'fact:agent.primary_model': {{ node_type: 'fact', label: 'agent.primary_model', layer: 'facts' }},
    'tag:identity': {{ node_type: 'tag', label: 'identity', layer: 'graph' }},
    'alias:primary-model': {{ node_type: 'alias', label: 'primary-model', layer: 'graph' }},
    'entity:gpt-5': {{ node_type: 'entity', label: 'gpt-5', layer: 'graph' }},
  }},
  [
    {{ source: 'fact:agent.name', relation: 'tagged_with', target: 'tag:identity' }},
    {{ source: 'fact:agent.primary_model', relation: 'related_to', target: 'entity:gpt-5' }},
    {{ source: 'fact:agent.primary_model', relation: 'has_alias', target: 'alias:primary-model' }},
  ],
  {{ search: '', nodeType: 'all' }}
);

console.log(JSON.stringify({{
  stats: viewModel.stats,
  nodeTypes: viewModel.nodeTypes,
  selectedNodeId: viewModel.selectedNodeId,
  visibleNodeIds: viewModel.nodes.filter((node) => node.visible).map((node) => node.id).sort(),
  visibleEdgeIds: viewModel.edges.filter((edge) => edge.visible).map((edge) => `${{edge.source}}|${{edge.target}}`).sort(),
  relationCounts: viewModel.relationCounts,
  laneSample: viewModel.nodes.filter((node) => node.visible).map((node) => ({{
    id: node.id,
    nodeType: node.nodeType,
    x: node.x,
    y: node.y,
  }})),
}}));
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["stats"]["totalNodes"], 5)
        self.assertEqual(payload["stats"]["totalEdges"], 3)
        self.assertEqual(payload["stats"]["visibleNodes"], 5)
        self.assertEqual(payload["stats"]["visibleEdges"], 3)
        self.assertEqual(payload["selectedNodeId"], "fact:agent.primary_model")
        self.assertEqual(payload["relationCounts"]["tagged_with"], 1)
        self.assertEqual(payload["relationCounts"]["has_alias"], 1)
        self.assertIn("fact", payload["nodeTypes"])
        self.assertIn("tag", payload["nodeTypes"])
        self.assertTrue(all(isinstance(item["x"], (int, float)) and isinstance(item["y"], (int, float)) for item in payload["laneSample"]))
        lane_map = {item["id"]: item for item in payload["laneSample"]}
        self.assertLess(lane_map["fact:agent.name"]["x"], lane_map["entity:gpt-5"]["x"])
        self.assertLess(lane_map["entity:gpt-5"]["x"], lane_map["tag:identity"]["x"])
        self.assertLess(lane_map["tag:identity"]["x"], lane_map["alias:primary-model"]["x"])
        self.assertEqual(lane_map["fact:agent.name"]["x"], lane_map["fact:agent.primary_model"]["x"])

    def test_graph_viewport_helpers_zoom_fit_and_reset(self) -> None:
        html = WEBAPP.read_text()
        default_match = re.search(r"function createDefaultGraphViewport\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        fit_match = re.search(r"function fitGraphViewport\(viewModel = graphState.viewModel\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        zoom_in_match = re.search(r"function zoomGraphIn\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        zoom_out_match = re.search(r"function zoomGraphOut\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        reset_match = re.search(r"function resetGraphViewport\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)

        self.assertIsNotNone(default_match, "createDefaultGraphViewport function not found")
        self.assertIsNotNone(fit_match, "fitGraphViewport function not found")
        self.assertIsNotNone(zoom_in_match, "zoomGraphIn function not found")
        self.assertIsNotNone(zoom_out_match, "zoomGraphOut function not found")
        self.assertIsNotNone(reset_match, "resetGraphViewport function not found")

        script = f"""
global.graphState = {{
  viewport: null,
  viewModel: {{
    width: 1000,
    height: 640,
    nodes: [
      {{ id: 'fact:one', visible: true, x: 200, y: 100, radius: 16 }},
      {{ id: 'alias:one', visible: true, x: 920, y: 520, radius: 12 }},
    ],
  }},
}};
let hudCalls = 0;
let renderCalls = 0;
global.updateGraphViewportHud = () => {{ hudCalls += 1; }};
global.renderGraphVisualization = () => {{ renderCalls += 1; }};
{default_match.group(0)}
{fit_match.group(0)}
{zoom_in_match.group(0)}
{zoom_out_match.group(0)}
{reset_match.group(0)}

graphState.viewport = createDefaultGraphViewport();
fitGraphViewport();
const afterFit = {{ ...graphState.viewport }};
zoomGraphIn();
const afterZoomIn = {{ ...graphState.viewport }};
zoomGraphOut();
const afterZoomOut = {{ ...graphState.viewport }};
resetGraphViewport();
const afterReset = {{ ...graphState.viewport }};

console.log(JSON.stringify({{
  afterFit,
  afterZoomIn,
  afterZoomOut,
  afterReset,
  hudCalls,
  renderCalls,
}}));
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertGreater(payload["afterFit"]["scale"], 0.1)
        self.assertLessEqual(payload["afterFit"]["scale"], 1.0)
        self.assertGreater(payload["afterZoomIn"]["scale"], payload["afterFit"]["scale"])
        self.assertLess(payload["afterZoomOut"]["scale"], payload["afterZoomIn"]["scale"])
        self.assertEqual(payload["afterReset"], {"scale": 1, "translateX": 0, "translateY": 0})
        self.assertGreaterEqual(payload["hudCalls"], 4)
        self.assertGreaterEqual(payload["renderCalls"], 4)

    def test_load_graph_builds_view_model_and_renders_visual_graph(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"async function loadGraph\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "loadGraph function not found")

        script = f"""
const calls = [];
const elements = {{
  graphSearchInput: {{ value: 'identity' }},
  graphTypeFilter: {{ value: 'tag' }},
}};
global.graphState = {{}};
global.document = {{
  getElementById(id) {{
    if (!elements[id]) throw new Error('Missing mock element: ' + id);
    return elements[id];
  }},
}};
global.getJson = async (path) => {{
  calls.push(path);
  if (path === '/api/layer?layer=graph.nodes') return {{ data: {{ 'tag:identity': {{ node_type: 'tag', label: 'identity' }} }} }};
  if (path === '/api/layer?layer=graph.edges') return {{ data: [] }};
  throw new Error('Unexpected path: ' + path);
}};
let buildArgs = null;
let renderOverviewCount = 0;
let renderVisualizationCount = 0;
let renderCollectionsCount = 0;
let renderFilterArgs = null;
global.buildGraphViewModel = (nodesMap, edgesList, options) => {{
  buildArgs = {{ nodesMap, edgesList, options }};
  return {{ nodes: [], edges: [], nodeTypes: ['tag'], stats: {{ totalNodes: 1, totalEdges: 0, visibleNodes: 1, visibleEdges: 0 }}, relationCounts: {{}} }};
}};
global.renderGraphOverview = () => {{ renderOverviewCount += 1; }};
global.renderGraphVisualization = () => {{ renderVisualizationCount += 1; }};
global.renderGraphCollections = () => {{ renderCollectionsCount += 1; }};
global.renderGraphTypeFilter = (nodeTypes, currentValue) => {{ renderFilterArgs = {{ nodeTypes, currentValue }}; }};
{match.group(0)}

loadGraph()
  .then(() => {{
    console.log(JSON.stringify({{
      calls,
      buildArgs,
      renderOverviewCount,
      renderVisualizationCount,
      renderCollectionsCount,
      renderFilterArgs,
      rawNodeKeys: Object.keys(graphState.rawNodes || {{}}),
      rawEdgeCount: (graphState.rawEdges || []).length,
    }}));
  }})
  .catch((error) => {{
    console.error(error);
    process.exit(1);
  }});
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["calls"], ["/api/layer?layer=graph.nodes", "/api/layer?layer=graph.edges"])
        self.assertEqual(payload["buildArgs"]["options"], {"search": "identity", "nodeType": "tag", "selectedNodeId": None})
        self.assertEqual(payload["renderOverviewCount"], 1)
        self.assertEqual(payload["renderVisualizationCount"], 1)
        self.assertEqual(payload["renderCollectionsCount"], 1)
        self.assertEqual(payload["renderFilterArgs"], {"nodeTypes": ["tag"], "currentValue": "tag"})
        self.assertEqual(payload["rawNodeKeys"], ["tag:identity"])
        self.assertEqual(payload["rawEdgeCount"], 0)

    def test_apply_graph_filters_rerenders_existing_graph_state(self) -> None:
        html = WEBAPP.read_text()
        match = re.search(r"function applyGraphFilters\(\) \{.*?^    \}", html, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "applyGraphFilters function not found")

        script = f"""
const elements = {{
  graphSearchInput: {{ value: 'agent' }},
  graphTypeFilter: {{ value: 'fact' }},
}};
global.graphState = {{
  rawNodes: {{ 'fact:agent.name': {{ node_type: 'fact', label: 'agent.name' }} }},
  rawEdges: [],
  selectedNodeId: 'fact:agent.name',
}};
global.document = {{
  getElementById(id) {{
    if (!elements[id]) throw new Error('Missing mock element: ' + id);
    return elements[id];
  }},
}};
let buildArgs = null;
let renderOverviewCount = 0;
let renderVisualizationCount = 0;
let renderCollectionsCount = 0;
global.buildGraphViewModel = (nodesMap, edgesList, options) => {{
  buildArgs = {{ nodesMap, edgesList, options }};
  return {{ nodes: [], edges: [], nodeTypes: ['fact'], stats: {{ totalNodes: 1, totalEdges: 0, visibleNodes: 1, visibleEdges: 0 }}, relationCounts: {{}} }};
}};
global.renderGraphOverview = () => {{ renderOverviewCount += 1; }};
global.renderGraphVisualization = () => {{ renderVisualizationCount += 1; }};
global.renderGraphCollections = () => {{ renderCollectionsCount += 1; }};
{match.group(0)}

applyGraphFilters();
console.log(JSON.stringify({{
  buildArgs,
  renderOverviewCount,
  renderVisualizationCount,
  renderCollectionsCount,
}}));
"""
        result = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["buildArgs"]["options"], {"search": "agent", "nodeType": "fact", "selectedNodeId": "fact:agent.name"})
        self.assertEqual(payload["renderOverviewCount"], 1)
        self.assertEqual(payload["renderVisualizationCount"], 1)
        self.assertEqual(payload["renderCollectionsCount"], 1)


if __name__ == "__main__":
    unittest.main()
