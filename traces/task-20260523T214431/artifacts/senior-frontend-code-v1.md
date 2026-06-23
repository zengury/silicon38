# Strategic Canvas iOS — Implementation

**Module:** senior-frontend  
**Constraint:** ui-design-system (hard), apple-hig-expert (soft)  
**Source of truth:** architect-adr-v1.md, ui-design-system-design-v1.md  

---

## File Inventory

All files under `StrategyCanvas/` Xcode project:

```
StrategyCanvas/
├── App/
│   ├── StrategyCanvasApp.swift      ← Entry point
│   ├── TabNavigation.swift          ← Root TabView
│   └── OnboardingView.swift         ← First-launch config
├── BackendClient/
│   ├── BackendClient.swift          ← REST + WebSocket facade
│   ├── RESTClient.swift             ← URLSession REST calls
│   ├── WebSocketClient.swift        ← URLSessionWebSocketTask wrapper
│   └── Models/
│       ├── APIResponse.swift        ← All API DTOs
│       └── GraphData.swift          ← CanvasGraph types
├── Chat/
│   ├── ChatViewModel.swift          ← Conversation state
│   └── ChatScreen.swift             ← SwiftUI chat UI
├── Graph/
│   ├── GraphViewModel.swift         ← 3D graph data
│   └── GraphScreen.swift            ← SceneKit wrapper
│       └── SceneKitGraphView.swift  ← UIViewRepresentable
├── Analysis/
│   ├── AnalysisViewModel.swift      ← Summary state
│   ├── AnalysisScreen.swift         ← SwiftUI analysis UI
│   └── StrategyHouseRenderer.swift  ← Core Graphics PNG gen
├── Projects/
│   ├── ProjectStore.swift           ← CRUD + persistence
│   └── ProjectSidebar.swift         ← Project list sheet
├── Settings/
│   ├── SettingsStore.swift          ← URL/API key/model
│   ├── KeychainManager.swift        ← Keychain wrapper
│   └── SettingsScreen.swift         ← Settings UI
├── DesignSystem/
│   └── DesignTokens.swift           ← Color/type/spacing constants
├── Models/
│   └── ProjectModels.swift          ← Domain models (Codable)
└── Assets.xcassets/                 ← AppIcon, AccentColor
```

---

## 1. App Entry Point

```swift
// StrategyCanvasApp.swift
import SwiftUI

@main
struct StrategyCanvasApp: App {
    @StateObject private var settingsStore = SettingsStore()
    @StateObject private var projectStore = ProjectStore()
    
    var body: some Scene {
        WindowGroup {
            if settingsStore.isConfigured {
                TabNavigation(
                    settingsStore: settingsStore,
                    projectStore: projectStore
                )
            } else {
                OnboardingView(settingsStore: settingsStore)
            }
        }
    }
}
```

---

## 2. TabNavigation

```swift
// TabNavigation.swift
import SwiftUI

struct TabNavigation: View {
    @ObservedObject var settingsStore: SettingsStore
    @ObservedObject var projectStore: ProjectStore
    @StateObject private var chatVM: ChatViewModel
    @StateObject private var graphVM: GraphViewModel
    @StateObject private var analysisVM: AnalysisViewModel
    
    init(settingsStore: SettingsStore, projectStore: ProjectStore) {
        self.settingsStore = settingsStore
        self.projectStore = projectStore
        let backend = BackendClient(
            baseURL: settingsStore.backendURL,
            apiKey: settingsStore.apiKey
        )
        _chatVM = StateObject(wrappedValue: ChatViewModel(
            backendClient: backend,
            projectStore: projectStore
        ))
        _graphVM = StateObject(wrappedValue: GraphViewModel(
            projectStore: projectStore
        ))
        _analysisVM = StateObject(wrappedValue: AnalysisViewModel(
            projectStore: projectStore
        ))
    }
    
    var body: some View {
        TabView {
            ChatScreen(chatVM: chatVM, projectStore: projectStore)
                .tabItem {
                    Label("Chat", systemImage: "bubble.left.and.bubble.right")
                }
                .accessibilityLabel("Chat, tab 1 of 3")
            
            GraphScreen(graphVM: graphVM)
                .tabItem {
                    Label("Graph", systemImage: "point.3.connected.trianglepath.dotted")
                }
                .accessibilityLabel("Graph, tab 2 of 3")
            
            AnalysisScreen(analysisVM: analysisVM, graphVM: graphVM)
                .tabItem {
                    Label("Analysis", systemImage: "chart.bar.doc.horizontal")
                }
                .accessibilityLabel("Analysis, tab 3 of 3")
        }
    }
}
```

---

## 3. BackendClient

```swift
// BackendClient.swift
import Foundation

actor BackendClient {
    let restClient: RESTClient
    let wsClient: WebSocketClient
    
    init(baseURL: String, apiKey: String) {
        self.restClient = RESTClient(baseURL: baseURL, apiKey: apiKey)
        self.wsClient = WebSocketClient(baseURL: baseURL)
    }
    
    // ── REST ─────────────────────────
    
    func fetchSkills() async throws -> SkillsResponse {
        try await restClient.get("/api/skills")
    }
    
    func fetchCanvas() async throws -> CanvasGraph {
        try await restClient.get("/api/canvas")
    }
    
    func lockNode(_ nodeId: String) async throws -> Bool {
        struct Response: Decodable { let success: Bool }
        let res: Response = try await restClient.post("/api/canvas/lock/\(nodeId)")
        return res.success
    }
    
    func unlockNode(_ nodeId: String) async throws -> Bool {
        struct Response: Decodable { let success: Bool }
        let res: Response = try await restClient.post("/api/canvas/unlock/\(nodeId)")
        return res.success
    }
    
    func resetSession() async throws {
        try await restClient.post("/api/reset")
    }
    
    // ── WebSocket ────────────────────
    
    func connect() {
        wsClient.connect()
    }
    
    func disconnect() {
        wsClient.disconnect()
    }
    
    func sendChat(_ text: String) {
        let msg = WSOutgoing(type: "chat", text: text, node_id: nil)
        wsClient.send(msg)
    }
    
    func sendLockNode(_ nodeId: String) {
        let msg = WSOutgoing(type: "lock_node", text: nil, node_id: nodeId)
        wsClient.send(msg)
    }
    
    func sendUnlockNode(_ nodeId: String) {
        let msg = WSOutgoing(type: "unlock_node", text: nil, node_id: nodeId)
        wsClient.send(msg)
    }
    
    func messages() -> AsyncStream<WSIncoming> {
        wsClient.messages
    }
}
```

```swift
// RESTClient.swift
import Foundation

final class RESTClient {
    private let baseURL: String
    private let apiKey: String
    private let session: URLSession
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()
    
    init(baseURL: String, apiKey: String) {
        self.baseURL = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL
        self.apiKey = apiKey
        self.session = URLSession(configuration: .default)
    }
    
    enum ClientError: Error {
        case invalidURL
        case httpError(Int)
        case decodingError(Error)
        case networkError(Error)
    }
    
    func get<T: Decodable>(_ path: String) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw ClientError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw ClientError.httpError((response as? HTTPURLResponse)?.statusCode ?? 0)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw ClientError.decodingError(error)
        }
    }
    
    func post<T: Decodable>(_ path: String, body: (any Encodable)? = nil) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(path)") else {
            throw ClientError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body = body {
            request.httpBody = try encoder.encode(AnyEncodable(body))
        }
        
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw ClientError.httpError((response as? HTTPURLResponse)?.statusCode ?? 0)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw ClientError.decodingError(error)
        }
    }
}

private struct AnyEncodable: Encodable {
    let value: any Encodable
    init(_ value: any Encodable) { self.value = value }
    func encode(to encoder: Encoder) throws { try value.encode(to: encoder) }
}
```

