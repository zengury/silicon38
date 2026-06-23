# Strategy Canvas iOS — API Contract for Mobile Client

**Version:** 1.0  
**Status:** Existing API — no new endpoints needed  
**Source:** Backend `main.py` (FastAPI routes + WebSocket)

---

## Design Rationale

The mobile client consumes the **same API** as the existing web client. No new endpoints, no modifications to request/response schemas. The API is already well-designed for thin-client consumption: all state lives on the server, the client sends user messages and receives structured responses.

**Key decision:** Zero backend changes. The mobile client is a drop-in consumer.

---

## API Endpoints

### REST Endpoints

#### GET /api/skills
List available strategy skills.

**Response:**
```json
{
  "counts": { "total": 30, "active": 28, "deprecated": 0, "pending": 2 },
  "skills": [
    {
      "skill_id": "porter-five-forces",
      "name": "Porter's Five Forces",
      "description": "Analyze industry competitive forces",
      "version": "1.0",
      "status": "active",
      "hit_count": 142,
      "quality_score": 0.92
    }
  ]
}
```

**Mobile usage:** Informational. Display in settings or about screen. Not required for normal operation.

---

#### GET /api/canvas
Get current canvas state (graph nodes + edges).

**Response:** `CanvasGraph` in vis-data format:
```json
{
  "nodes": [
    {
      "id": "abc123",
      "node_type": "goal",
      "label": "Market Leader",
      "content": "Become the market leader in climate tech",
      "confidence": 0.9,
      "weight": 2.0,
      "x": 80.0, "y": 30.0, "z": 0.0,
      "locked": false,
      "status": "active",
      "color": "#FFD700"
    }
  ],
  "links": [
    {
      "id": "edge_1",
      "edge_type": "supports",
      "source": "abc123",
      "target": "def456",
      "label": "",
      "strength": 0.8,
      "color": "#4CAF50"
    }
  ]
}
```

**Mobile usage:** Initial graph load when opening a project. Also used for polling (optional — primary updates come via WebSocket).

---

#### POST /api/canvas/lock/{node_id}
Lock a node (prevent AI from modifying it).

**Response:** `{"success": true}`

**Mobile usage:** Long-press a node → "Lock" option. Locked nodes appear with a lock icon in the node selector.

---

#### POST /api/canvas/unlock/{node_id}
Unlock a previously locked node.

**Response:** `{"success": true}`

**Mobile usage:** Long-press a locked node → "Unlock" option.

---

#### POST /api/reset
Reset the current session (clears context and canvas).

**Response:** `{"status": "reset"}`

**Mobile usage:** Confirmation alert → "Reset this session?" → clears local project state + calls backend reset.

---

### WebSocket Endpoint

#### WS /ws — Real-time Chat

**Connect:** `ws://<baseURL>/ws` or `wss://<baseURL>/ws`

**Message flow (client → server):**

```json
// Send chat message
{
  "type": "chat",
  "text": "I'm considering leaving my job to start a company."
}

// Lock a node
{
  "type": "lock_node",
  "node_id": "abc123"
}

// Unlock a node
{
  "type": "unlock_node",
  "node_id": "abc123"
}
```

**Message flow (server → client):**

```json
// Thinking indicator
{
  "type": "thinking",
  "text": "正在思考..."
}

// Full response
{
  "type": "response",
  "reply": "I hear you're at a crossroads...",
  "stage": "explore",
  "one_line_judgment": "The core tension is financial security vs. autonomy.",
  "confidence": 0.65,
  "invocations": [
    {
      "skill_id": "decision-fork-analysis",
      "reason": "User is facing a binary career decision",
      "version": "1.0"
    }
  ],
  "canvas": "{... full canvas JSON ...}",
  "canvas_diff": {
    "added": 3,
    "modified": 0,
    "invalidated": 0
  },
  "latency_ms": 2340,
  "turn_id": "t01a2b3"
}

// Node locked confirmation
{
  "type": "node_locked",
  "node_id": "abc123"
}

// Node unlocked confirmation
{
  "type": "node_unlocked",
  "node_id": "abc123"
}
```

