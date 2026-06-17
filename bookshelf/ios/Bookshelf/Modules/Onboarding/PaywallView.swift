import SwiftUI

/// Subscription paywall — shown after auth if not subscribed.
/// $1.99/month, with restore option.
struct PaywallView: View {
    @EnvironmentObject var appState: AppState
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "books.vertical.fill")
                .font(.system(size: 56))
                .foregroundColor(.brown)

            Text("Bookshelf Premium")
                .font(.largeTitle)
                .fontWeight(.bold)

            VStack(alignment: .leading, spacing: 16) {
                FeatureRow(icon: "camera.fill", text: "Unlimited shelf photos")
                FeatureRow(icon: "sparkles", text: "AI book recognition & summaries")
                FeatureRow(icon: "magnifyingglass", text: "Search across all shelves")
                FeatureRow(icon: "rectangle.stack.fill", text: "Up to 10 shelves")
            }
            .padding(.horizontal, 32)

            VStack(spacing: 4) {
                Text("$1.99")
                    .font(.system(size: 48, weight: .bold))
                    .foregroundColor(.brown)
                Text("per month")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 8)

            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
            }

            Button(action: { Task { await subscribe() } }) {
                HStack {
                    if isLoading { ProgressView().tint(.white) }
                    Text("Subscribe")
                        .font(.headline)
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.brown)
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(isLoading)
            .padding(.horizontal, 32)

            Button("Restore Purchases") {
                Task { await restore() }
            }
            .font(.subheadline)
            .foregroundColor(.secondary)

            Spacer()
        }
        .background(Color(.systemGroupedBackground))
    }

    private func subscribe() async {
        isLoading = true; errorMessage = nil
        do {
            try await SubscriptionService.shared.purchase()
            appState.onSubscribed()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func restore() async {
        isLoading = true; errorMessage = nil
        do {
            try await SubscriptionService.shared.restore()
            if SubscriptionService.shared.isSubscribed {
                appState.onSubscribed()
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

struct FeatureRow: View {
    let icon: String
    let text: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(.brown)
                .frame(width: 28)
            Text(text)
                .font(.body)
            Spacer()
        }
    }
}

/// Allow skipping paywall (for development)
struct PaywallSkipModifier: ViewModifier {
    @EnvironmentObject var appState: AppState

    func body(content: Content) -> some View {
        content
            .toolbar {
                #if DEBUG
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Skip (Dev)") {
                        appState.onSubscribed()
                    }
                    .font(.caption)
                }
                #endif
            }
    }
}