```swift
// WebSocketClient.swift
import Foundation

final class WebSocketClient {
    private let baseURL: String
    private var task: URLSessionWebSocketTask?
    private var reconnectTask: Task<Void, Never>?
    private var backoff: TimeInterval = 1
    private let maxBackoff: TimeInterval = 30
    
    let messages: AsyncStream<WSIncoming>
    private let messageContinuation: AsyncStream<WSIncoming>.Continuation
    
    init(baseURL: String) {
        let cleanURL = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL
        let wsProtocol = cleanURL.hasPrefix("https") ? "wss" : "ws"
        let host = cleanURL.replacingOccurrences(of: "https://", with: "")
                         .replacingOccurrences(of: "http://", with: "")
        self.baseURL = "\(wsProtocol)://\(host)"
        
        var continuation: AsyncStream<WSIncoming>.Continuation!
        self.messages = AsyncStream { continuation = $0 }
        self.messageContinuation = continuation
    }
    
    func connect() {
        guard let url = URL(string: "\(baseURL)/ws") else { return }
        task = URLSession.shared.webSocketTask(with: url)
        task?.resume()
        backoff = 1
        receive()
    }
    
    func disconnect() {
        reconnectTask?.cancel()
        reconnectTask = nil
        task?.cancel(with: .normalClosure, reason: nil)
        task = nil
    }
    
    func send(_ message: WSOutgoing) {
        guard let data = try? JSONEncoder().encode(message),
              let json = String(data: data, encoding: .utf8) else { return }
        task?.send(.string(json)) { error in
            if let error = error {
                print("[WS] Send error: \(error)")
            }
        }
    }
    
    private func receive() {
        task?.receive { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    if let data = text.data(using: .utf8),
                       let incoming = try? JSONDecoder().decode(WSIncoming.self, from: data) {
                        self.messageContinuation.yield(incoming)
                    }
                case .data(let data):
                    if let incoming = try? JSONDecoder().decode(WSIncoming.self, from: data) {
                        self.messageContinuation.yield(incoming)
                    }
                @unknown default: break
                }
                self.receive() // continue listening
                
            case .failure:
                self.scheduleReconnect()
            }
        }
    }
    
    private func scheduleReconnect() {
        reconnectTask?.cancel()
        reconnectTask = Task { [weak self] in
            guard let self = self else { return }
            let jitter = TimeInterval.random(in: 0.75...1.25)
            try? await Task.sleep(nanoseconds: UInt64(self.backoff * jitter * 1_000_000_000))
            guard !Task.isCancelled else { return }
            self.connect()
            self.backoff = min(self.backoff * 2, self.maxBackoff)
        }
    }
}

struct WSOutgoing: Encodable {
    let type: String
    let text: String?
    let node_id: String?
}

struct WSIncoming: Decodable {
    let type: String
    var text: String?
    var reply: String?
    var stage: String?
    var one_line_judgment: String?
    var confidence: Double?
    var invocations: [SkillInvocationDTO]?
    var canvas: String?
    var canvas_diff: CanvasDiffDTO?
    var latency_ms: Int?
    var turn_id: String?
    var golden_phrases: [String]?
    var named_concepts: [String]?
    var node_id: String?
}

struct SkillInvocationDTO: Decodable {
    let skill_id: String
    let reason: String?
    let version: String?
}

struct CanvasDiffDTO: Decodable {
    let added: Int
    let modified: Int
    let invalidated: Int
}
```

---

## 4. ChatViewModel + ChatScreen

```swift
// ChatViewModel.swift
import SwiftUI

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isThinking = false
    @Published var connectionState: ConnectionState = .disconnected
    @Published var error: ChatError? = nil
    
    private let backendClient: BackendClient
    private let projectStore: ProjectStore
    
    enum ConnectionState {
        case connected, disconnected, reconnecting
    }
    
    struct ChatError: Identifiable {
        let id = UUID()
        let message: String
        let retryAction: (() -> Void)?
    }
    
    init(backendClient: BackendClient, projectStore: ProjectStore) {
        self.backendClient = backendClient
        self.projectStore = projectStore
        loadProjectMessages()
    }
    
    func connect() async {
        await backendClient.connect()
        startListening()
    }
    
    func send(_ text: String) {
        guard !isThinking else { return }
        let userMsg = ChatMessage(speaker: .user, text: text)
        messages.append(userMsg)
        projectStore.addMessage(userMsg, toActiveProject: true)
        
        isThinking = true
        Task {
            await backendClient.sendChat(text)
        }
    }
    
    private func startListening() {
        Task {
            for await msg in await backendClient.messages() {
                await handleIncoming(msg)
            }
        }
    }
    
    private func handleIncoming(_ msg: WSIncoming) async {
        switch msg.type {
        case "thinking":
            isThinking = true
        case "response":
            isThinking = false
            
            let coachMsg = ChatMessage(
                speaker: .assistant,
                text: msg.reply ?? "",
                invocations: msg.invocations,
                latencyMs: msg.latency_ms
            )
            messages.append(coachMsg)
            projectStore.addMessage(coachMsg, toActiveProject: true)
            
            // Update project state
            projectStore.updateActiveProject { project in
                if let stage = msg.stage { project.stage = stage }
                if let confidence = msg.confidence { project.confidence = confidence }
                if let judgment = msg.one_line_judgment { project.judgment = judgment }
                if let phrases = msg.golden_phrases, !phrases.isEmpty {
                    project.goldenPhrases = phrases
                }
                if let concepts = msg.named_concepts, !concepts.isEmpty {
                    project.namedConcepts = concepts
                }
                // Parse canvas state
                if let canvasStr = msg.canvas,
                   let canvasData = canvasStr.data(using: .utf8),
                   let graph = try? JSONDecoder().decode(CanvasGraph.self, from: canvasData) {
                    project.graphData.nodes = graph.nodes
                    project.graphData.links = graph.links
                }
            }
            
        case "node_locked", "node_unlocked":
            await refreshCanvas()
            
        default:
            break
        }
    }
    
    private func refreshCanvas() async {
        if let graph: CanvasGraph = try? await backendClient.fetchCanvas() {
            projectStore.updateActiveProject { project in
                project.graphData.nodes = graph.nodes
                project.graphData.links = graph.links
            }
        }
    }
    
    private func loadProjectMessages() {
        if let project = projectStore.activeProject {
            messages = project.messages
        }
    }
}

struct ChatMessage: Identifiable, Codable {
    let id = UUID()
    let speaker: Speaker
    let text: String
    var invocations: [SkillInvocationDTO]? = nil
    var latencyMs: Int? = nil
    
    enum Speaker: String, Codable {
        case user, assistant
    }
}
```

