import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const DEFAULT_TASK_ID = "task-20260527T223527-0b0ecd01";
const API_SNAPSHOT = "/api/snapshot?task_id=";
const API_TASKS = "/api/tasks";
const POLL_MS = 3500;
const EDGE_TYPES = ["triggers", "may_trigger", "evaluates", "supports", "constrains", "complements", "augments", "precedes"];
const ACTIVATION_TYPES = new Set(["triggers", "may_trigger", "evaluates"]);
const CONTEXT_ONLY_TYPES = new Set(["supports", "constrains", "complements", "augments", "precedes"]);
const NODE_STATES = ["idle", "candidate", "activated", "running", "completed", "skipped", "deferred", "blocked", "failed", "delivered"];

const colors = {
  triggers: 0x78e1ff,
  may_trigger: 0xffd166,
  evaluates: 0xc7a0ff,
  supports: 0x7ab8ff,
  constrains: 0xff7f50,
  complements: 0x56d6c9,
  augments: 0x68d391,
  precedes: 0xa8b4c8,
  idle: 0x41506a,
  candidate: 0xffd166,
  activated: 0x78e1ff,
  running: 0x78e1ff,
  completed: 0x6ee7a8,
  skipped: 0x69778e,
  deferred: 0xf5b84b,
  blocked: 0xff6b6b,
  failed: 0xff6b6b,
  delivered: 0xf6c453,
  graph: 0x78e1ff,
  policy: 0xffd166,
  ledger: 0x7ab8ff,
  runtime: 0x6ee7a8,
  learning: 0xc7a0ff
};

const state = {
  snapshot: null,
  selected: null,
  eventIndex: 0,
  playing: true,
  speed: 1,
  reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  concept: "all",
  enabledEdges: new Set(EDGE_TYPES),
  enabledStates: new Set(NODE_STATES),
  labels: new Map(),
  sceneObjects: {
    nodes: new Map(),
    edges: new Map(),
    blocks: new Map(),
    concepts: new Map()
  },
  pollTimer: null,
  replayTimer: 0,
  lastCopiedRefs: []
};

const el = {
  app: document.getElementById("app"),
  mount: document.getElementById("sceneMount"),
  labelLayer: document.getElementById("labelLayer"),
  traceSelect: document.getElementById("traceSelect"),
  modeBadge: document.getElementById("modeBadge"),
  taskIdLabel: document.getElementById("taskIdLabel"),
  syncLabel: document.getElementById("syncLabel"),
  nodeCount: document.getElementById("nodeCount"),
  edgeCount: document.getElementById("edgeCount"),
  eventCount: document.getElementById("eventCount"),
  handoffCount: document.getElementById("handoffCount"),
  edgeFilters: document.getElementById("edgeFilters"),
  stateFilters: document.getElementById("stateFilters"),
  conceptFilters: document.getElementById("conceptFilters"),
  inspectorTitle: document.getElementById("inspectorTitle"),
  inspectorBody: document.getElementById("inspectorBody"),
  copyRef: document.getElementById("copyRef"),
  timelineRange: document.getElementById("timelineRange"),
  eventPreview: document.getElementById("eventPreview"),
  playPause: document.getElementById("playPause"),
  stepBack: document.getElementById("stepBack"),
  stepForward: document.getElementById("stepForward"),
  speedSelect: document.getElementById("speedSelect"),
  searchInput: document.getElementById("searchInput"),
  searchResults: document.getElementById("searchResults"),
  themeToggle: document.getElementById("themeToggle"),
  motionToggle: document.getElementById("motionToggle"),
  resetCamera: document.getElementById("resetCamera")
};

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(el.mount.clientWidth, el.mount.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
el.mount.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x070a10, 0.018);

const camera = new THREE.PerspectiveCamera(48, el.mount.clientWidth / el.mount.clientHeight, 0.1, 1000);
camera.position.set(0, 18, 34);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.target.set(0, 0, 0);
controls.maxDistance = 84;
controls.minDistance = 12;

const raycaster = new THREE.Raycaster();
raycaster.params.Line.threshold = 0.32;
const pointer = new THREE.Vector2();
const clock = new THREE.Clock();

const root = new THREE.Group();
scene.add(root);
scene.add(new THREE.AmbientLight(0xb8c7dc, 0.48));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
keyLight.position.set(8, 18, 10);
scene.add(keyLight);
const rimLight = new THREE.PointLight(0x78e1ff, 1.35, 80);
rimLight.position.set(-16, 12, 10);
scene.add(rimLight);

const materials = {
  transparent: new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, depthWrite: false })
};

boot();

async function boot() {
  createFilterControls();
  bindUi();
  await loadTasks();
  await refreshSnapshot("latest");
  startPolling();
  animate();
}

function bindUi() {
  el.traceSelect.addEventListener("change", () => refreshSnapshot(el.traceSelect.value || "latest"));
  el.themeToggle.addEventListener("click", () => {
    const next = el.app.dataset.theme === "dark" ? "light" : "dark";
    el.app.dataset.theme = next;
    scene.fog.color.set(next === "dark" ? 0x070a10 : 0xf5f7fb);
  });
  el.motionToggle.addEventListener("click", () => {
    state.reducedMotion = !state.reducedMotion;
    el.motionToggle.classList.toggle("is-active", state.reducedMotion);
  });
  el.resetCamera.addEventListener("click", resetCamera);
  el.playPause.addEventListener("click", () => {
    state.playing = !state.playing;
    el.playPause.textContent = state.playing ? "Ⅱ" : "▶";
  });
  el.stepBack.addEventListener("click", () => setEventIndex(state.eventIndex - 1));
  el.stepForward.addEventListener("click", () => setEventIndex(state.eventIndex + 1));
  el.speedSelect.addEventListener("change", () => {
    state.speed = Number(el.speedSelect.value) || 1;
  });
  el.timelineRange.addEventListener("input", () => setEventIndex(Number(el.timelineRange.value)));
  el.searchInput.addEventListener("input", renderSearchResults);
  el.copyRef.addEventListener("click", async () => {
    const text = state.lastCopiedRefs.join("\n");
    if (!text) return;
    await navigator.clipboard?.writeText(text).catch(() => null);
    el.copyRef.textContent = "Copied";
    setTimeout(() => (el.copyRef.textContent = "Copy refs"), 900);
  });
  el.conceptFilters.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-concept]");
    if (!button) return;
    state.concept = button.dataset.concept;
    [...el.conceptFilters.querySelectorAll("button")].forEach((item) => item.classList.toggle("is-active", item === button));
    applySceneFilters();
  });
  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  renderer.domElement.addEventListener("dblclick", focusSelection);
  window.addEventListener("resize", onResize);
  document.addEventListener("keydown", onKeyDown);
}

