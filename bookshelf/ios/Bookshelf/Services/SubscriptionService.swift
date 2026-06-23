import Foundation
import StoreKit

@MainActor
class SubscriptionService: ObservableObject {
    static let shared = SubscriptionService()

    @Published var isSubscribed = false
    @Published var plan: String = "free"
    @Published var isLoading = false

    private let productId = "com.bookshelf.premium.monthly"

    func fetchStatus() async throws {
        let status: SubscriptionStatus = try await APIClient.shared.request("/subscriptions/status")
        isSubscribed = status.active
        plan = status.plan
    }

    func purchase() async throws {
        // Request products from App Store
        let products = try await Product.products(for: [productId])
        guard let product = products.first else {
            throw APIError.notFound
        }

        // Purchase
        let result = try await product.purchase()
        switch result {
        case .success(let verification):
            // Validate with backend
            if case .verified(let transaction) = verification {
                let receiptData = "" // In production: get from Bundle.main.appStoreReceiptURL
                let _: VerifyReceiptResponse = try await APIClient.shared.request(
                    "/subscriptions/verify",
                    method: "POST",
                    body: VerifyReceiptRequest(receiptData: receiptData)
                )
                isSubscribed = true
                plan = "premium"
                await transaction.finish()
            }
        case .userCancelled:
            throw APIError.validationError("Purchase cancelled")
        case .pending:
            throw APIError.validationError("Purchase pending")
        @unknown default:
            throw APIError.serverError("Unknown purchase result")
        }
    }

    func restore() async throws {
        try await AppStore.sync()
        try await fetchStatus()
    }
}