```swift
// ChatScreen.swift
import SwiftUI

struct ChatScreen: View {
    @ObservedObject var chatVM: ChatViewModel
    @ObservedObject var projectStore: ProjectStore
    @State private var inputText = ""
    @State private var showProjects = false
    @State private var showSettings = false
    @FocusState private var isInputFocused: Bool
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: DesignTokens.spacing.sm) {
                            if chatVM.messages.isEmpty {
                                emptyStateView
                            }
                            ForEach(chatVM.messages) { msg in
                                ChatBubble(message: msg)
                                    .id(msg.id)
                            }
                            if chatVM.isThinking {
                                ThinkingIndicator()
                                    .id("thinking")
                            }
                        }
                        .padding(.horizontal, DesignTokens.spacing.lg)
                        .padding(.vertical, DesignTokens.spacing.md)
                    }
                    .onChange(of: chatVM.messages.count) { _ in
                        withAnimation { proxy.scrollTo(chatVM.messages.last?.id ?? "thinking") }
                    }
                    .onChange(of: chatVM.isThinking) { _ in
                        withAnimation { proxy.scrollTo("thinking") }
                    }
                }
                .scrollDismissesKeyboard(.interactively)
                
                // Input bar
                inputBar
            }
            .navigationTitle(projectStore.activeProject?.name ?? "Strategy Canvas")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { showProjects = true } label: {
                        Image(systemName: "folder")
                    }
                    .accessibilityLabel("Projects")
                }
                ToolbarItem(placement: .topBarTrailing) {
                    HStack(spacing: 12) {
                        ConnectionDot(state: chatVM.connectionState)
                        Button { showSettings = true } label: {
                            Image(systemName: "gearshape")
                        }
                        .accessibilityLabel("Settings")
                    }
                }
            }
            .sheet(isPresented: $showProjects) {
                ProjectSidebar(projectStore: projectStore, onSelect: { chatVM.messages = $0.messages })
            }
            .sheet(isPresented: $showSettings) {
                SettingsScreen()
            }
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Text("🏛️")
                .font(.system(size: 48))
            Text("Start a conversation about the decision you're facing...")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 80)
    }
    
    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: DesignTokens.spacing.sm) {
            TextField("Describe your strategic decision...", text: $inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(.ultraThinMaterial)
                .cornerRadius(DesignTokens.radius.chatBubble)
                .focused($isInputFocused)
                .lineLimit(1...4)
                .accessibilityLabel("Message input")
                .accessibilityHint("Type your strategic question, then tap Send")
            
            Button {
                let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
                guard !text.isEmpty else { return }
                chatVM.send(text)
                inputText = ""
                Haptics.medium()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || chatVM.isThinking)
            .accessibilityLabel("Send message")
            .frame(minWidth: 44, minHeight: 44)
        }
        .padding(.horizontal, DesignTokens.spacing.md)
        .padding(.vertical, DesignTokens.spacing.sm)
        .background(.bar)
    }
}

// ── Sub-components ──────────────────────────────

struct ChatBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.speaker == .user { Spacer(minLength: 48) }
            
            VStack(alignment: message.speaker == .user ? .trailing : .leading, spacing: 4) {
                Text(message.text)
                    .font(.body)
                    .foregroundStyle(message.speaker == .user ? .white : .primary)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(message.speaker == .user ? Color.accentColor : Color(.systemGray5))
                    .cornerRadius(DesignTokens.radius.chatBubble)
                
                if let ms = message.latencyMs {
                    Text("\(ms)ms")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
            
            if message.speaker == .assistant { Spacer(minLength: 48) }
        }
        .accessibilityLabel("\(message.speaker == .user ? "You" : "Coach"): \(message.text)")
    }
}

struct ThinkingIndicator: View {
    @State private var animating = false
    
    var body: some View {
        HStack {
            HStack(spacing: 4) {
                ForEach(0..<3) { i in
                    Circle()
                        .fill(Color(.systemGray3))
                        .frame(width: 8, height: 8)
                        .scaleEffect(animating ? 1.0 : 0.5)
                        .animation(
                            .spring(response: 0.3, dampingFraction: 0.5)
                            .repeatForever()
                            .delay(Double(i) * 0.15),
                            value: animating
                        )
                }
            }
            .padding(12)
            .background(Color(.systemGray5))
            .cornerRadius(DesignTokens.radius.chatBubble)
            Spacer()
        }
        .onAppear { animating = true }
    }
}

struct ConnectionDot: View {
    let state: ChatViewModel.ConnectionState
    
    var body: some View {
        Circle()
            .fill(color)
            .frame(width: 8, height: 8)
            .accessibilityLabel(stateText)
    }
    
    var color: Color {
        switch state {
        case .connected: .green
        case .disconnected: .red
        case .reconnecting: .yellow
        }
    }
    
    var stateText: String {
        switch state {
        case .connected: "Connected"
        case .disconnected: "Disconnected"
        case .reconnecting: "Reconnecting"
        }
    }
}
```

---

## 5. GraphViewModel + GraphScreen

```swift
// GraphViewModel.swift
import SwiftUI

@MainActor
final class GraphViewModel: ObservableObject {
    @Published var nodes: [CanvasNode] = []
    @Published var links: [CanvasLink] = []
    @Published var selectedNodeId: String? = nil
    @Published var filteredType: String? = nil
    
    private let projectStore: ProjectStore
    
    init(projectStore: ProjectStore) {
        self.projectStore = projectStore
        loadGraph()
    }
    
    func loadGraph() {
        guard let project = projectStore.activeProject else { return }
        nodes = project.graphData.nodes
        links = project.graphData.links
    }
    
    var filteredNodes: [CanvasNode] {
        guard let type = filteredType else { return nodes }
        return nodes.filter { $0.node_type == type }
    }
    
    var nodeTypeCounts: [(type: String, color: String, count: Int)] {
        let grouped = Dictionary(grouping: nodes, by: \.node_type)
        return grouped.map { type, nodes in
            (type: type, color: nodes.first?.color ?? "#999", count: nodes.count)
        }
    }
}
```

```swift
// GraphScreen.swift
import SwiftUI

struct GraphScreen: View {
    @ObservedObject var graphVM: GraphViewModel
    
    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                if graphVM.nodes.isEmpty {
                    emptyState
                } else {
                    SceneKitGraphView(
                        nodes: graphVM.filteredNodes,
                        links: graphVM.links,
                        selectedNodeId: $graphVM.selectedNodeId
                    )
                    .edgesIgnoringSafeArea([.top, .horizontal])
                }
                
                // Legend
                if !graphVM.nodes.isEmpty {
                    legendBar
                }
            }
            .navigationTitle("Node Graph")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Text("\(graphVM.nodes.count) nodes / \(graphVM.links.count) edges")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
    
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "point.3.connected.trianglepath.dotted")
                .font(.system(size: 48))
                .foregroundStyle(.tertiary)
            Text("Nodes will appear here as the conversation progresses...")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }
    
    private var legendBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(graphVM.nodeTypeCounts, id: \.type) { item in
                    Button {
                        withAnimation {
                            graphVM.filteredType = graphVM.filteredType == item.type ? nil : item.type
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(Color(hex: item.color))
                                .frame(width: 8, height: 8)
                            Text(nodeTypeLabel(item.type))
                                .font(.caption2)
                            Text("\(item.count)")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(
                            graphVM.filteredType == item.type
                                ? Color.accentColor.opacity(0.15)
                                : Color(.systemGray6)
                        )
                        .cornerRadius(DesignTokens.radius.pill)
                    }
                }
            }
            .padding(.horizontal, DesignTokens.spacing.md)
        }
        .padding(.bottom, 8)
    }
}

func nodeTypeLabel(_ type: String) -> String {
    [
        "goal": "目标", "position": "定位", "option": "选项",
        "mechanism": "机制", "resource": "资源", "constraint": "约束",
        "evidence": "证据", "tension": "张力", "assumption": "假设",
        "risk": "风险", "signal": "信号", "action": "行动",
        "pattern": "模式", "stakeholder": "利益方"
    ][type] ?? type
}
```

