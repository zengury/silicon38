import SwiftUI

/// Global application state — owns auth, subscription, and navigation state.
/// This is the single source of truth that flows down to all views.
@MainActor
class AppState: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isSubscribed = false
    @Published var needsOnboarding: Bool
    @Published var shouldShowPaywall = false
    @Published var selectedTab = 0

    init() {
        // Per soul.md (Salk — subtraction): the app state starts minimal.
        // Only track what changes navigation. Everything else lives in services.
        self.needsOnboarding = !UserDefaults.standard.bool(forKey: "onboarding.completed")
    }

    func initialize() {
        isAuthenticated = AuthService.shared.isAuthenticated
        Task {
            try? await SubscriptionService.shared.fetchStatus()
            isSubscribed = SubscriptionService.shared.isSubscribed
        }
    }

    func completeOnboarding() {
        UserDefaults.standard.set(true, forKey: "onboarding.completed")
        needsOnboarding = false
    }

    func onAuthenticated() {
        isAuthenticated = true
        Task {
            try? await SubscriptionService.shared.fetchStatus()
            isSubscribed = SubscriptionService.shared.isSubscribed
            shouldShowPaywall = !isSubscribed
        }
    }

    func onSubscribed() {
        isSubscribed = true
        shouldShowPaywall = false
    }

    func logout() {
        AuthService.shared.logout()
        isAuthenticated = false
        isSubscribed = false
    }

    /// Navigate to the search tab — used when a shelf search button is tapped
    func navigateToSearch() {
        selectedTab = 1
    }
}