function createFilterControls() {
  el.edgeFilters.innerHTML = EDGE_TYPES.map((type) => filterItem("edge", type, true, relationLabel(type))).join("");
  el.stateFilters.innerHTML = NODE_STATES.map((type) => filterItem("state", type, true, type)).join("");
  el.edgeFilters.addEventListener("change", (event) => {
    const input = event.target.closest("input");
    if (!input) return;
    toggleSet(state.enabledEdges, input.value, input.checked);
    applySceneFilters();
  });
  el.stateFilters.addEventListener("change", (event) => {
    const input = event.target.closest("input");
    if (!input) return;
    toggleSet(state.enabledStates, input.value, input.checked);
    applySceneFilters();
  });
}

function filterItem(kind, value, checked, label) {
  return `
    <label class="check-item">
      <input type="checkbox" value="${escapeHtml(value)}" ${checked ? "checked" : ""} />
      <span>${escapeHtml(label)}</span>
      <span class="mono">${kind === "edge" ? edgeSemantics(value) : ""}</span>
    </label>
  `;
}

function toggleSet(set, value, enabled) {
  if (enabled) set.add(value);
  else set.delete(value);
}

async function loadTasks() {
  try {
    const response = await fetch(API_TASKS, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const tasks = await response.json();
    const list = Array.isArray(tasks) ? tasks : tasks.tasks || [];
    for (const item of list) {
      const id = typeof item === "string" ? item : item.taskId || item.task_id || item.id;
      if (!id) continue;
      const option = document.createElement("option");
      option.value = id;
      option.textContent = id;
      el.traceSelect.appendChild(option);
    }
  } catch {
    const option = document.createElement("option");
    option.value = DEFAULT_TASK_ID;
    option.textContent = DEFAULT_TASK_ID;
    el.traceSelect.appendChild(option);
  }
}

async function refreshSnapshot(taskId) {
  const wanted = taskId === "latest" ? "latest" : taskId || DEFAULT_TASK_ID;
  try {
    const api = await fetchJson(`${API_SNAPSHOT}${encodeURIComponent(wanted)}`);
    setSnapshot(normalizeSnapshot(api, "live"));
  } catch (apiError) {
    try {
      const repo = await loadRepoSnapshot(wanted === "latest" ? DEFAULT_TASK_ID : wanted);
      setSnapshot(repo);
    } catch (repoError) {
      setSnapshot(createDemoSnapshot(apiError, repoError));
    }
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

async function fetchTextAny(paths) {
  const errors = [];
  for (const path of paths) {
    try {
      const response = await fetch(encodeURI(path), { cache: "no-store" });
      if (response.ok) return response.text();
      errors.push(`${path}: ${response.status}`);
    } catch (error) {
      errors.push(`${path}: ${error.message}`);
    }
  }
  throw new Error(errors.join("; "));
}

async function fetchYaml(paths) {
  const text = await fetchTextAny(paths);
  return window.jsyaml.load(text);
}

async function loadRepoSnapshot(taskId) {
  const [nodesDoc, relationsDoc, manifest, graphState, eventsDoc] = await Promise.all([
    fetchYaml(["/ontology/nodes.yaml", "../ontology/nodes.yaml"]),
    fetchYaml(["/ontology/relations.yaml", "../ontology/relations.yaml"]),
    fetchYaml([`/traces/${taskId}/manifest.yaml`, `../traces/${taskId}/manifest.yaml`]),
    fetchYaml([`/traces/${taskId}/state.yaml`, `../traces/${taskId}/state.yaml`]),
    fetchYaml([`/traces/${taskId}/events.yaml`, `../traces/${taskId}/events.yaml`])
  ]);
  const handoffTrail = manifest.handoff_trail || [];
  const handoffs = await Promise.all(handoffTrail.map(async (item) => {
    try {
      const data = await fetchYaml([`/traces/${taskId}/${item.ref}`, `../traces/${taskId}/${item.ref}`]);
      return normalizeHandoff(data, item.ref);
    } catch {
      return normalizeHandoff(item, item.ref);
    }
  }));
  return normalizeSnapshot({
    schema: "silicon_org.visualizer.snapshot.v1",
    generatedAt: new Date().toISOString(),
    graph: {
      nodes: (nodesDoc.nodes || []).map((node) => ({
        id: node.role,
        title: node.title,
        layer: node.layer,
        domain: node.domain,
        carriesSoul: Boolean(node.carries_soul),
        harnessRef: node.harness_ref,
        skillRef: node.skill_ref,
        sourceRefs: ["ontology/nodes.yaml"]
      })),
      edges: (relationsDoc.relations || []).map((edge, index) => normalizeEdge(edge, index))
    },
    run: {
      task_id: manifest.task_id || taskId,
      mode: "replay",
      manifest,
      node_states: graphState.node_states || {},
      convergence: graphState.convergence || {},
      summary: manifest.task_summary
    },
    ledger: {
      artifacts: manifest.artifact_index || [],
      handoffs,
      events: normalizeEvents(eventsDoc.events || [])
    },
    policy: { candidates: extractCandidates(eventsDoc.events || []) },
    learning: { signals: [], proposals: [] },
    source: {
      generated_at: new Date().toISOString(),
      refs: ["ontology/nodes.yaml", "ontology/relations.yaml", `traces/${taskId}/manifest.yaml`, `traces/${taskId}/state.yaml`, `traces/${taskId}/events.yaml`],
      warnings: []
    }
  }, "replay");
}

function normalizeSnapshot(raw, modeHint) {
  const graph = raw.graph || raw.org || {};
  const run = raw.run || raw.task || {};
  const trace = raw.trace || {};
  const traceState = trace.state || {};
  const ledger = raw.ledger || {};
  const policy = raw.policy || {};
  const learning = raw.learning || {};
  const manifest = run.manifest || trace.manifest || raw.manifest || {};
  const nodeStates = run.node_states || run.nodeStates || traceState.node_states || traceState.nodeStates || ledger.nodes || {};
  const convergence = run.convergence || ledger.convergence || policy.convergence || traceState.convergence || {};
  const rawEvents = ledger.events || run.events || trace.events || [];
  const rawHandoffs = ledger.handoffs || run.handoffs || trace.handoffs || [];
  const artifacts = ledger.artifacts || run.artifacts || trace.artifacts || raw.artifacts || [];
  const nodes = (graph.nodes || []).map((node) => {
    const id = node.id || node.role;
    const ledgerState = nodeStates[id] || {};
    return {
      id,
      title: node.title || id,
      layer: node.layer ?? null,
      domain: node.domain || "unknown",
      carriesSoul: Boolean(node.carriesSoul ?? node.carries_soul),
      harnessRef: node.harnessRef || node.harness_ref || node.registryRef || "",
      skillRef: node.skillRef || node.skill_ref || "",
      status: normalizeNodeStatus(ledgerState.status || node.status || "idle"),
      artifactRefs: ledgerState.output_artifact_ids || ledgerState.artifact_refs || [],
      sourceRefs: node.sourceRefs || node.source_refs || ["ontology/nodes.yaml"]
    };
  });
  const edges = (graph.edges || []).map((edge, index) => normalizeEdge(edge, index));
  const events = normalizeEvents(rawEvents);
  const handoffs = rawHandoffs.map((item) => normalizeHandoff(item, item.ref || item.sourceRef || item.source_ref));
  const candidates = policy.candidates || policy.decisions || extractCandidates(events);
  const taskId = raw.taskId || raw.task_id || run.task_id || run.taskId || manifest.task_id || DEFAULT_TASK_ID;
  return {
    schema: raw.schema || "silicon_org.visualizer.snapshot.v1",
    generatedAt: raw.generatedAt || raw.generated_at || new Date().toISOString(),
    mode: run.mode || (trace.taskDir ? "live" : modeHint) || "demo",
    graph: { nodes, edges },
    run: {
      taskId,
      summary: run.summary || run.task_summary || manifest.task_summary || "Silicon Org operations visualizer",
      manifest,
      nodeStates,
      convergence
    },
    ledger: { events, handoffs, artifacts },
    policy: { candidates },
    learning,
    source: raw.source || { generated_at: raw.generatedAt || raw.generated_at || new Date().toISOString(), refs: trace.sourceRefs || graph.sourceRefs || [], warnings: [] }
  };
}

function normalizeEdge(edge, index) {
  const relationType = edge.relation_type || edge.relationType || edge.type || "supports";
  const probability = edge.probability ?? edge.weights?.probability?.value;
  const necessity = edge.necessity ?? edge.weights?.necessity?.value;
  const strictness = edge.strictness ?? edge.weights?.strictness?.value;
  const confidence =
    edge.confidence ??
    edge.weights?.probability?.confidence ??
    edge.weights?.necessity?.confidence ??
    edge.weights?.strictness?.confidence ??
    null;
  return {
    id: edge.id || `${edge.from}->${edge.to}:${relationType}:${index}`,
    from: edge.from,
    to: edge.to,
    relationType,
    weight: coerceWeight(probability ?? necessity ?? strictness),
    confidence: coerceWeight(confidence),
    condition: edge.condition || edge.weights?.probability?.condition || edge.weights?.condition,
    activationCapable: edge.activationCapable ?? edge.activation_capable ?? ACTIVATION_TYPES.has(relationType),
    sourceRef: edge.sourceRef || edge.source_ref || "ontology/relations.yaml"
  };
}

function normalizeEvents(events) {
  return events.map((event, index) => {
    const payload = event.payload || {};
    const detail = payload.detail || event.detail || "";
    const nodeFromDetail = typeof detail === "string" && detail.includes(":") ? detail.split(":")[0].trim() : null;
    return {
      sequence: event.sequence ?? index,
      eventId: event.event_id || event.id || `ev-${String(index + 1).padStart(3, "0")}`,
      timestamp: event.timestamp || "",
      eventType: event.event_type || event.eventType || event.type || "event",
      actor: payload.role || payload.from || event.nodeId || nodeFromDetail || null,
      nodeId: event.nodeId || payload.role || nodeFromDetail || payload.to || null,
      from: payload.from || event.edge?.from,
      to: payload.to || event.edge?.to,
      relationType: payload.relation_type || event.edge?.relationType,
      decision: payload.decision,
      detail,
      payload,
      sourceRef: event.sourceRef || "events.yaml"
    };
  });
}

function normalizeHandoff(item, ref) {
  const block = item.context_block || item.contextBlock || {};
  const compressed = block.compressed_context || block.compressedContext || {};
  return {
    id: ref || `${item.from}->${item.to}:${item.timestamp || "handoff"}`,
    ref,
    timestamp: item.timestamp || "",
    from: item.from,
    to: item.to,
    relationType: item.relation_type || item.relationType,
    focus: item.focus || "",
    artifactRefs: item.artifact_refs || item.artifactRefs || item.deliverable?.artifact_refs || [],
    deliverable: item.deliverable || null,
    contextBlock: {
      digest: block.context_digest || block.contextDigest || item.context_block_digest || item.context_digest || item.contextDigest,
      source: block.source || {},
      compressed,
      previousBlocks: block.previous_blocks || block.previousBlocks || []
    },
    soulRef: item.soul_ref || item.soulRef,
    sourceRef: ref
  };
}

function normalizeNodeStatus(status) {
  if (status === "active") return "activated";
  if (status === "in_progress") return "running";
  return NODE_STATES.includes(status) ? status : "idle";
}

function coerceWeight(value) {
  if (value === null || value === undefined) return null;
  if (typeof value === "number") return value;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function extractCandidates(events) {
  return normalizeEvents(events).filter((event) => event.eventType === "activation_decision").map((event) => ({
    from: event.from,
    to: event.to,
    relationType: event.relationType,
    decision: event.decision,
    reason: event.detail,
    timestamp: event.timestamp,
    sourceRef: event.sourceRef
  }));
}

function setSnapshot(snapshot) {
  state.snapshot = snapshot;
  state.eventIndex = Math.max(0, snapshot.ledger.events.length - 1);
  buildScene(snapshot);
  renderHud(snapshot);
  setEventIndex(state.eventIndex);
  renderSearchResults();
  applySceneFilters();
}

function buildScene(snapshot) {
  clearGroup(root);
  clearLabels();
  state.sceneObjects.nodes.clear();
  state.sceneObjects.edges.clear();
  state.sceneObjects.blocks.clear();
  state.sceneObjects.concepts.clear();
  const positions = computeNodePositions(snapshot.graph.nodes);
  snapshot.graph.nodes.forEach((node) => {
    const object = makeNodeObject(node, positions.get(node.id));
    root.add(object);
    state.sceneObjects.nodes.set(node.id, object);
    addLabel(node.id, node.id, object.position, "node-label");
  });
  addConceptObjects();
  snapshot.graph.edges.forEach((edge) => {
    const from = positions.get(edge.from);
    const to = positions.get(edge.to);
    if (!from || !to) return;
    const object = makeEdgeObject(edge, from, to);
    root.add(object);
    state.sceneObjects.edges.set(edge.id, object);
  });
  snapshot.ledger.handoffs.forEach((handoff, index) => {
    const from = positions.get(handoff.from);
    const to = positions.get(handoff.to);
    if (!from || !to) return;
    const object = makeHandoffObject(handoff, from, to, index);
    root.add(object);
    state.sceneObjects.blocks.set(handoff.id, object);
  });
  addLedgerPlane();
}

function clearGroup(group) {
  while (group.children.length) {
    const child = group.children.pop();
    child.traverse?.((object) => {
      object.geometry?.dispose?.();
      if (Array.isArray(object.material)) object.material.forEach((mat) => mat.dispose?.());
      else object.material?.dispose?.();
    });
  }
}

function clearLabels() {
  state.labels.clear();
  el.labelLayer.innerHTML = "";
}

function computeNodePositions(nodes) {
  const byLayer = new Map();
  nodes.forEach((node) => {
    const key = node.layer === 1 ? "layer1" : node.layer === 3 ? "layer3" : node.domain === "learning" || node.domain === "org-dev" ? "meta" : "layer2";
    if (!byLayer.has(key)) byLayer.set(key, []);
    byLayer.get(key).push(node);
  });
  const specs = {
    layer1: { y: 6.4, z: -7.2, radius: 8.8, start: -0.2 },
    layer2: { y: 0.2, z: 0, radius: 15.2, start: 0.05 },
    layer3: { y: -5.8, z: 7.4, radius: 10.6, start: 0.3 },
    meta: { y: 1.4, z: 13.5, radius: 18.2, start: 0.95 }
  };
  const positions = new Map();
  for (const [key, list] of byLayer.entries()) {
    const spec = specs[key];
    list.sort((a, b) => a.id.localeCompare(b.id));
    list.forEach((node, index) => {
      const spread = key === "layer2" ? Math.PI * 1.5 : Math.PI * 1.16;
      const angle = spec.start + (list.length === 1 ? 0 : (index / (list.length - 1) - 0.5) * spread);
      const x = Math.sin(angle) * spec.radius;
      const z = spec.z + Math.cos(angle) * spec.radius * 0.48;
      positions.set(node.id, new THREE.Vector3(x, spec.y, z));
    });
  }
  return positions;
}

function makeNodeObject(node, position) {
  const group = new THREE.Group();
  group.position.copy(position);
  group.userData = { kind: "node", item: node, refs: node.sourceRefs };
  const color = colors[node.status] || colors.idle;
  const geometry = new THREE.SphereGeometry(node.layer === 1 ? 0.58 : node.layer === 3 ? 0.66 : 0.62, 32, 16);
  const material = new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: node.status === "completed" ? 0.3 : node.status === "activated" ? 0.46 : 0.12,
    roughness: 0.38,
    metalness: 0.22,
    transparent: true,
    opacity: node.status === "idle" ? 0.62 : 0.96
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData = group.userData;
  group.add(mesh);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.78, 0.025, 8, 48),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: node.status === "idle" ? 0.16 : 0.64 })
  );
  ring.rotation.x = Math.PI / 2;
  ring.userData = group.userData;
  group.add(ring);
  if (node.artifactRefs?.length) {
    const badge = new THREE.Mesh(
      new THREE.BoxGeometry(0.56, 0.22, 0.22),
      new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0x78e1ff, emissiveIntensity: 0.12 })
    );
    badge.position.set(0.42, 0.62, 0.08);
    badge.userData = group.userData;
    group.add(badge);
  }
  return group;
}

