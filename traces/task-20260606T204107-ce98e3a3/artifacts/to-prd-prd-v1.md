## Problem Statement
Book owners with hundreds of books across multiple shelves struggle to locate specific books or discover books by topic because physical shelves are not searchable. Digitizing a library manually is too time-consuming. The user needs a mobile app that uses photo-based AI recognition to create a digital replica of their physical bookshelf, enabling search and social features.

## Solution
Bookshelf is a mobile app that lets users photograph their bookshelves and uses AI to automatically recognize books and generate summaries. The digital shelf mirrors the physical layout, allowing users to search for books and see their exact location. Social features enable users to connect based on shelf similarity.

## User Stories
1. As a book owner, I want to take a photo of my bookshelf, so that the app automatically recognizes all books and creates a digital replica.
2. As a user, I want the digital shelf to visually match my physical shelf layout, so that I can easily locate books.
3. As a user, I want to search for a book by title or author, so that I can find its exact position on my shelf.
4. As a user, I want to tap on a book in the digital shelf, so that I can see its summary and details.
5. As a user, I want to view my entire collection across multiple shelves, so that I can browse all my books.
6. As a user, I want to discover other users with similar shelves, so that I can connect and discuss books.
7. As a user, I want to send messages to other users, so that I can communicate about shared interests.
8. As a user, I want to subscribe for $1.99/month, so that I can access all features.
9. As a user, I want to receive notifications when new books are recognized or when I have messages.
10. As a user, I want to manage my subscription, so that I can cancel or renew.

## Implementation Decisions
- **Mobile Platform**: Initial release on iOS using SwiftUI; Android version to follow.
- **AI Recognition**: Use a cloud-based LLM (e.g., GPT-4o) for book recognition from photos. The app sends images to the backend, which processes them and returns recognized book metadata and summaries.
- **Backend**: Node.js/Express with PostgreSQL for user data, shelf layouts, and social features. Use Redis for caching.
- **Shelf Layout**: Store shelf layout as a JSON structure mapping books to positions (row, column, order). The digital shelf renders using a custom view that mimics physical arrangement.
- **Social Features**: Implement shelf similarity using cosine similarity on book genre vectors. Users can opt-in to sharing their shelf profile.
- **Authentication**: Email/password and OAuth (Google, Apple).
- **Subscription**: Use Apple In-App Purchase for iOS; Stripe for future Android.
- **Testing**: Unit tests for backend logic, UI tests for critical flows (photo capture, search, social). Use XCTest for iOS.

## Testing Decisions
- **Good test**: Tests external behavior (e.g., "given a photo of a shelf, the app returns correct book list") not internal implementation.
- **Modules tested**: Photo capture flow, book recognition API, search functionality, social matching algorithm.
- **Prior art**: Follow existing patterns in the codebase for network layer testing (mocking URLSession) and UI testing (XCUITest).

## Out of Scope
- Manual book entry (keyboard input)
- Integration with Goodreads, LibraryThing, or other digital libraries
- E-book or audiobook management
- Physical book purchasing or marketplace
- Advanced analytics or reading tracking beyond shelf management
- Multi-language support (initial release English only)
- Web or desktop versions

## Further Notes
- Privacy: Photos are processed on the server and not stored longer than necessary. Users can delete their shelf data.
- Accuracy threshold: Aim for 90%+ recognition accuracy. If lower, flag uncertain books for user confirmation.
- Open questions: Target platform first (iOS), minimum social feature (shelf sharing + messaging), multilingual support (deferred).