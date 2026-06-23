import SwiftUI

/// Three tabs only — per soul.md (Salk: subtraction) and UX spec.
/// Shelves is home. Search is the primary job. Profile is utilities.
struct MainTabView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        TabView(selection: $appState.selectedTab) {
            ShelfListView()
                .tabItem {
                    Label("Shelves", systemImage: "books.vertical.fill")
                }
                .tag(0)

            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
                .tag(1)

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.circle")
                }
                .tag(2)
        }
        .tint(.brown) // Per soul — warm, grounded, like a wooden shelf
    }
}
