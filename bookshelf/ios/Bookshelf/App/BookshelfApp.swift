import SwiftUI

@main
struct BookshelfApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            Group {
                if appState.needsOnboarding {
                    OnboardingView()
                        .environmentObject(appState)
                } else if !appState.isAuthenticated {
                    AuthView()
                        .environmentObject(appState)
                } else if !appState.isSubscribed && appState.shouldShowPaywall {
                    PaywallView()
                        .environmentObject(appState)
                } else {
                    MainTabView()
                        .environmentObject(appState)
                }
            }
            .onAppear {
                appState.initialize()
            }
        }
    }
}
