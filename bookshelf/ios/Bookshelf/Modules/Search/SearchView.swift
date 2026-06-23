import SwiftUI

/// Search across all shelves — the primary job (per vision: "find by physical location").
/// Results always show shelf name + position — the location IS the answer.
struct SearchView: View {
    @StateObject private var service = BookService.shared
    @State private var query = ""
    @State private var selectedBook: Book?

    var body: some View {
        NavigationStack {
            VStack {
                if query.isEmpty {
                    recentSearches
                } else if service.searchResults.isEmpty {
                    emptyResults
                } else {
                    searchResults
                }
            }
            .navigationTitle("Search")
            .searchable(
                text: $query,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: "Search by title or author..."
            )
            .onSubmit(of: .search) {
                Task { await performSearch() }
            }
            .onChange(of: query) { newValue in
                if newValue.isEmpty {
                    service.searchResults = []
                    service.searchTotal = 0
                }
            }
            .sheet(item: $selectedBook) { book in
                BookDetailSheet(book: book)
            }
        }
    }

    private var recentSearches: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Start typing to search across all shelves")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .padding()
            Spacer()
        }
    }

    private var emptyResults: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "magnifyingglass")
                .font(.system(size: 40))
                .foregroundColor(.secondary)

            Text("No books found matching \"\(query)\"")
                .foregroundColor(.secondary)
            Spacer()
        }
    }

    private var searchResults: some View {
        List {
            Text("\(service.searchTotal) results")
                .font(.caption)
                .foregroundColor(.secondary)
                .listRowSeparator(.hidden)

            ForEach(service.searchResults) { book in
                Button(action: { selectedBook = book }) {
                    SearchResultRow(book: book)
                }
                .buttonStyle(.plain)
            }
        }
        .listStyle(.plain)
    }

    private func performSearch() async {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        do {
            try await service.searchBooks(query: query)
        } catch {
            service.searchResults = []
        }
    }
}

// MARK: - Search Result Row

/// The most important UI decision (per UX spec): every search result
/// shows the physical location. "Row 2, Col 4" is the answer.
struct SearchResultRow: View {
    let book: Book

    var body: some View {
        HStack(spacing: 12) {
            // Spine color indicator
            RoundedRectangle(cornerRadius: 3)
                .fill(spineColor(book.title))
                .frame(width: 4, height: 48)

            VStack(alignment: .leading, spacing: 3) {
                Text(book.title)
                    .font(.body)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                    .lineLimit(1)

                Text(book.author)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)

                // Location — the primary action signal
                HStack(spacing: 4) {
                    Image(systemName: "books.vertical.fill")
                        .font(.system(size: 9))
                        .foregroundColor(.brown)
                    Text(book.shelfName ?? "Shelf")
                        .font(.caption2)
                        .foregroundColor(.brown)

                    Text("·")
                        .foregroundColor(.secondary)

                    Image(systemName: "location.fill")
                        .font(.system(size: 9))
                        .foregroundColor(.brown)
                    Text("Row \(book.positionRow), Col \(book.positionCol)")
                        .font(.caption2)
                        .foregroundColor(.brown)
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 6)
    }

    private func spineColor(_ title: String) -> Color {
        let hash = abs(title.hashValue)
        let colors: [Color] = [.brown, .indigo, .red, .green, .orange]
        return colors[hash % colors.count]
    }
}