```swift
// SceneKitGraphView.swift
import SwiftUI
import SceneKit

struct SceneKitGraphView: UIViewRepresentable {
    let nodes: [CanvasNode]
    let links: [CanvasLink]
    @Binding var selectedNodeId: String?
    
    func makeUIView(context: Context) -> SCNView {
        let scnView = SCNView()
        scnView.scene = context.coordinator.buildScene(nodes: nodes, links: links)
        scnView.allowsCameraControl = true
        scnView.autoenablesDefaultLighting = true
        scnView.backgroundColor = UIColor.clear
        scnView.antialiasingMode = .multisampling4X
        
        let tap = UITapGestureRecognizer(
            target: context.coordinator,
            action: #selector(Coordinator.handleTap(_:))
        )
        scnView.addGestureRecognizer(tap)
        
        return scnView
    }
    
    func updateUIView(_ uiView: SCNView, context: Context) {
        uiView.scene = context.coordinator.buildScene(nodes: nodes, links: links)
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject {
        let parent: SceneKitGraphView
        
        init(_ parent: SceneKitGraphView) { self.parent = parent }
        
        func buildScene(nodes: [CanvasNode], links: [CanvasLink]) -> SCNScene {
            let scene = SCNScene()
            
            let cameraNode = SCNNode()
            cameraNode.camera = SCNCamera()
            cameraNode.position = SCNVector3(0, 0, 250)
            scene.rootNode.addChildNode(cameraNode)
            
            let ambientLight = SCNNode()
            ambientLight.light = SCNLight()
            ambientLight.light!.type = .ambient
            ambientLight.light!.color = UIColor(white: 0.6, alpha: 1.0)
            scene.rootNode.addChildNode(ambientLight)
            
            // Build node map for edge resolution
            var nodeMap: [String: CanvasNode] = [:]
            
            // Create sphere nodes
            for node in nodes {
                nodeMap[node.id] = node
                let sphere = SCNNode()
                let radius = CGFloat(max(0.5, min(1.5, Double(node.weight) * 0.6)))
                sphere.geometry = SCNSphere(radius: radius)
                
                let color = UIColor(hex: node.color) ?? .gray
                let emissiveIntensity: CGFloat = node.locked ? 0.3 : CGFloat(node.confidence * 0.55)
                sphere.geometry?.firstMaterial?.diffuse.contents = color
                sphere.geometry?.firstMaterial?.emission.contents = color
                sphere.geometry?.firstMaterial?.emission.intensity = emissiveIntensity
                
                sphere.position = SCNVector3(CGFloat(node.x), CGFloat(node.y), CGFloat(node.z))
                sphere.name = node.id
                
                // Hit target expansion: transparent plane for 44pt minimum
                let hitPlane = SCNNode()
                hitPlane.geometry = SCNPlane(width: 44, height: 44)
                hitPlane.geometry?.firstMaterial?.diffuse.contents = UIColor.clear
                hitPlane.geometry?.firstMaterial?.isDoubleSided = true
                hitPlane.constraints = [SCNBillboardConstraint()]
                sphere.addChildNode(hitPlane)
                
                scene.rootNode.addChildNode(sphere)
            }
            
            // Create edge cylinders
            for link in links {
                guard let sourceNode = nodeMap[link.source],
                      let targetNode = nodeMap[link.target] else { continue }
                
                let edge = SCNNode()
                let sourcePos = SCNVector3(CGFloat(sourceNode.x), CGFloat(sourceNode.y), CGFloat(sourceNode.z))
                let targetPos = SCNVector3(CGFloat(targetNode.x), CGFloat(targetNode.y), CGFloat(targetNode.z))
                
                let midX = (sourcePos.x + targetPos.x) / 2
                let midY = (sourcePos.y + targetPos.y) / 2
                let midZ = (sourcePos.z + targetPos.z) / 2
                
                let dx = targetPos.x - sourcePos.x
                let dy = targetPos.y - sourcePos.y
                let dz = targetPos.z - sourcePos.z
                let distance = sqrt(dx*dx + dy*dy + dz*dz)
                
                edge.geometry = SCNCylinder(radius: 0.15, height: CGFloat(distance))
                edge.position = SCNVector3(midX, midY, midZ)
                edge.geometry?.firstMaterial?.diffuse.contents = UIColor.gray.withAlphaComponent(0.3)
                
                scene.rootNode.addChildNode(edge)
            }
            
            return scene
        }
        
        @objc func handleTap(_ gesture: UITapGestureRecognizer) {
            guard let scnView = gesture.view as? SCNView else { return }
            let point = gesture.location(in: scnView)
            let hits = scnView.hitTest(point, options: [
                .searchMode: SCNHitTestSearchMode.all.rawValue
            ])
            
            // Find first sphere node (skip hit planes and edges)
            for hit in hits {
                if let name = hit.node.name ?? hit.node.parent?.name,
                   !name.isEmpty {
                    parent.selectedNodeId = name
                    Haptics.light()
                    
                    // Fly camera to node
                    if let node = hit.node.parent ?? hit.node,
                       node.position.x != 0 || node.position.y != 0 || node.position.z != 0 {
                        SCNTransaction.begin()
                        SCNTransaction.animationDuration = 1.0
                        scnView.pointOfView?.position = SCNVector3(
                            node.position.x,
                            node.position.y,
                            node.position.z + 120
                        )
                        SCNTransaction.commit()
                    }
                    break
                }
            }
        }
    }
}

// ── UIColor hex extension ──────────────────────

extension UIColor {
    convenience init?(hex: String) {
        let r, g, b: CGFloat
        var hexSanitized = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        if hexSanitized.hasPrefix("#") { hexSanitized.removeFirst() }
        guard hexSanitized.count == 6 else { return nil }
        var rgb: UInt64 = 0
        guard Scanner(string: hexSanitized).scanHexInt64(&rgb) else { return nil }
        r = CGFloat((rgb & 0xFF0000) >> 16) / 255.0
        g = CGFloat((rgb & 0x00FF00) >> 8) / 255.0
        b = CGFloat(rgb & 0x0000FF) / 255.0
        self.init(red: r, green: g, blue: b, alpha: 1.0)
    }
}

extension Color {
    init(hex: String) {
        if let uiColor = UIColor(hex: hex) {
            self.init(uiColor: uiColor)
        } else {
            self.init(.gray)
        }
    }
}
```

---

## 6. AnalysisViewModel + AnalysisScreen + StrategyHouseRenderer

```swift
// AnalysisViewModel.swift
import SwiftUI

@MainActor
final class AnalysisViewModel: ObservableObject {
    @Published var stage: String = "explore"
    @Published var confidence: Double = 0.0
    @Published var judgment: String = ""
    @Published var goldenPhrases: [String] = []
    @Published var namedConcepts: [String] = []
    @Published var houseImage: UIImage? = nil
    @Published var isGenerating = false
    
    private let projectStore: ProjectStore
    
    init(projectStore: ProjectStore) {
        self.projectStore = projectStore
        loadFromProject()
    }
    
    func loadFromProject() {
        guard let project = projectStore.activeProject else { return }
        stage = project.stage
        confidence = project.confidence
        judgment = project.judgment
        goldenPhrases = project.goldenPhrases
        namedConcepts = project.namedConcepts
    }
    
    func generateHouse() {
        guard let project = projectStore.activeProject else { return }
        isGenerating = true
        Task.detached(priority: .userInitiated) {
            let image = StrategyHouseRenderer.render(nodes: project.graphData.nodes)
            await MainActor.run {
                self.houseImage = image
                self.isGenerating = false
                Haptics.success()
            }
        }
    }
}
```