function makeEdgeObject(edge, from, to) {
  const mid = from.clone().lerp(to, 0.5);
  const lift = edge.relationType === "evaluates" ? 2.6 : edge.activationCapable ? 1.3 : 0.35;
  const curve = new THREE.QuadraticBezierCurve3(from, mid.add(new THREE.Vector3(0, lift, 0)), to);
  const points = curve.getPoints(edge.relationType === "may_trigger" ? 14 : 36);
  const geometry = new THREE.BufferGeometry().setFromPoints(edge.relationType === "may_trigger" ? dashedPoints(points) : points);
  const material = new THREE.LineBasicMaterial({
    color: colors[edge.relationType] || colors.precedes,
    transparent: true,
    opacity: edge.activationCapable ? 0.52 : 0.22,
    linewidth: 1
  });
  const line = new THREE.LineSegments(geometry, material);
  if (edge.relationType !== "may_trigger") {
    line.geometry = new THREE.BufferGeometry().setFromPoints(points);
    line.type = "Line";
  }
  line.userData = { kind: "edge", item: edge, refs: [edge.sourceRef] };
  return line;
}

function dashedPoints(points) {
  const result = [];
  for (let index = 0; index < points.length - 1; index += 2) {
    result.push(points[index], points[index + 1]);
  }
  return result;
}

