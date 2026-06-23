import SwiftUI

/// Profile tab — the minimum necessary (Salk: subtraction).
/// Subscription management, logout, privacy.
struct ProfileView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var subService = SubscriptionService.shared
    @State private var shelfCount = 0
    @State private var bookCount = 0

    var body: some View {
        NavigationStack {
            List {
                // User info
                Section {
                    HStack(spacing: 16) {
                        Image(systemName: "person.circle.fill")
                            .font(.system(size: 48))
                            .foregroundColor(.brown)

                        VStack(alignment: .leading, spacing: 2) {
                            Text(AuthService.shared.userId?.prefix(8) ?? "Reader")
                                .font(.title3)
                                .fontWeight(.semibold)

                            Text("\(shelfCount) shelves · \(bookCount) books")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 8)
                }

                // Subscription
                Section {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Bookshelf Premium")
                                .font(.body)
                            Text(planDescription)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        if subService.isSubscribed {
                            Image(systemName: "checkmark.seal.fill")
                                .foregroundColor(.brown)
                        }
                    }

                    if !subService.isSubscribed {
                        Button("Upgrade to Premium · $1.99/month") {
                            Task { await subscribe() }
                        }
                    } else {
                        Button("Manage Subscription") {
                            // Opens App Store subscription management
                            if let url = URL(string: "itms-apps://apps.apple.com/account/subscriptions") {
                                UIApplication.shared.open(url)
                            }
                        }
                    }
                } header: {
                    Text("Subscription")
                }

                // Settings
                Section {
                    NavigationLink(destination: Text("Notification preferences — coming in v1.1")) {
                        Label("Notifications", systemImage: "bell")
                    }
                    NavigationLink(destination: Text("Your photos are processed securely and deleted after 30 days.")) {
                        Label("Privacy", systemImage: "hand.raised")
                    }
                    NavigationLink(destination: Text("Bookshelf v1.0 · Made for book lovers")) {
                        Label("About", systemImage: "info.circle")
                    }
                } header: {
                    Text("Settings")
                }

                // Danger zone
                Section {
                    Button(role: .destructive, action: {
                        // Account deletion — requires confirmation
                    }) {
                        Label("Delete Account", systemImage: "trash")
                    }

                    Button("Sign Out", role: .destructive) {
                        appState.logout()
                    }
                }
            }
            .navigationTitle("Profile")
        }
        .task {
            try? await subService.fetchStatus()
            // Count shelves/books
            let shelves = ShelfService.shared.shelves
            shelfCount = shelves.count
            bookCount = shelves.reduce(0) { $0 + ($1.bookCount ?? 0) }
        }
    }

    private var planDescription: String {
        if subService.isSubscribed {
            return "Premium · $1.99/month"
        } else {
            return "Free · Limited to 1 shelf"
        }
    }

    private func subscribe() async {
        do {
            try await subService.purchase()
            appState.onSubscribed()
        } catch {
            // Error handled silently — user can retry
        }
    }
}
