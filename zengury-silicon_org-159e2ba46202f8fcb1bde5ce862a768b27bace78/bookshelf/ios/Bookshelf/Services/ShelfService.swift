import Foundation

@MainActor
class ShelfService: ObservableObject {
    static let shared = ShelfService()

    @Published var shelves: [Shelf] = []

    func fetchShelves() async throws {
        let data: [String: [Shelf]] = try await APIClient.shared.request("/shelves")
        shelves = data["shelves"] ?? []
    }

    func createShelf(name: String?, rowCount: Int, columnCount: Int) async throws -> Shelf {
        let req = CreateShelfRequest(name: name, rowCount: rowCount, columnCount: columnCount)
        let shelf: Shelf = try await APIClient.shared.request("/shelves", method: "POST", body: req)
        shelves.insert(shelf, at: 0)
        return shelf
    }

    func deleteShelf(_ shelfId: String) async throws {
        let _: EmptyResponse = try await APIClient.shared.request("/shelves/\(shelfId)", method: "DELETE")
        shelves.removeAll { $0.id == shelfId }
    }
}

struct EmptyResponse: Codable {}