```swift
// AnalysisScreen.swift
import SwiftUI

struct AnalysisScreen: View {
    @ObservedObject var analysisVM: AnalysisViewModel
    @ObservedObject var graphVM: GraphViewModel
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignTokens.spacing.lg) {
                    // Stage + Confidence
                    stageConfidenceCard
                    
                    // Judgment
                    if !analysisVM.judgment.isEmpty {
                        judgmentCard
                    }
                    
                    // Golden Phrases
                    if !analysisVM.goldenPhrases.isEmpty {
                        goldenPhrasesCard
                    }
                    
                    // Named Concepts
                    if !analysisVM.namedConcepts.isEmpty {
                        namedConceptsCard
                    }
                    
                    // Node Selector
                    if !graphVM.nodes.isEmpty {
                        nodeSelectorCard
                    }
                    
                    // Strategy House
                    strategyHouseCard
                }
                .padding(DesignTokens.spacing.lg)
            }
            .navigationTitle("Analysis")
            .onAppear {
                analysisVM.loadFromProject()
                graphVM.loadGraph()
            }
        }
    }
    
    private var stageConfidenceCard: some View {
        VStack(spacing: DesignTokens.spacing.sm) {
            HStack {
                Text("Stage / 阶段")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Spacer()
                StageBadge(stage: analysisVM.stage)
            }
            
            HStack {
                Text("Confidence")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("\(Int(analysisVM.confidence * 100))%")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            ConfidenceBar(confidence: analysisVM.confidence)
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
    
    private var judgmentCard: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacing.sm) {
            Text("Judgment / 判断")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(analysisVM.judgment)
                .font(.body)
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
    
    private var goldenPhrasesCard: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacing.sm) {
            Text("Golden Phrases / 金句")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            ForEach(analysisVM.goldenPhrases, id: \.self) { phrase in
                Text(""\(phrase)"")
                    .font(.title3)
                    .italic()
                    .padding(.leading, 12)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(Color(hex: "#FFD700"))
                            .frame(width: 3)
                    }
            }
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
    
    private var namedConceptsCard: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacing.sm) {
            Text("Named Concepts / 命名概念")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            FlowLayout(spacing: 8) {
                ForEach(analysisVM.namedConcepts, id: \.self) { concept in
                    Text(concept)
                        .font(.caption)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(Color.accentColor.opacity(0.1))
                        .cornerRadius(DesignTokens.radius.sm)
                }
            }
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
    
    private var nodeSelectorCard: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacing.sm) {
            Text("Select Nodes / 选择节点")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            ForEach(graphVM.nodeTypeCounts, id: \.type) { item in
                DisclosureGroup {
                    ForEach(graphVM.filteredNodes.filter { $0.node_type == item.type }) { node in
                        HStack {
                            Circle()
                                .fill(Color(hex: node.color))
                                .frame(width: 8, height: 8)
                            Text(node.label)
                                .font(.caption)
                            Spacer()
                            Text("\(Int(node.confidence * 100))%")
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                        }
                        .padding(.vertical, 2)
                    }
                } label: {
                    HStack {
                        Circle()
                            .fill(Color(hex: item.color))
                            .frame(width: 8, height: 8)
                        Text(nodeTypeLabel(item.type))
                            .font(.caption)
                        Text("\(item.count)")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
    
    private var strategyHouseCard: some View {
        VStack(spacing: DesignTokens.spacing.md) {
            Text("Strategy House / 战略屋")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            if let image = analysisVM.houseImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .cornerRadius(DesignTokens.radius.sm)
                
                HStack {
                    Button {
                        analysisVM.generateHouse()
                    } label: {
                        Label("Regenerate", systemImage: "arrow.clockwise")
                    }
                    
                    Spacer()
                    
                    ShareLink(item: Image(uiImage: image), preview: SharePreview("Strategy House", image: Image(uiImage: image))) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                }
                .font(.caption)
            } else {
                VStack(spacing: DesignTokens.spacing.md) {
                    Image(systemName: "building.columns")
                        .font(.system(size: 36))
                        .foregroundStyle(.tertiary)
                    
                    if analysisVM.isGenerating {
                        ProgressView("Generating...")
                    } else {
                        Text("Complete your strategic conversation, then generate a Strategy House diagram.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                        
                        Button {
                            analysisVM.generateHouse()
                        } label: {
                            Label("Generate Strategy / 生成战略", systemImage: "wand.and.stars")
                                .padding(.horizontal, 20)
                                .padding(.vertical, 12)
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(graphVM.nodes.isEmpty)
                    }
                }
                .padding(.vertical, 24)
            }
        }
        .padding(DesignTokens.spacing.lg)
        .background(.regularMaterial)
        .cornerRadius(DesignTokens.radius.md)
    }
}

struct StageBadge: View {
    let stage: String
    
    var label: String {
        switch stage {
        case "explore": "Explore / 探索"
        case "converge": "Converge / 收敛"
        case "stress_test": "Stress Test / 压力测试"
        case "commit": "Commit / 决策"
        case "review": "Review / 回顾"
        default: stage
        }
    }
    
    var color: Color {
        switch stage {
        case "explore": .blue
        case "converge": .teal
        case "stress_test": .orange
        case "commit": .green
        case "review": .purple
        default: .gray
        }
    }
    
    var body: some View {
        Text(label)
            .font(.subheadline.weight(.medium))
            .foregroundStyle(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 4)
            .background(color)
            .cornerRadius(DesignTokens.radius.pill)
            .accessibilityLabel(label)
    }
}

struct ConfidenceBar: View {
    let confidence: Double
    
    var color: Color {
        if confidence < 0.3 { return .red }
        if confidence < 0.7 { return .orange }
        return .green
    }
    
    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color(.systemGray5))
                    .frame(height: 8)
                RoundedRectangle(cornerRadius: 4)
                    .fill(color)
                    .frame(width: geo.size.width * CGFloat(confidence), height: 8)
                    .animation(.spring(response: 0.3), value: confidence)
            }
        }
        .frame(height: 8)
        .accessibilityLabel("Confidence \(Int(confidence * 100)) percent")
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrange(proposal: proposal, subviews: subviews)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrange(proposal: proposal, subviews: subviews)
        for (index, frame) in result.frames.enumerated() {
            subviews[index].place(at: CGPoint(x: bounds.minX + frame.minX, y: bounds.minY + frame.minY), proposal: .unspecified)
        }
    }
    
    private func arrange(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, frames: [CGRect]) {
        let maxWidth = proposal.width ?? .infinity
        var x: CGFloat = 0, y: CGFloat = 0, rowHeight: CGFloat = 0
        var frames: [CGRect] = []
        
        for view in subviews {
            let size = view.sizeThatFits(.unspecified)
            if x + size.width > maxWidth, x > 0 {
                x = 0; y += rowHeight + spacing; rowHeight = 0
            }
            frames.append(CGRect(x: x, y: y, width: size.width, height: size.height))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        
        return (CGSize(width: maxWidth, height: y + rowHeight), frames)
    }
}
```