function makeHandoffObject(handoff, from, to, index) {
  const group = new THREE.Group();
  const geometry = new THREE.BoxGeometry(0.54, 0.38, 0.38);
  const material = new THREE.MeshStandardMaterial({
    color: colors[handoff.relationType] || 0xffffff,
    emissive: colors[handoff.relationType] || 0xffffff,
    emissiveIntensity: 0.48,
    roughness: 0.24,
    metalness: 0.34
  });
  const block = new THREE.Mesh(geometry, material);
  group.add(block);
  const slit = new THREE.Mesh(
    new THREE.BoxGeometry(0.04, 0.46, 0.48),
    new THREE.MeshBasicMaterial({ color: handoff.soulRef ? 0xffffff : 0x1f2937, transparent: true, opacity: handoff.soulRef ? 0.92 : 0.18 })
  );
  slit.position.x = 0.31;
  group.add(slit);
  group.userData = { kind: "handoff", item: handoff, refs: [handoff.sourceRef, ...(handoff.artifactRefs || [])] };
  block.userData = group.userData;
  slit.userData = group.userData;
  group.userData.path = { from: from.clone(), to: to.clone(), offset: index * 0.09 };
  updateHandoffPosition(group, index / Math.max(1, state.snapshot?.ledger?.handoffs?.length || 1));
  return group;
}

