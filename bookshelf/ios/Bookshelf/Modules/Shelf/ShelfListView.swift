import SwiftUI

/// List of all shelves — per UX spec, this is the home screen (Tab 1).
struct ShelfListView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var service = ShelfService.shared
    @State private var showNewShelf = false
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if service.shelves.isEmpty && !isLoading {
                    emptyState
                } else {
                    shelfList
                }
            }
            .navigationTitle("My Library")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showNewShelf = true }) {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showNewShelf) {
                NewShelfView { shelf in
                    showNewShelf = false
                }
            }
            .task {
                await loadShelves()
            }
            .refreshable {
                await loadShelves()
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 24) {
            Image(systemName: "books.vertical")
                .font(.system(size: 64))
                .foregroundColor(.brown.opacity(0.5))

            Text("No shelves yet")
                .font(.title2)
                .fontWeight(.bold)

            Text("Take a photo of your first bookshelf to get started")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 48)

            Button(action: { showNewShelf = true }) {
                Label("Add Your First Shelf", systemImage: "camera.fill")
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.brown)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
            }
        }
        .padding()
    }

    private var shelfList: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(service.shelves) { shelf in
                    NavigationLink(destination: ShelfDetailView(shelf: shelf)) {
                        ShelfCard(shelf: shelf)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }

    private func loadShelves() async {
        isLoading = true; errorMessage = nil
        do {
            try await service.fetchShelves()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

// MARK: - Shelf Card

struct ShelfCard: View {
    let shelf: Shelf

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(shelf.name)
                        .font(.headline)
                        .foregroundColor(.primary)

                    Text("\(shelf.bookCount ?? 0) books · \(shelf.rowCount)×\(shelf.columnCount)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Miniature book spine visualization
            ShelfSpinePreview(rowCount: shelf.rowCount, columnCount: shelf.columnCount, bookCount: shelf.bookCount ?? 0)
                .frame(height: 40)
                .clipShape(RoundedRectangle(cornerRadius: 4))
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }
}

/// Miniature book spine strip — hint of what the shelf looks like
struct ShelfSpinePreview: View {
    let rowCount: Int
    let columnCount: Int
    let bookCount: Int

    var body: some View {
        GeometryReader { geo in
            let spineWidth = geo.size.width / CGFloat(columnCount)
            let spineHeight = geo.size.height / CGFloat(rowCount)

            ForEach(0..<rowCount, id: \.self) { row in
                ForEach(0..<columnCount, id: \.self) { col in
                    let index = row * columnCount + col
                    Rectangle()
                        .fill(index < bookCount ? spineColor(index) : Color(.systemGray5))
                        .frame(width: max(spineWidth - 1, 2), height: max(spineHeight - 1, 2))
                        .position(x: spineWidth * (CGFloat(col) + 0.5), y: spineHeight * (CGFloat(row) + 0.5))
                }
            }
        }
    }

    private func spineColor(_ index: Int) -> Color {
        let colors: [Color] = [.brown, .orange, .red, .blue, .green, .purple, .teal, .indigo]
        return colors[index % colors.count].opacity(0.7)
    }
}