```swift
// StrategyHouseRenderer.swift
import UIKit

enum StrategyHouseRenderer {
    
    static func render(nodes: [CanvasNode]) -> UIImage {
        let dpr = UIScreen.main.scale
        let W: CGFloat = 600
        let H: CGFloat = 1200
        let format = UIGraphicsImageRendererFormat()
        format.scale = dpr
        format.opaque = false
        
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: W, height: H), format: format)
        
        return renderer.image { ctx in
            let context = ctx.cgContext
            let pad: CGFloat = 24
            let contentW = W - pad * 2
            var y: CGFloat = pad
            
            // Group nodes by house section
            let groups = groupNodes(nodes)
            
            // Background
            context.setFillColor(UIColor.systemBackground.cgColor)
            context.fill(CGRect(x: 0, y: 0, width: W, height: H))
            
            // Title
            let title = "STRATEGY HOUSE / 战略屋"
            let titleAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 18, weight: .bold),
                .foregroundColor: UIColor.label
            ]
            let titleSize = title.size(withAttributes: titleAttrs)
            title.draw(at: CGPoint(x: (W - titleSize.width) / 2, y: y), withAttributes: titleAttrs)
            y += 40
            
            // Roof (vision triangle)
            if !groups.roof.isEmpty {
                let roofH: CGFloat = 60 + CGFloat(groups.roof.count) * 22
                
                context.setFillColor(UIColor(red: 1.0, green: 0.97, blue: 0.88, alpha: 1.0).cgColor)
                context.beginPath()
                context.move(to: CGPoint(x: W/2, y: y))
                context.addLine(to: CGPoint(x: pad, y: y + roofH))
                context.addLine(to: CGPoint(x: W - pad, y: y + roofH))
                context.closePath()
                context.fillPath()
                
                context.setStrokeColor(UIColor(red: 1.0, green: 0.83, blue: 0.31, alpha: 1.0).cgColor)
                context.setLineWidth(2)
                context.beginPath()
                context.move(to: CGPoint(x: W/2, y: y))
                context.addLine(to: CGPoint(x: pad, y: y + roofH))
                context.addLine(to: CGPoint(x: W - pad, y: y + roofH))
                context.closePath()
                context.strokePath()
                
                let visionAttrs: [NSAttributedString.Key: Any] = [
                    .font: UIFont.systemFont(ofSize: 11, weight: .bold),
                    .foregroundColor: UIColor(red: 0.96, green: 0.50, blue: 0.09, alpha: 1.0)
                ]
                let visionLabel = "VISION / 愿景"
                let vs = visionLabel.size(withAttributes: visionAttrs)
                visionLabel.draw(at: CGPoint(x: (W - vs.width) / 2, y: y + 28), withAttributes: visionAttrs)
                
                for (i, node) in groups.roof.enumerated() {
                    let labelAttrs: [NSAttributedString.Key: Any] = [
                        .font: UIFont.systemFont(ofSize: 13),
                        .foregroundColor: UIColor(red: 0.72, green: 0.53, blue: 0.04, alpha: 1.0)
                    ]
                    let label = node.label.count > 35 ? String(node.label.prefix(33)) + "..." : node.label
                    let ls = label.size(withAttributes: labelAttrs)
                    label.draw(at: CGPoint(x: (W - ls.width) / 2, y: y + 48 + CGFloat(i) * 22), withAttributes: labelAttrs)
                }
                
                y += roofH + 4
            }
            
            // Pillars
            if !groups.pillar.isEmpty {
                let gap: CGFloat = 8
                let pillarW = (contentW - gap * CGFloat(groups.pillar.count - 1)) / CGFloat(groups.pillar.count)
                let pillarH: CGFloat = 120
                
                for (i, node) in groups.pillar.enumerated() {
                    let px = pad + CGFloat(i) * (pillarW + gap)
                    let rect = CGRect(x: px, y: y, width: pillarW, height: pillarH)
                    
                    context.setFillColor(UIColor(red: 0.91, green: 0.96, blue: 0.91, alpha: 1.0).cgColor)
                    let path = UIBezierPath(roundedRect: rect, cornerRadius: 4)
                    context.addPath(path.cgPath)
                    context.fillPath()
                    context.setStrokeColor(UIColor(red: 0.51, green: 0.78, blue: 0.52, alpha: 1.0).cgColor)
                    context.addPath(path.cgPath)
                    context.strokePath()
                    
                    let headerAttrs: [NSAttributedString.Key: Any] = [
                        .font: UIFont.systemFont(ofSize: 11, weight: .bold),
                        .foregroundColor: UIColor(red: 0.18, green: 0.49, blue: 0.20, alpha: 1.0)
                    ]
                    let label = node.label.count > Int(pillarW / 7) ? String(node.label.prefix(Int(pillarW / 7) - 2)) + ".." : node.label
                    label.draw(at: CGPoint(x: px + 8, y: y + 20), withAttributes: headerAttrs)
                    
                    if let content = node.content {
                        let contentAttrs: [NSAttributedString.Key: Any] = [
                            .font: UIFont.systemFont(ofSize: 11),
                            .foregroundColor: UIColor.secondaryLabel
                        ]
                        let contentLines = wrapText(content, maxWidth: pillarW - 16, font: UIFont.systemFont(ofSize: 11))
                        for (li, line) in contentLines.prefix(5).enumerated() {
                            line.draw(at: CGPoint(x: px + 8, y: y + 36 + CGFloat(li) * 14), withAttributes: contentAttrs)
                        }
                    }
                }
                y += pillarH + 10
            }
            
            // Other sections
            y = drawSection(context: context, meta: houseSectionMeta("internal"), nodes: groups.internal, startY: y, sectionW: contentW, pad: pad)
            y = drawSection(context: context, meta: houseSectionMeta("foundation"), nodes: groups.foundation, startY: y, sectionW: contentW, pad: pad)
            y = drawSection(context: context, meta: houseSectionMeta("action"), nodes: groups.action, startY: y, sectionW: contentW, pad: pad)
            y = drawSection(context: context, meta: houseSectionMeta("signal"), nodes: groups.signal, startY: y, sectionW: contentW, pad: pad)
            if !groups.external.isEmpty {
                y = drawSection(context: context, meta: houseSectionMeta("external"), nodes: groups.external, startY: y, sectionW: contentW, pad: pad)
            }
            
            // Watermark
            let watermarkAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 10),
                .foregroundColor: UIColor.tertiaryLabel
            ]
            let wm = "Generated by Strategic Canvas"
            let wmSize = wm.size(withAttributes: watermarkAttrs)
            wm.draw(at: CGPoint(x: (W - wmSize.width) / 2, y: y + 16), withAttributes: watermarkAttrs)
        }
    }
    
    // MARK: - Private helpers
    
    private struct HouseSections {
        var roof: [CanvasNode] = []
        var pillar: [CanvasNode] = []
        var foundation: [CanvasNode] = []
        var `internal`: [CanvasNode] = []
        var signal: [CanvasNode] = []
        var action: [CanvasNode] = []
        var external: [CanvasNode] = []
    }
    
    private static func groupNodes(_ nodes: [CanvasNode]) -> HouseSections {
        var sections = HouseSections()
        let map: [String: WritableKeyPath<HouseSections, [CanvasNode]>] = [
            "goal": \.roof, "position": \.roof,
            "option": \.pillar, "mechanism": \.pillar,
            "resource": \.foundation, "constraint": \.foundation, "evidence": \.foundation,
            "tension": \.internal, "assumption": \.internal, "risk": \.internal, "pattern": \.internal,
            "signal": \.signal, "action": \.action, "stakeholder": \.external,
        ]
        for node in nodes {
            if let keyPath = map[node.node_type] {
                sections[keyPath: keyPath].append(node)
            } else {
                sections.internal.append(node)
            }
        }
        return sections
    }
    
    private static func houseSectionMeta(_ section: String) -> (label: String, color: UIColor, bg: UIColor, border: UIColor) {
        switch section {
        case "roof":       return ("VISION / 愿景",     UIColor(red: 0.96, green: 0.50, blue: 0.09, alpha: 1.0), UIColor(red: 1.0, green: 0.97, blue: 0.88, alpha: 1.0), UIColor(red: 1.0, green: 0.83, blue: 0.31, alpha: 1.0))
        case "pillar":     return ("PILLARS / 战略支柱", UIColor(red: 0.18, green: 0.49, blue: 0.20, alpha: 1.0), UIColor(red: 0.91, green: 0.96, blue: 0.91, alpha: 1.0), UIColor(red: 0.51, green: 0.78, blue: 0.52, alpha: 1.0))
        case "foundation": return ("FOUNDATION / 地基",  UIColor(red: 0.08, green: 0.40, blue: 0.75, alpha: 1.0), UIColor(red: 0.89, green: 0.95, blue: 0.99, alpha: 1.0), UIColor(red: 0.39, green: 0.71, blue: 0.96, alpha: 1.0))
        case "internal":   return ("TENSIONS / 内部张力", UIColor(red: 0.90, green: 0.32, blue: 0.00, alpha: 1.0), UIColor(red: 1.0, green: 0.95, blue: 0.88, alpha: 1.0), UIColor(red: 1.0, green: 0.72, blue: 0.30, alpha: 1.0))
        case "signal":     return ("SIGNALS / 验证信号",  UIColor(red: 0.00, green: 0.51, blue: 0.56, alpha: 1.0), UIColor(red: 0.88, green: 0.97, blue: 0.98, alpha: 1.0), UIColor(red: 0.30, green: 0.82, blue: 0.88, alpha: 1.0))
        case "action":     return ("ACTIONS / 下一步",    UIColor(red: 0.42, green: 0.11, blue: 0.60, alpha: 1.0), UIColor(red: 0.95, green: 0.90, blue: 0.96, alpha: 1.0), UIColor(red: 0.73, green: 0.41, blue: 0.78, alpha: 1.0))
        case "external":   return ("EXTERNAL / 外部",     UIColor(red: 0.22, green: 0.28, blue: 0.31, alpha: 1.0), UIColor(red: 0.93, green: 0.94, blue: 0.95, alpha: 1.0), UIColor(red: 0.56, green: 0.65, blue: 0.69, alpha: 1.0))
        default:           return ("", .black, .white, .gray)
        }
    }
    
    private static func drawSection(
        context: CGContext,
        meta: (label: String, color: UIColor, bg: UIColor, border: UIColor),
        nodes: [CanvasNode],
        startY: CGFloat,
        sectionW: CGFloat,
        pad: CGFloat
    ) -> CGFloat {
        guard !nodes.isEmpty else { return startY }
        
        let innerPad: CGFloat = 10
        let lineH: CGFloat = 16
        let font = UIFont.systemFont(ofSize: 12)
        
        // Calculate height
        var totalH: CGFloat = 36
        for node in nodes {
            let fullText = node.label + (node.content.map { " — " + $0 } ?? "")
            let lines = wrapText(fullText, maxWidth: sectionW - innerPad * 2 - 16, font: font)
            totalH += 8 + CGFloat(lines.count) * lineH + 8
        }
        
        let rect = CGRect(x: pad, y: startY, width: sectionW, height: totalH)
        context.setFillColor(meta.bg.cgColor)
        let path = UIBezierPath(roundedRect: rect, cornerRadius: 6)
        context.addPath(path.cgPath)
        context.fillPath()
        context.setStrokeColor(meta.border.cgColor)
        context.addPath(path.cgPath)
        context.strokePath()
        
        // Header
        let headerAttrs: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: 11, weight: .bold),
            .foregroundColor: meta.color
        ]
        meta.label.draw(at: CGPoint(x: pad + innerPad, y: startY + 22), withAttributes: headerAttrs)
        
        var ny = startY + 36
        for node in nodes {
            let color = UIColor(hex: node.color) ?? .gray
            context.setFillColor(color.cgColor)
            let dotRect = CGRect(x: pad + innerPad, y: ny, width: 6, height: 6)
            let dotPath = UIBezierPath(roundedRect: dotRect, cornerRadius: 3)
            context.addPath(dotPath.cgPath)
            context.fillPath()
            
            let fullText = node.label + (node.content.map { " — " + $0 } ?? "")
            let lines = wrapText(fullText, maxWidth: sectionW - innerPad * 2 - 16, font: font)
            let textAttrs: [NSAttributedString.Key: Any] = [
                .font: font,
                .foregroundColor: UIColor.label
            ]
            
            for (li, line) in lines.enumerated() {
                line.draw(at: CGPoint(x: pad + innerPad + 14, y: ny + 6 + CGFloat(li) * lineH), withAttributes: textAttrs)
            }
            
            // Confidence
            let confAttrs: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 10),
                .foregroundColor: UIColor.tertiaryLabel
            ]
            let confText = "\(Int(node.confidence * 100))%"
            confText.draw(at: CGPoint(x: pad + sectionW - innerPad - 30, y: ny + 6), withAttributes: confAttrs)
            
            ny += 8 + CGFloat(lines.count) * lineH + 4
        }
        
        return startY + totalH + 10
    }
    
    private static func wrapText(_ text: String, maxWidth: CGFloat, font: UIFont) -> [String] {
        var lines: [String] = []
        var currentLine = ""
        for char in text {
            let test = currentLine + String(char)
            let size = (test as NSString).size(withAttributes: [.font: font])
            if size.width > maxWidth, !currentLine.isEmpty {
                lines.append(currentLine)
                currentLine = String(char)
            } else {
                currentLine = test
            }
        }
        if !currentLine.isEmpty { lines.append(currentLine) }
        return lines
    }
}
```