**Mobile client processing order:**
1. Receive `"type": "thinking"` → show animated dots in chat
2. Receive `"type": "response"` → parse `reply` (display in chat), `stage`, `confidence`, `one_line_judgment` (update analysis), `canvas` (update graph), extract `golden_phrases` and `named_concepts` from canvas response
3. Update all ViewModels atomically

---

## Error Responses

All REST errors follow FastAPI default format:

```json
{
  "detail": "Error description"
}
```

**HTTP status codes:**
| Code | Meaning | Mobile action |
|------|---------|---------------|
| 200 | Success | — |
| 400 | Bad request (invalid stage name, etc.) | Show error in chat or alert |
| 422 | Validation error | Show field-level errors in settings |
| 500 | Server error | Retry with backoff, show "Coach is having trouble" |

**WebSocket errors:**
- Connection close with code 1006: network issue → auto-reconnect
- No structured error messages on WebSocket (server-side errors surface in chat as error replies)

---

## Data Types (Swift Models)

```swift
// ── REST Response Types ──────────────────────────

struct SkillsResponse: Codable {
    let counts: SkillCounts
    let skills: [SkillInfo]
}

struct SkillCounts: Codable {
    let total: Int
    let active: Int
    let deprecated: Int
    let pending: Int
}

struct SkillInfo: Codable {
    let skill_id: String
    let name: String
    let description: String
    let version: String
    let status: String
    let hit_count: Int
    let quality_score: Double
}

// ── Canvas Graph Types ───────────────────────────

struct CanvasGraph: Codable {
    let nodes: [CanvasNode]
    let links: [CanvasLink]
}

struct CanvasNode: Codable, Identifiable {
    let id: String
    let node_type: String
    let label: String
    let content: String?
    let confidence: Double
    let weight: Double
    let x: Double
    let y: Double
    let z: Double
    let locked: Bool
    let status: String
    let color: String
}

struct CanvasLink: Codable {
    let id: String?
    let edge_type: String
    let source: String      // node ID
    let target: String      // node ID
    let label: String?
    let strength: Double
    let color: String?
}

// ── WebSocket Message Types ──────────────────────

struct WSOutgoing: Encodable {
    let type: String
    var text: String?
    var node_id: String?
}

struct WSIncoming: Decodable {
    let type: String
    // "thinking"
    var text: String?
    // "response"
    var reply: String?
    var stage: String?
    var one_line_judgment: String?
    var confidence: Double?
    var invocations: [SkillInvocation]?
    var canvas: String?           // JSON string — parse separately
    var canvas_diff: CanvasDiff?
    var latency_ms: Int?
    var turn_id: String?
    // "node_locked" / "node_unlocked"
    var node_id: String?
}

struct SkillInvocation: Codable {
    let skill_id: String
    let reason: String?
    let version: String?
}

struct CanvasDiff: Codable {
    let added: Int
    let modified: Int
    let invalidated: Int
}
```

---

## API Usage Constraints for Mobile

1. **No polling.** The mobile client should NOT poll `/api/canvas`. Canvas state updates come through WebSocket responses. Only fetch canvas on initial project load (optional — could also use cached state from last session).

2. **WebSocket is the primary channel.** All real-time interaction (chat, node locking, state updates) flows through WebSocket. REST endpoints are supplementary.

3. **One connection per session.** Do not open multiple WebSocket connections. If the app goes to background, close the connection and reopen on foreground.

4. **Message ordering.** The server processes messages sequentially. Do not send a new chat message before receiving the response for the previous one. Queue if needed.

5. **Connection timeout.** If no response within 15 seconds, show a timeout error and offer retry.

6. **API key via header.** The DeepSeek API key is configured on the backend, not sent by the mobile client. The mobile client only needs the backend URL.

---

## Breaking Change Assessment

**No breaking changes.** The mobile client is a new consumer of the existing API. All endpoints, message formats, and data types are identical to the web client.

**Future considerations:**
- If the backend adds authentication (beyond the existing API key-in-backend model), the mobile client would need token-based auth.
- If the WebSocket protocol changes (e.g., message format), both web and mobile clients must update simultaneously.