function updateHandoffPosition(group, phase) {
  const path = group.userData.path;
  if (!path) return;
  const t = state.reducedMotion ? 1 : (phase % 1);
  const eased = 0.5 - Math.cos(t * Math.PI) / 2;
  const mid = path.from.clone().lerp(path.to, eased);
  mid.y += Math.sin(eased * Math.PI) * 1.8 + path.offset;
  group.position.copy(mid);
  group.lookAt(path.to);
}

function addConceptObjects() {
  const concepts = [
    { id: "graph", label: "Graph", position: [0, 0, 0], shape: "octa" },
    { id: "policy", label: "Policy", position: [0, 9.8, -1.6], shape: "gate" },
    { id: "ledger", label: "Ledger", position: [0, -8.6, 0], shape: "plane" },
    { id: "runtime", label: "Runtime", position: [-18.6, 1.8, -1.5], shape: "spine" },
    { id: "learning", label: "Learning", position: [18.6, 1.8, 2.8], shape: "halo" }
  ];
  concepts.forEach((concept) => {
    const group = new THREE.Group();
    group.position.set(...concept.position);
    group.userData = { kind: "concept", item: concept, refs: ["org/CONTEXT_BLOCK.md"] };
    const color = colors[concept.id];
    let mesh;
    if (concept.shape === "gate") mesh = new THREE.Mesh(new THREE.TorusGeometry(1.1, 0.055, 8, 64), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.78 }));
    else if (concept.shape === "plane") mesh = new THREE.Mesh(new THREE.BoxGeometry(10, 0.05, 4.5), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.22 }));
    else if (concept.shape === "spine") mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 12, 16), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.68 }));
    else if (concept.shape === "halo") mesh = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.035, 8, 96), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.66 }));
    else mesh = new THREE.Mesh(new THREE.OctahedronGeometry(1.1, 0), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.32, wireframe: true }));
    mesh.userData = group.userData;
    group.add(mesh);
    root.add(group);
    state.sceneObjects.concepts.set(concept.id, group);
    addLabel(`concept-${concept.id}`, concept.label, group.position, "concept-label");
  });
}

function addLedgerPlane() {
  const grid = new THREE.GridHelper(38, 24, 0x7ab8ff, 0x334155);
  grid.position.y = -8.7;
  grid.material.transparent = true;
  grid.material.opacity = 0.18;
  root.add(grid);
}

function renderHud(snapshot) {
  el.modeBadge.textContent = snapshot.mode;
  el.taskIdLabel.textContent = snapshot.run.taskId;
  el.syncLabel.textContent = `synced ${new Date(snapshot.generatedAt).toLocaleTimeString()}`;
  el.nodeCount.textContent = String(snapshot.graph.nodes.length);
  el.edgeCount.textContent = String(snapshot.graph.edges.length);
  el.eventCount.textContent = String(snapshot.ledger.events.length);
  el.handoffCount.textContent = String(snapshot.ledger.handoffs.length);
  el.timelineRange.max = String(Math.max(0, snapshot.ledger.events.length - 1));
}

function setEventIndex(index) {
  const events = state.snapshot?.ledger.events || [];
  state.eventIndex = Math.max(0, Math.min(index, Math.max(0, events.length - 1)));
  el.timelineRange.value = String(state.eventIndex);
  const event = events[state.eventIndex];
  if (!event) {
    el.eventPreview.textContent = "No events loaded";
    return;
  }
  el.eventPreview.textContent = `${event.eventId} · ${event.eventType} · ${event.timestamp || "no timestamp"} · ${event.detail || event.actor || ""}`;
  applyTimelineState();
}

function applyTimelineState() {
  const snapshot = state.snapshot;
  if (!snapshot) return;
  const activeStatuses = deriveStatusesAtEvent(snapshot, state.eventIndex);
  for (const node of snapshot.graph.nodes) {
    const object = state.sceneObjects.nodes.get(node.id);
    if (!object) continue;
    const status = activeStatuses.get(node.id) || node.status;
    const mesh = object.children.find((child) => child.isMesh);
    if (mesh?.material) {
      mesh.material.color.set(colors[status] || colors.idle);
      mesh.material.emissive?.set(colors[status] || colors.idle);
      mesh.material.emissiveIntensity = status === "completed" ? 0.32 : status === "activated" ? 0.54 : 0.14;
      mesh.material.opacity = status === "idle" ? 0.52 : 0.96;
    }
    object.userData.timelineStatus = status;
  }
  applySceneFilters();
}

function deriveStatusesAtEvent(snapshot, index) {
  const statuses = new Map(snapshot.graph.nodes.map((node) => [node.id, "idle"]));
  for (let cursor = 0; cursor <= index; cursor += 1) {
    const event = snapshot.ledger.events[cursor];
    if (!event) continue;
    if (event.eventType === "node_activated" && event.nodeId) statuses.set(event.nodeId, "activated");
    if (event.eventType === "node_completed" && event.nodeId) statuses.set(event.nodeId, "completed");
    if (event.eventType === "node_skipped" && event.nodeId) statuses.set(event.nodeId, "skipped");
    if (event.eventType === "activation_decision" && event.to) {
      if (event.decision === "activate") statuses.set(event.to, statuses.get(event.to) === "completed" ? "completed" : "candidate");
      if (event.decision === "skip") statuses.set(event.to, statuses.get(event.to) === "completed" ? "completed" : "skipped");
      if (event.decision === "defer") statuses.set(event.to, "deferred");
    }
  }
  return statuses;
}