---

## 7. ProjectStore & Models

```swift
// ProjectStore.swift
import SwiftUI

@MainActor
final class ProjectStore: ObservableObject {
    @Published var projects: [Project] = []
    @Published var activeProjectId: String?
    
    private let storageKey = "strategy_canvas_projects"
    
    var activeProject: Project? {
        projects.first { $0.id == activeProjectId }
    }
    
    init() { load() }
    
    func createProject(name: String = "New Project") {
        let project = Project(name: name)
        projects.insert(project, at: 0)
        activeProjectId = project.id
        save()
    }
    
    func selectProject(_ id: String) {
        guard projects.contains(where: { $0.id == id }) else { return }
        activeProjectId = id
        save()
    }
    
    func renameProject(_ id: String, to name: String) {
        guard let idx = projects.firstIndex(where: { $0.id == id }) else { return }
        projects[idx].name = name
        save()
    }
    
    func deleteProject(_ id: String) {
        projects.removeAll { $0.id == id }
        if activeProjectId == id {
            activeProjectId = projects.first?.id
        }
        save()
    }
    
    func addMessage(_ message: ChatMessage, toActiveProject: Bool) {
        guard toActiveProject, let idx = projects.firstIndex(where: { $0.id == activeProjectId }) else { return }
        projects[idx].messages.append(message)
        save()
    }
    
    func updateActiveProject(_ update: (inout Project) -> Void) {
        guard let idx = projects.firstIndex(where: { $0.id == activeProjectId }) else { return }
        update(&projects[idx])
        save()
    }
    
    private func load() {
        guard let data = UserDefaults.standard.data(forKey: storageKey),
              let saved = try? JSONDecoder().decode(ProjectStorage.self, from: data) else {
            // First launch: create default project
            createProject(name: "My Strategy")
            return
        }
        projects = saved.projects
        activeProjectId = saved.activeId ?? projects.first?.id
        if projects.isEmpty {
            createProject(name: "My Strategy")
        }
    }
    
    private func save() {
        let storage = ProjectStorage(projects: projects, activeId: activeProjectId)
        if let data = try? JSONEncoder().encode(storage) {
            UserDefaults.standard.set(data, forKey: storageKey)
        }
    }
}

struct ProjectStorage: Codable {
    var projects: [Project]
    var activeId: String?
}
```

