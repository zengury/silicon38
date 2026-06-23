import SwiftUI
import AuthenticationServices

/// Email/password or Apple Sign In — per PRD.
/// After auth, transitions to Paywall or MainTab.
struct AuthView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var viewModel = AuthViewModel()

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            // Logo
            Image(systemName: "books.vertical.fill")
                .font(.system(size: 56))
                .foregroundColor(.brown)

            Text("Bookshelf")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("Your library, digitized.")
                .font(.subheadline)
                .foregroundColor(.secondary)

            Spacer().frame(height: 32)

            // Email/Password fields
            VStack(spacing: 12) {
                TextField("Email", text: $viewModel.email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                SecureField("Password (8+ chars, A-Z, a-z, 0-9)", text: $viewModel.password)
                    .textContentType(.password)
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .padding(.horizontal, 32)

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.horizontal, 32)
            }

            // Sign Up
            Button(action: { Task { await viewModel.register(appState) } }) {
                HStack {
                    if viewModel.isLoading { ProgressView().tint(.white) }
                    Text("Create Account")
                        .font(.headline)
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.brown)
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(viewModel.isLoading)
            .padding(.horizontal, 32)

            // Sign In
            Button(action: { Task { await viewModel.login(appState) } }) {
                Text("Sign In")
                    .font(.headline)
                    .foregroundColor(.brown)
            }
            .disabled(viewModel.isLoading)

            // Divider
            HStack {
                Rectangle().frame(height: 1).foregroundColor(.secondary.opacity(0.3))
                Text("or").font(.caption).foregroundColor(.secondary)
                Rectangle().frame(height: 1).foregroundColor(.secondary.opacity(0.3))
            }
            .padding(.horizontal, 48)

            // Apple Sign In
            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.fullName, .email]
            } onCompletion: { result in
                Task { await viewModel.handleAppleSignIn(result, appState: appState) }
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .padding(.horizontal, 32)

            Spacer()
        }
        .background(Color(.systemGroupedBackground))
    }
}

@MainActor
class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var isLoading = false
    @Published var errorMessage: String?

    func register(_ appState: AppState) async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Email and password are required"
            return
        }
        isLoading = true; errorMessage = nil
        do {
            let name = email.components(separatedBy: "@").first ?? "Reader"
            try await AuthService.shared.register(email: email, password: password, name: name)
            appState.onAuthenticated()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func login(_ appState: AppState) async {
        isLoading = true; errorMessage = nil
        do {
            try await AuthService.shared.login(email: email, password: password)
            appState.onAuthenticated()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func handleAppleSignIn(_ result: Result<ASAuthorization, Error>, appState: AppState) async {
        switch result {
        case .success(let auth):
            guard let credential = auth.credential as? ASAuthorizationAppleIDCredential,
                  let idToken = credential.identityToken,
                  let tokenString = String(data: idToken, encoding: .utf8) else {
                errorMessage = "Apple Sign In failed"
                return
            }
            isLoading = true; errorMessage = nil
            do {
                try await AuthService.shared.oauthLogin(provider: "apple", idToken: tokenString)
                appState.onAuthenticated()
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        case .failure(let error):
            errorMessage = error.localizedDescription
        }
    }
}
