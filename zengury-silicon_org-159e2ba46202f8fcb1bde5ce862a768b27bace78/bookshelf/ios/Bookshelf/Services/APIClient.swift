import Foundation

enum APIError: LocalizedError {
    case unauthorized
    case forbidden
    case notFound
    case validationError(String)
    case serverError(String)
    case networkError(Error)
    case decodingError

    var errorDescription: String? {
        switch self {
        case .unauthorized: return "Please sign in again"
        case .forbidden: return "Subscription required"
        case .notFound: return "Not found"
        case .validationError(let m): return m
        case .serverError(let m): return m
        case .networkError(let e): return e.localizedDescription
        case .decodingError: return "Unexpected response"
        }
    }
}

actor APIClient {
    static let shared = APIClient()
    private let baseURL: String
    private var token: String?

    private init() {
        // In production, read from Info.plist or build config
        self.baseURL = ProcessInfo.processInfo.environment["API_BASE_URL"] ?? "http://localhost:3000/api/v1"
    }

    func setToken(_ token: String?) {
        self.token = token
    }

    func request<T: Codable>(_ path: String, method: String = "GET", body: Encodable? = nil) async throws -> T {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(UUID().uuidString, forHTTPHeaderField: "X-Request-Id")

        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        }

        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as! HTTPURLResponse

        if httpResponse.statusCode == 204 {
            // No content — return empty success
            guard let empty = try? JSONDecoder().decode(T.self, from: "{}".data(using: .utf8)!) else {
                throw APIError.decodingError
            }
            return empty
        }

        if httpResponse.statusCode >= 400 {
            if let apiError = try? JSONDecoder().decode(ApiError.self, from: data) {
                switch httpResponse.statusCode {
                case 401: throw APIError.unauthorized
                case 403: throw APIError.forbidden
                case 404: throw APIError.notFound
                case 400: throw APIError.validationError(apiError.error.message)
                default: throw APIError.serverError(apiError.error.message)
                }
            }
            throw APIError.serverError("HTTP \(httpResponse.statusCode)")
        }

        do {
            let wrapper = try JSONDecoder().decode(ApiResponse<T>.self, from: data)
            return wrapper.data
        } catch {
            // Try decoding without wrapper
            do {
                return try JSONDecoder().decode(T.self, from: data)
            } catch {
                throw APIError.decodingError
            }
        }
    }

    func uploadPhoto(_ path: String, imageData: Data, fieldName: String = "image") async throws -> RecognitionJob {
        let url = URL(string: "\(baseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue(UUID().uuidString, forHTTPHeaderField: "X-Request-Id")
        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"shelf.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        let httpResponse = response as! HTTPURLResponse

        if httpResponse.statusCode >= 400 {
            if let apiError = try? JSONDecoder().decode(ApiError.self, from: data) {
                throw APIError.serverError(apiError.error.message)
            }
            throw APIError.serverError("Upload failed")
        }

        do {
            let wrapper = try JSONDecoder().decode(ApiResponse<RecognitionJob>.self, from: data)
            return wrapper.data
        } catch {
            throw APIError.decodingError
        }
    }
}

// Helper to encode any Encodable
struct AnyEncodable: Encodable {
    let value: Encodable
    init(_ value: Encodable) { self.value = value }
    func encode(to encoder: Encoder) throws {
        try value.encode(to: encoder)
    }
}