function applySceneFilters() {
  for (const [id, object] of state.sceneObjects.nodes) {
    const node = object.userData.item;
    const status = object.userData.timelineStatus || node.status;
    object.visible = state.enabledStates.has(status) && conceptAllowsNode(node);
    setLabelVisible(id, object.visible);
  }
  for (const [id, object] of state.sceneObjects.edges) {
    const edge = object.userData.item;
    object.visible = state.enabledEdges.has(edge.relationType) && conceptAllowsEdge(edge);
  }
  for (const [id, object] of state.sceneObjects.blocks) {
    object.visible = state.concept === "all" || state.concept === "ledger" || state.concept === "runtime";
  }
  for (const [id, object] of state.sceneObjects.concepts) {
    object.visible = state.concept === "all" || state.concept === id;
    setLabelVisible(`concept-${id}`, object.visible);
  }
}

function conceptAllowsNode(node) {
  if (state.concept === "all" || state.concept === "graph") return true;
  if (state.concept === "runtime") return node.status !== "idle";
  if (state.concept === "ledger") return Boolean(node.artifactRefs?.length) || node.status !== "idle";
  if (state.concept === "learning") return node.domain === "learning" || node.domain === "org-dev";
  if (state.concept === "policy") return node.status === "candidate" || node.status === "deferred" || node.status === "skipped" || node.status === "blocked";
  return true;
}

function conceptAllowsEdge(edge) {
  if (state.concept === "all" || state.concept === "graph") return true;
  if (state.concept === "policy") return edge.activationCapable;
  if (state.concept === "ledger") return false;
  if (state.concept === "runtime") return edge.activationCapable;
  if (state.concept === "learning") return edge.weight !== null || edge.confidence !== null;
  return true;
}

function renderSearchResults() {
  const query = el.searchInput.value.trim().toLowerCase();
  if (!query || !state.snapshot) {
    el.searchResults.innerHTML = "";
    return;
  }
  const results = [];
  for (const node of state.snapshot.graph.nodes) {
    if ([node.id, node.title, node.domain].some((value) => String(value).toLowerCase().includes(query))) results.push({ type: "node", id: node.id, label: node.id });
  }
  for (const handoff of state.snapshot.ledger.handoffs) {
    const haystack = [handoff.ref, handoff.from, handoff.to, handoff.contextBlock.digest].join(" ").toLowerCase();
    if (haystack.includes(query)) results.push({ type: "handoff", id: handoff.id, label: handoff.ref || handoff.id });
  }
  for (const event of state.snapshot.ledger.events) {
    const haystack = [event.eventId, event.eventType, event.detail, event.from, event.to].join(" ").toLowerCase();
    if (haystack.includes(query)) results.push({ type: "event", id: event.sequence, label: `${event.eventId} ${event.eventType}` });
  }
  el.searchResults.innerHTML = results.slice(0, 8).map((result) => `<button class="result-button" data-type="${result.type}" data-id="${escapeHtml(String(result.id))}" type="button">${escapeHtml(result.type)} · ${escapeHtml(result.label)}</button>`).join("");
  el.searchResults.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.type === "node") selectObject(state.sceneObjects.nodes.get(button.dataset.id));
      if (button.dataset.type === "handoff") selectObject(state.sceneObjects.blocks.get(button.dataset.id));
      if (button.dataset.type === "event") {
        setEventIndex(Number(button.dataset.id));
        inspectEvent(state.snapshot.ledger.events[Number(button.dataset.id)]);
      }
    });
  });
}

function onPointerDown(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const targets = [];
  root.traverse((object) => {
    if (object.userData?.kind && object.visible) targets.push(object);
  });
  const hit = raycaster.intersectObjects(targets, true)[0];
  if (hit) selectObject(hit.object);
}

function selectObject(object) {
  if (!object) return;
  const owner = object.userData?.kind ? object : object.parent;
  const data = object.userData?.kind ? object.userData : owner?.userData;
  if (!data) return;
  state.selected = data;
  if (data.kind === "node") inspectNode(data.item);
  if (data.kind === "edge") inspectEdge(data.item);
  if (data.kind === "handoff") inspectHandoff(data.item);
  if (data.kind === "concept") inspectConcept(data.item);
}

function focusSelection() {
  if (!state.selected) return;
  let object;
  if (state.selected.kind === "node") object = state.sceneObjects.nodes.get(state.selected.item.id);
  if (state.selected.kind === "handoff") object = state.sceneObjects.blocks.get(state.selected.item.id);
  if (state.selected.kind === "concept") object = state.sceneObjects.concepts.get(state.selected.item.id);
  if (!object) return;
  controls.target.copy(object.position);
  camera.position.copy(object.position.clone().add(new THREE.Vector3(0, 7, 13)));
}

function inspectNode(node) {
  const inbound = state.snapshot.graph.edges.filter((edge) => edge.to === node.id);
  const outbound = state.snapshot.graph.edges.filter((edge) => edge.from === node.id);
  const handoffs = state.snapshot.ledger.handoffs.filter((handoff) => handoff.from === node.id || handoff.to === node.id);
  const decisions = state.snapshot.policy.candidates.filter((candidate) => candidate.from === node.id || candidate.to === node.id);
  state.lastCopiedRefs = [...node.sourceRefs, ...handoffs.map((handoff) => handoff.ref).filter(Boolean)];
  el.inspectorTitle.textContent = node.id;
  el.inspectorBody.innerHTML = `
    <div class="fact-list">
      ${fact("Role", `${paragraph(node.title)}<div class="tag-row">${tag(`layer ${node.layer ?? "?"}`)}${tag(node.domain)}${tag(node.status)}${node.carriesSoul ? tag("carries soul") : ""}</div>`)}
      ${fact("Implementation refs", `${paragraph(node.harnessRef || "no harness ref")}${paragraph(node.skillRef || "no skill ref")}`)}
      ${fact("Artifacts", list(node.artifactRefs?.length ? node.artifactRefs : ["none registered"]))}
      ${fact("Relations", `${paragraph(`${inbound.length} inbound · ${outbound.length} outbound`)}${relationSummary(outbound)}`)}
      ${fact("Handoffs", list(handoffs.map((handoff) => `${handoff.from} → ${handoff.to} · ${handoff.relationType}`)))}
      ${fact("Policy decisions", list(decisions.map((item) => `${item.from} → ${item.to}: ${item.decision} · ${item.reason}`)))}
    </div>
  `;
}

