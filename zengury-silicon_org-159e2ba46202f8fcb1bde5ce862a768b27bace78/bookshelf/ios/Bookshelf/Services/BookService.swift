import Foundation

@MainActor
class BookService: ObservableObject {
    static let shared = BookService()

    @Published var searchResults: [Book] = []
    @Published var searchTotal = 0

    func fetchBooks(shelfId: String) async throws -> [Book] {
        let data: [String: [Book]] = try await APIClient.shared.request("/shelves/\(shelfId)/books")
        return data["books"] ?? []
    }

    func searchBooks(query: String, limit: Int = 20, offset: Int = 0) async throws {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        let result: SearchResult = try await APIClient.shared.request("/books/search?q=\(encoded)&limit=\(limit)&offset=\(offset)")
        searchResults = result.books
        searchTotal = result.total
    }

    func getBook(_ bookId: String) async throws -> Book {
        return try await APIClient.shared.request("/books/\(bookId)")
    }

    func startRecognition(shelfId: String, imageData: Data) async throws -> RecognitionJob {
        return try await APIClient.shared.uploadPhoto("/shelves/\(shelfId)/recognize", imageData: imageData)
    }

    func pollRecognition(shelfId: String, jobId: String) async throws -> RecognitionJob {
        return try await APIClient.shared.request("/shelves/\(shelfId)/recognize/\(jobId)")
    }
}
