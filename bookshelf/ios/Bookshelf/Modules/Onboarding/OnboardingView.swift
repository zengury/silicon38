import SwiftUI

/// Three cards, skippable — per UX spec.
/// After onboarding, user goes to Auth.
struct OnboardingView: View {
    @EnvironmentObject var appState: AppState
    @State private var currentPage = 0

    private let pages: [OnboardingPage] = [
        OnboardingPage(
            icon: "camera.fill",
            title: "Your Library in One Photo",
            subtitle: "Take a photo of any bookshelf. Our AI recognizes every book and builds your digital library instantly."
        ),
        OnboardingPage(
            icon: "sparkles",
            title: "AI Knows Your Books",
            subtitle: "Every book gets its title, author, and a summary — automatically. No typing. No scanning barcodes."
        ),
        OnboardingPage(
            icon: "magnifyingglass",
            title: "Find Anything Instantly",
            subtitle: "Search by title or author. See exactly which shelf and position. Walk straight to your book."
        ),
    ]

    var body: some View {
        VStack {
            Spacer()

            TabView(selection: $currentPage) {
                ForEach(Array(pages.enumerated()), id: \.offset) { index, page in
                    OnboardingCard(page: page)
                        .tag(index)
                }
            }
            .tabViewStyle(.page(indexDisplayMode: .always))

            Spacer()

            Button(action: {
                appState.completeOnboarding()
            }) {
                Text(currentPage == pages.count - 1 ? "Get Started" : "Next")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.brown)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .padding(.horizontal, 32)

            Button("Skip") {
                appState.completeOnboarding()
            }
            .font(.subheadline)
            .foregroundColor(.secondary)
            .padding(.top, 8)
            .padding(.bottom, 48)
        }
        .background(Color(.systemGroupedBackground))
    }
}

struct OnboardingPage {
    let icon: String
    let title: String
    let subtitle: String
}

struct OnboardingCard: View {
    let page: OnboardingPage

    var body: some View {
        VStack(spacing: 24) {
            Image(systemName: page.icon)
                .font(.system(size: 64))
                .foregroundColor(.brown)
                .padding(.bottom, 8)

            Text(page.title)
                .font(.title2)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)

            Text(page.subtitle)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
                .lineSpacing(4)
        }
        .padding(.horizontal, 16)
    }
}