```swift
// ProjectModels.swift
import Foundation

struct Project: Identifiable, Codable {
    let id: String
    var name: String
    let createdAt: String
    var messages: [ChatMessageDTO]
    var graphData: GraphData
    var goldenPhrases: [String]
    var namedConcepts: [String]
    var stage: String
    var confidence: Double
    var judgment: String
    
    init(name: String) {
        self.id = Date.now.timeIntervalSince1970.description + UUID().uuidString.prefix(6)
        self.name = name
        self.createdAt = ISO8601DateFormatter().string(from: Date())
        self.messages = []
        self.graphData = GraphData(nodes: [], links: [])
        self.goldenPhrases = []
        self.namedConcepts = []
        self.stage = "explore"
        self.confidence = 0.0
        self.judgment = ""
    }
}

struct GraphData: Codable {
    var nodes: [CanvasNode]
    var links: [CanvasLink]
}

struct ChatMessageDTO: Codable {
    let speaker: String
    let text: String
}

// Canvas types imported from API — see BackendClient/Models

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
    let source: String
    let target: String
    let label: String?
    let strength: Double
    let color: String?
}
```

---

## 8. SettingsStore + SettingsScreen

```swift
// SettingsStore.swift
import SwiftUI

@MainActor
final class SettingsStore: ObservableObject {
    @AppStorage("backend_url") var backendURL: String = ""
    @AppStorage("model") var model: String = "deepseek-chat"
    
    @Published var connectionStatus: ConnectionTestStatus = .untested
    @Published var isTesting = false
    
    var isConfigured: Bool {
        !backendURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !(KeychainManager.shared.read(key: "api_key") ?? "").isEmpty
    }
    
    enum ConnectionTestStatus {
        case untested, testing, success, failed(String)
    }
    
    var apiKey: String {
        get { KeychainManager.shared.read(key: "api_key") ?? "" }
        set { KeychainManager.shared.save(key: "api_key", value: newValue) }
    }
    
    func testConnection() async {
        isTesting = true
        connectionStatus = .testing
        
        let cleanURL = backendURL.trimmingCharacters(in: .whitespacesAndNewlines)
                         .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: "\(cleanURL)/api/skills") else {
            connectionStatus = .failed("Invalid URL")
            isTesting = false
            return
        }
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            if let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) {
                connectionStatus = .success
            } else {
                connectionStatus = .failed("Server returned error")
            }
        } catch {
            connectionStatus = .failed(error.localizedDescription)
        }
        
        isTesting = false
    }
}
```

```swift
// KeychainManager.swift
import Security
import Foundation

final class KeychainManager {
    static let shared = KeychainManager()
    private let service = "com.strategiccanvas.ios"
    
    func save(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        delete(key: key)
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlocked
        ]
        SecItemAdd(query as CFDictionary, nil)
    }
    
    func read(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    
    func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
```

```swift
// SettingsScreen.swift
import SwiftUI

struct SettingsScreen: View {
    @StateObject private var store = SettingsStore()
    @State private var apiKeyInput: String = ""
    @State private var showApiKey = false
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Backend Connection") {
                    TextField("Backend URL", text: $store.backendURL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                        .accessibilityLabel("Backend URL")
                    
                    HStack {
                        if showApiKey {
                            TextField("API Key", text: $apiKeyInput)
                                .autocapitalization(.none)
                                .disableAutocorrection(true)
                        } else {
                            SecureField("API Key", text: $apiKeyInput)
                        }
                        Button {
                            showApiKey.toggle()
                        } label: {
                            Image(systemName: showApiKey ? "eye.slash" : "eye")
                        }
                        .accessibilityLabel(showApiKey ? "Hide API key" : "Show API key")
                    }
                }
                
                Section("Model") {
                    Picker("Model", selection: $store.model) {
                        Text("DeepSeek Chat").tag("deepseek-chat")
                        Text("DeepSeek Reasoner").tag("deepseek-reasoner")
                    }
                }
                
                Section {
                    Button {
                        Task {
                            store.apiKey = apiKeyInput
                            await store.testConnection()
                        }
                    } label: {
                        HStack {
                            Text("Test Connection")
                            if store.isTesting {
                                Spacer()
                                ProgressView()
                            }
                        }
                    }
                    .disabled(store.backendURL.isEmpty || apiKeyInput.isEmpty || store.isTesting)
                    
                    if case .success = store.connectionStatus {
                        Label("Connected", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                    } else if case .failed(let msg) = store.connectionStatus {
                        Label("Failed: \(msg)", systemImage: "xmark.circle.fill")
                            .foregroundStyle(.red)
                    }
                }
                
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0 (1)")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        store.apiKey = apiKeyInput
                        dismiss()
                    }
                }
            }
            .onAppear {
                apiKeyInput = store.apiKey
            }
        }
    }
}
```

---

## 9. Design Tokens

```swift
// DesignTokens.swift
import SwiftUI

enum DesignTokens {
    enum spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
        static let xl: CGFloat = 20
        static let xxl: CGFloat = 24
        static let xxxl: CGFloat = 32
    }
    
    enum radius {
        static let sm: CGFloat = 6
        static let md: CGFloat = 10
        static let lg: CGFloat = 16
        static let pill: CGFloat = 9999
        static let chatBubble: CGFloat = 12
    }
}

enum Haptics {
    static func light() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }
    static func medium() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }
    static func success() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }
}
```

---

## 10. Onboarding View

```swift
// OnboardingView.swift
import SwiftUI

struct OnboardingView: View {
    @ObservedObject var settingsStore: SettingsStore
    @State private var urlInput = ""
    @State private var apiKeyInput = ""
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                Spacer()
                
                Image(systemName: "building.columns.fill")
                    .font(.system(size: 64))
                    .foregroundStyle(.tint)
                
                Text("Strategy Canvas")
                    .font(.largeTitle.weight(.bold))
                
                Text("AI Strategic Coaching")
                    .font(.title3)
                    .foregroundStyle(.secondary)
                
                VStack(spacing: 16) {
                    TextField("Backend URL (e.g. https://strategy.example.com)", text: $urlInput)
                        .textFieldStyle(.roundedBorder)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                    
                    SecureField("API Key (sk-...)", text: $apiKeyInput)
                        .textFieldStyle(.roundedBorder)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                }
                .padding(.horizontal, 32)
                
                Button {
                    settingsStore.backendURL = urlInput
                    settingsStore.apiKey = apiKeyInput
                } label: {
                    Text("Get Started")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal, 32)
                .disabled(urlInput.isEmpty || apiKeyInput.isEmpty)
                
                Spacer()
                
                Text("Your API key is stored securely in the Keychain.")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                    .padding(.bottom)
            }
            .navigationBarHidden(true)
        }
    }
}
```