function inspectEdge(edge) {
  state.lastCopiedRefs = [edge.sourceRef];
  el.inspectorTitle.textContent = `${edge.from} → ${edge.to}`;
  el.inspectorBody.innerHTML = `
    <div class="fact-list">
      ${fact("Relation", `${paragraph(relationLabel(edge.relationType))}<div class="tag-row">${tag(edge.activationCapable ? "activation capable" : "context only")}${tag(edgeSemantics(edge.relationType))}</div>`)}
      ${fact("Weights", `${paragraph(`weight: ${edge.weight ?? "n/a"}`)}${paragraph(`confidence: ${edge.confidence ?? "n/a"}`)}${edge.condition ? paragraph(`condition: ${edge.condition}`) : ""}`)}
      ${fact("Source", paragraph(edge.sourceRef))}
      ${CONTEXT_ONLY_TYPES.has(edge.relationType) ? fact("Policy warning", paragraph("This relation can carry context or pressure but cannot activate a node by itself.")) : ""}
    </div>
  `;
}

function inspectHandoff(handoff) {
  const compressed = handoff.contextBlock.compressed || {};
  state.lastCopiedRefs = [handoff.ref, ...(handoff.artifactRefs || []), handoff.contextBlock.digest].filter(Boolean);
  el.inspectorTitle.textContent = `${handoff.from} → ${handoff.to}`;
  el.inspectorBody.innerHTML = `
    <div class="fact-list">
      ${fact("Handoff", `${paragraph(handoff.ref || handoff.id)}<div class="tag-row">${tag(handoff.relationType)}${handoff.soulRef ? tag("soul ref") : ""}</div>${paragraph(handoff.focus || "")}`)}
      ${fact("Deliverable", list(handoff.artifactRefs?.length ? handoff.artifactRefs : ["no artifact refs"]))}
      ${fact("Context digest", `${paragraph(handoff.contextBlock.digest || "missing")}${paragraph(`report: ${handoff.contextBlock.source?.context_compression_report_ref || "not supplied"}`)}`)}
      ${fact("Decisions", structuredItems(compressed.decisions))}
      ${fact("Constraints", structuredItems(compressed.constraints))}
      ${fact("Assumptions", structuredItems(compressed.assumptions))}
      ${fact("Open questions", structuredItems(compressed.open_questions))}
      ${fact("Omitted context", structuredItems(compressed.omitted_context))}
      ${fact("Digest chain", list((handoff.contextBlock.previousBlocks || []).map((block) => `${block.ref}: ${block.context_digest || block.contextDigest}`)))}
    </div>
  `;
}

function inspectConcept(concept) {
  const copy = {
    graph: "Static law: 35 nodes, typed edges, weights, and reachability.",
    policy: "Legal interpreter: Graph + Ledger facts become activate, skip, defer, block.",
    ledger: "Durable facts: manifest, state, events, artifacts, handoffs, context blocks.",
    runtime: "Executor: performs legal actions and writes back to Ledger.",
    learning: "Feedback layer: reads traces and proposes conservative graph/model/routing updates."
  };
  state.lastCopiedRefs = ["org/CONTEXT_BLOCK.md"];
  el.inspectorTitle.textContent = concept.label;
  el.inspectorBody.innerHTML = `<div class="fact-list">${fact(concept.label, paragraph(copy[concept.id]))}</div>`;
}

function inspectEvent(event) {
  state.lastCopiedRefs = [event.sourceRef, event.eventId].filter(Boolean);
  el.inspectorTitle.textContent = event.eventId;
  el.inspectorBody.innerHTML = `
    <div class="fact-list">
      ${fact("Event", `${paragraph(event.eventType)}${paragraph(event.timestamp)}${paragraph(event.detail || "")}`)}
      ${fact("Payload", `<pre>${escapeHtml(JSON.stringify(event.payload, null, 2))}</pre>`)}
    </div>
  `;
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const elapsed = clock.elapsedTime;
  if (state.playing && state.snapshot?.ledger.events.length) {
    state.replayTimer += delta * state.speed;
    if (state.replayTimer > 1.5) {
      state.replayTimer = 0;
      setEventIndex((state.eventIndex + 1) % state.snapshot.ledger.events.length);
    }
  }
  for (const object of state.sceneObjects.nodes.values()) {
    const status = object.userData.timelineStatus || object.userData.item.status;
    const pulse = !state.reducedMotion && (status === "activated" || status === "running" || status === "candidate");
    const scale = pulse ? 1 + Math.sin(elapsed * 3) * 0.08 : 1;
    object.scale.setScalar(scale);
  }
  let index = 0;
  for (const object of state.sceneObjects.blocks.values()) {
    updateHandoffPosition(object, state.reducedMotion ? 1 : (elapsed * 0.08 + index * 0.11) % 1);
    index += 1;
  }
  controls.update();
  renderer.render(scene, camera);
  updateLabels();
}

function updateLabels() {
  const width = el.mount.clientWidth;
  const height = el.mount.clientHeight;
  for (const [, data] of state.labels) {
    const position = data.position.clone().project(camera);
    const x = (position.x * 0.5 + 0.5) * width;
    const y = (-position.y * 0.5 + 0.5) * height;
    data.element.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    data.element.style.opacity = position.z < 1 ? "1" : "0";
  }
}

function addLabel(id, text, position, className) {
  const element = document.createElement("div");
  element.className = className;
  element.textContent = text;
  el.labelLayer.appendChild(element);
  state.labels.set(id, { element, position });
}

function setLabelVisible(id, visible) {
  const label = state.labels.get(id);
  if (label) label.element.style.display = visible ? "block" : "none";
}

function resetCamera() {
  camera.position.set(0, 18, 34);
  controls.target.set(0, 0, 0);
}

