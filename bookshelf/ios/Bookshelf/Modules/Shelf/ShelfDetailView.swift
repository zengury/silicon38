import SwiftUI

/// Shelf detail — the grid view that mirrors the physical shelf layout.
/// This is the soul of the app (Esherick: the deep module is hidden;
/// what the user sees is the shelf exactly as it exists in their room).
struct ShelfDetailView: View {
    let shelf: Shelf
    @EnvironmentObject var appState: AppState
    @State private var books: [Book] = []
    @State private var isLoading = true
    @State private var selectedBook: Book?

    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView()
                    .padding(.top, 100)
            } else if books.isEmpty {
                VStack(spacing: 24) {
                    Image(systemName: "camera.fill")
                        .font(.system(size: 48))
                        .foregroundColor(.brown)

                    Text("This shelf is empty")
                        .font(.title3)

                    Text("Take a photo to fill it with books")
                        .foregroundColor(.secondary)

                    NavigationLink(destination: CameraView(
                        shelfId: shelf.id,
                        shelfName: shelf.name,
                        rowCount: shelf.rowCount,
                        columnCount: shelf.columnCount
                    )) {
                        Label("Take Photo", systemImage: "camera.fill")
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.brown)
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                    }
                }
                .padding(.top, 80)
            } else {
                shelfGrid
            }
        }
        .navigationTitle(shelf.name)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                NavigationLink(destination: CameraView(
                    shelfId: shelf.id,
                    shelfName: shelf.name,
                    rowCount: shelf.rowCount,
                    columnCount: shelf.columnCount
                )) {
                    Image(systemName: "camera.fill")
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: { appState.navigateToSearch() }) {
                    Image(systemName: "magnifyingglass")
                }
            }
        }
        .sheet(item: $selectedBook) { book in
            BookDetailSheet(book: book)
        }
        .task {
            await loadBooks()
        }
    }

    // MARK: - Shelf Grid

    private var shelfGrid: some View {
        let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: shelf.columnCount)

        return LazyVGrid(columns: columns, spacing: 4) {
            ForEach(Array(booksByPosition().enumerated()), id: \.offset) { _, book in
                BookCell(book: book)
                    .onTapGesture { selectedBook = book }
            }
        }
        .padding()
    }

    /// Arrange books into grid positions, filling empty slots with nil
    private func booksByPosition() -> [Book?] {
        var grid = Array(repeating: nil as Book?, count: shelf.rowCount * shelf.columnCount)
        for book in books {
            let row = max(0, min(book.positionRow - 1, shelf.rowCount - 1))
            let col = max(0, min(book.positionCol - 1, shelf.columnCount - 1))
            let index = row * shelf.columnCount + col
            if index < grid.count {
                grid[index] = book
            }
        }
        return grid
    }

    private func loadBooks() async {
        isLoading = true
        do {
            books = try await BookService.shared.fetchBooks(shelfId: shelf.id)
        } catch {
            books = []
        }
        isLoading = false
    }
}

// MARK: - Book Cell

struct BookCell: View {
    let book: Book?

    var body: some View {
        ZStack {
            if let book = book {
                VStack(spacing: 2) {
                    // Cover placeholder — in production, AsyncImage from coverUrl
                    RoundedRectangle(cornerRadius: 3)
                        .fill(spineColor(book.title))
                        .aspectRatio(0.65, contentMode: .fit)

                    Text(book.title)
                        .font(.system(size: 7))
                        .lineLimit(2)
                        .foregroundColor(.primary)

                    if (book.confidence ?? 1.0) < 0.7 {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 6))
                            .foregroundColor(.yellow)
                    }
                }
                .padding(2)
            } else {
                RoundedRectangle(cornerRadius: 3)
                    .fill(Color(.systemGray5))
                    .aspectRatio(0.65, contentMode: .fit)
                    .overlay(
                        Image(systemName: "questionmark")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    )
            }
        }
    }

    private func spineColor(_ title: String) -> Color {
        let hash = abs(title.hashValue)
        let colors: [Color] = [
            Color(red: 0.55, green: 0.27, blue: 0.07), // brown
            Color(red: 0.18, green: 0.31, blue: 0.55), // navy
            Color(red: 0.50, green: 0.11, blue: 0.11), // burgundy
            Color(red: 0.13, green: 0.37, blue: 0.13), // forest
            Color(red: 0.45, green: 0.35, blue: 0.15), // olive
        ]
        return colors[hash % colors.count]
    }
}

// MARK: - Book Detail Sheet (half-screen)

struct BookDetailSheet: View {
    let book: Book

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Book cover placeholder + metadata
                    HStack(alignment: .top, spacing: 16) {
                        RoundedRectangle(cornerRadius: 6)
                            .fill(spineColor(book.title))
                            .frame(width: 80, height: 120)
                            .overlay(
                                Text(String(book.title.prefix(1)))
                                    .font(.largeTitle)
                                    .foregroundColor(.white.opacity(0.6))
                            )

                        VStack(alignment: .leading, spacing: 4) {
                            Text(book.title)
                                .font(.title3)
                                .fontWeight(.bold)

                            Text(book.author)
                                .font(.subheadline)
                                .foregroundColor(.secondary)

                            if let isbn = book.isbn {
                                Text("ISBN: \(isbn)")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }

                    // Location
                    HStack(spacing: 4) {
                        Image(systemName: "books.vertical.fill")
                            .font(.caption)
                            .foregroundColor(.brown)
                        Text(book.shelfName ?? "Shelf")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text("·")
                            .foregroundColor(.secondary)
                        Image(systemName: "location.fill")
                            .font(.caption)
                            .foregroundColor(.brown)
                        Text("Row \(book.positionRow), Col \(book.positionCol)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)

                    // Confidence warning
                    if (book.confidence ?? 1.0) < 0.7 {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.yellow)
                            Text("AI is uncertain about this book. Tap to confirm or edit.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(10)
                        .background(Color.yellow.opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    Divider()

                    // Summary
                    if let summary = book.summary, !summary.isEmpty {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Summary")
                                .font(.headline)

                            Text(summary)
                                .font(.body)
                                .foregroundColor(.secondary)
                                .lineSpacing(4)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Book Details")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func spineColor(_ title: String) -> Color {
        let hash = abs(title.hashValue)
        let colors: [Color] = [
            Color(red: 0.55, green: 0.27, blue: 0.07),
            Color(red: 0.18, green: 0.31, blue: 0.55),
            Color(red: 0.50, green: 0.11, blue: 0.11),
            Color(red: 0.13, green: 0.37, blue: 0.13),
        ]
        return colors[hash % colors.count]
    }
}
