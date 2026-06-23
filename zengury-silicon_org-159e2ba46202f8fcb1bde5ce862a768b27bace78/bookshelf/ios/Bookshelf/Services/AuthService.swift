import Foundation

@MainActor
class AuthService: ObservableObject {
    static let shared = AuthService()

    @Published var isAuthenticated = false
    @Published var token: String?
    @Published var userId: String?

    private let tokenKey = "bookshelf.auth.token"
    private let userIdKey = "bookshelf.auth.userId"

    init() {
        self.token = UserDefaults.standard.string(forKey: tokenKey)
        self.userId = UserDefaults.standard.string(forKey: userIdKey)
        self.isAuthenticated = token != nil
    }

    func register(email: String, password: String, name: String) async throws {
        let req = RegisterRequest(email: email, password: password, name: name)
        let res: AuthResponse = try await APIClient.shared.request("/auth/register", method: "POST", body: req)
        await saveAuth(res)
    }

    func login(email: String, password: String) async throws {
        let req = LoginRequest(email: email, password: password)
        let res: AuthResponse = try await APIClient.shared.request("/auth/login", method: "POST", body: req)
        await saveAuth(res)
    }

    func oauthLogin(provider: String, idToken: String) async throws {
        let req = OAuthRequest(provider: provider, idToken: idToken)
        let res: AuthResponse = try await APIClient.shared.request("/auth/oauth", method: "POST", body: req)
        await saveAuth(res)
    }

    func logout() {
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: userIdKey)
        Task { await APIClient.shared.setToken(nil) }
        token = nil
        userId = nil
        isAuthenticated = false
    }

    private func saveAuth(_ response: AuthResponse) async {
        UserDefaults.standard.set(response.token, forKey: tokenKey)
        UserDefaults.standard.set(response.userId, forKey: userIdKey)
        await APIClient.shared.setToken(response.token)
        token = response.token
        userId = response.userId
        isAuthenticated = true
    }
}