function onResize() {
  const width = el.mount.clientWidth;
  const height = el.mount.clientHeight;
  renderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function onKeyDown(event) {
  if (event.target.matches("input, select, textarea")) return;
  if (event.key === " ") {
    event.preventDefault();
    state.playing = !state.playing;
  }
  if (event.key === "ArrowRight") setEventIndex(state.eventIndex + 1);
  if (event.key === "ArrowLeft") setEventIndex(state.eventIndex - 1);
  if (event.key.toLowerCase() === "r") resetCamera();
}

function startPolling() {
  clearInterval(state.pollTimer);
  state.pollTimer = setInterval(() => {
    const taskId = el.traceSelect.value || "latest";
    refreshSnapshot(taskId);
  }, POLL_MS);
}

function createDemoSnapshot(apiError, repoError) {
  const nodes = [
    "triage", "zoom-out", "caveman", "grill-with-docs", "to-prd", "to-issues", "prototype",
    "architect", "api-designer", "database-engineer", "senior-engineer", "tdd", "diagnose",
    "refactor-specialist", "improve-codebase-architecture", "devops-engineer", "observability-engineer",
    "performance-engineer", "security-engineer", "ux-researcher-designer", "ui-design-system",
    "apple-hig-expert", "senior-frontend", "epic-design", "skill-scout", "hrbp", "delivery-prover",
    "customer-success", "graph-topologist", "code-reviewer", "grill-me", "dependency-auditor",
    "release-manager", "technical-writer", "handoff"
  ].map((id, index) => ({
    id,
    title: id,
    layer: index < 7 ? 1 : index < 26 ? 2 : 3,
    domain: id.includes("graph") ? "learning" : "demo",
    carriesSoul: ["prototype", "architect", "ux-researcher-designer", "ui-design-system", "senior-frontend", "epic-design"].includes(id),
    status: ["triage", "caveman", "prototype", "ux-researcher-designer", "architect"].includes(id) ? "completed" : id === "senior-frontend" ? "activated" : "idle",
    artifactRefs: id === "prototype" ? ["prototype-plan-v1"] : [],
    sourceRefs: ["embedded fallback"]
  }));
  const edgePairs = [
    ["triage", "to-prd", "triggers"], ["triage", "prototype", "may_trigger"], ["caveman", "ux-researcher-designer", "may_trigger"],
    ["prototype", "senior-frontend", "may_trigger"], ["ux-researcher-designer", "ui-design-system", "may_trigger"],
    ["architect", "senior-engineer", "triggers"], ["architect", "api-designer", "triggers"], ["senior-frontend", "code-reviewer", "triggers"],
    ["prototype", "delivery-prover", "triggers"], ["to-prd", "grill-me", "evaluates"], ["architect", "grill-me", "evaluates"]
  ];
  const edges = edgePairs.map(([from, to, relationType], index) => normalizeEdge({ from, to, type: relationType, weights: { probability: { value: 0.7, confidence: 0.2 } } }, index));
  const handoff = normalizeHandoff({
    from: "prototype",
    to: "senior-frontend",
    relation_type: "may_trigger",
    focus: "implement runnable Three.js viewer from prototype plan",
    artifact_refs: ["prototype-plan-v1"],
    context_block: {
      context_digest: "2b2d3b97f2465c9d9e7da65a3d5e330386853a9081cac377930e94b49f32acf1",
      source: { context_compression_report_ref: "artifacts/prototype-context-report-v1.yaml" },
      compressed_context: {
        decisions: [{ statement: "Prototype validates trace replay before realtime transport.", impact: "Use normalized snapshot first." }],
        constraints: [{ statement: "Ledger-derived facts are the only operational truth.", impact: "Do not render private runtime reasoning as fact." }],
        assumptions: [{ statement: "Static snapshot is enough for first demo.", risk: "Realtime transport comes later." }],
        open_questions: [],
        omitted_context: [{ source: "full runtime command examples", reason: "background_only" }]
      }
    },
    soul_ref: "org/soul.md"
  }, "embedded fallback handoff");
  return normalizeSnapshot({
    graph: { nodes, edges },
    run: { task_id: DEFAULT_TASK_ID, mode: "demo", summary: "Fallback demo snapshot" },
    ledger: {
      handoffs: [handoff],
      artifacts: [{ artifact_id: "prototype-plan-v1", producer: "prototype", type: "plan", status: "draft", ref: "artifacts/prototype-plan-v1.md" }],
      events: normalizeEvents([
        { event_id: "demo-001", timestamp: new Date().toISOString(), event_type: "node_activated", payload: { detail: "senior-frontend: activated" } },
        { event_id: "demo-002", timestamp: new Date().toISOString(), event_type: "activation_decision", payload: { from: "prototype", to: "senior-frontend", relation_type: "may_trigger", decision: "activate", detail: "implement runnable Three.js viewer" } }
      ])
    },
    policy: { candidates: [] },
    learning: { signals: [], proposals: [] },
    source: {
      generated_at: new Date().toISOString(),
      refs: ["embedded fallback"],
      warnings: [`API unavailable: ${apiError?.message || "unknown"}`, `Repo snapshot unavailable: ${repoError?.message || "unknown"}`]
    }
  }, "demo");
}

function relationLabel(type) {
  return type.replace("_", " ");
}

function edgeSemantics(type) {
  if (type === "triggers") return "activate";
  if (type === "may_trigger") return "conditional";
  if (type === "evaluates") return "review";
  return "context";
}

function fact(title, html) {
  return `<section class="fact"><b>${escapeHtml(title)}</b>${html}</section>`;
}

function paragraph(value) {
  return `<p>${escapeHtml(String(value || ""))}</p>`;
}

function list(items) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return paragraph("none");
  return `<ul>${values.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ul>`;
}

function structuredItems(items) {
  if (!items?.length) return paragraph("none");
  return `<ul>${items.map((item) => `<li>${escapeHtml(item.statement || item.source || JSON.stringify(item))}${item.impact ? `<br><span>${escapeHtml(item.impact)}</span>` : ""}${item.risk ? `<br><span>${escapeHtml(item.risk)}</span>` : ""}</li>`).join("")}</ul>`;
}

function relationSummary(edges) {
  if (!edges.length) return paragraph("no outbound edges");
  const counts = edges.reduce((acc, edge) => {
    acc[edge.relationType] = (acc[edge.relationType] || 0) + 1;
    return acc;
  }, {});
  return `<div class="tag-row">${Object.entries(counts).map(([type, count]) => tag(`${type}: ${count}`)).join("")}</div>`;
}

function tag(value) {
  return `<span class="tag">${escapeHtml(String(value))}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}
