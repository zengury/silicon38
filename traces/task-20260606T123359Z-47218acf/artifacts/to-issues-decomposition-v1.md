## Issues

### Issue 1: Photo Capture and Upload
- **Title**: Photo Capture and Upload
- **Description**: Implement the photo capture flow using the device camera. User takes a photo of a bookshelf, the app displays a preview, and uploads the image to the backend for processing. The upload should show progress and handle errors gracefully.
- **Acceptance Criteria**:
  - [ ] User can open camera from the app and take a photo.
  - [ ] Photo preview is shown before upload.
  - [ ] Upload progress indicator is displayed.
  - [ ] Upload completes successfully and returns a job ID.
  - [ ] Error handling for network failures and camera permissions.
- **Estimated Size**: M
- **Blocked By**: None - can start immediately

### Issue 2: Backend Image Processing and Book Recognition
- **Title**: Backend Image Processing and Book Recognition
- **Description**: Create a backend endpoint that receives uploaded images, sends them to an AI service (e.g., GPT-4o) for book recognition, and returns recognized books with metadata (title, author, summary) and their positions on the shelf. Store the results in the database.
- **Acceptance Criteria**:
  - [ ] POST endpoint `/api/shelves/recognize` accepts image and returns list of books with positions.
  - [ ] Integration with AI service for recognition.
  - [ ] Recognized books are stored in the database with shelf ID and position.
  - [ ] Response includes book metadata (title, author, summary).
  - [ ] Error handling for AI service failures.
- **Estimated Size**: L
- **Blocked By**: Issue 1

### Issue 3: Digital Shelf Rendering
- **Title**: Digital Shelf Rendering
- **Description**: Render the digital shelf on the mobile app to visually match the physical shelf layout. Display books as thumbnails in rows and columns according to their stored positions. Support multiple shelves per user.
- **Acceptance Criteria**:
  - [ ] Shelf view displays books in grid layout matching stored positions.
  - [ ] Each book shows cover thumbnail (if available) or placeholder.
  - [ ] User can scroll through shelves.
  - [ ] Tapping a book shows its details (title, author, summary).
  - [ ] Multiple shelves are displayed as a list or scrollable collection.
- **Estimated Size**: M
- **Blocked By**: Issue 2

### Issue 4: Search Books on Shelf
- **Title**: Search Books on Shelf
- **Description**: Implement search functionality that allows users to search for books by title or author across all their shelves. Search results highlight the book's position on the shelf.
- **Acceptance Criteria**:
  - [ ] Search bar is available on the shelf view.
  - [ ] Search returns matching books from user's collection.
  - [ ] Tapping a search result navigates to the shelf and highlights the book.
  - [ ] Search is case-insensitive and supports partial matches.
- **Estimated Size**: M
- **Blocked By**: Issue 3

### Issue 5: User Authentication (Email/Password + OAuth)
- **Title**: User Authentication
- **Description**: Implement user registration and login using email/password and OAuth (Google, Apple). Include session management and token-based authentication for API calls.
- **Acceptance Criteria**:
  - [ ] User can sign up with email and password.
  - [ ] User can log in with email and password.
  - [ ] User can sign in with Google and Apple OAuth.
  - [ ] Session tokens are stored securely and used for API requests.
  - [ ] Logout clears session.
- **Estimated Size**: M
- **Blocked By**: None - can start immediately

### Issue 6: Subscription Management (iOS In-App Purchase)
- **Title**: Subscription Management (iOS In-App Purchase)
- **Description**: Implement $1.99/month subscription using Apple In-App Purchase. Handle purchase flow, receipt validation, and subscription status management. Restrict features for non-subscribers.
- **Acceptance Criteria**:
  - [ ] Subscription offer is displayed to non-subscribers.
  - [ ] User can purchase subscription via App Store.
  - [ ] Receipt is validated on backend.
  - [ ] Subscription status is checked before allowing access to features.
  - [ ] User can manage subscription (restore, cancel).
- **Estimated Size**: L
- **Blocked By**: Issue 5

### Issue 7: Social Feature - Shelf Similarity Matching
- **Title**: Shelf Similarity Matching
- **Description**: Implement backend algorithm to compute similarity between users' shelves based on book genres. Provide an endpoint to return a list of similar users. Users can opt-in to sharing their shelf profile.
- **Acceptance Criteria**:
  - [ ] Backend computes cosine similarity on genre vectors.
  - [ ] GET endpoint `/api/users/similar` returns list of similar users.
  - [ ] Users can opt-in/out of shelf sharing.
  - [ ] Similarity results are cached and updated periodically.
- **Estimated Size**: M
- **Blocked By**: Issue 2

### Issue 8: Social Feature - Messaging
- **Title**: Messaging Between Users
- **Description**: Implement a messaging system that allows users to send and receive messages. Include a conversation list, real-time notifications, and message history.
- **Acceptance Criteria**:
  - [ ] User can start a conversation with another user.
  - [ ] Messages are sent and received in real-time (WebSocket or polling).
  - [ ] Conversation list shows recent messages.
  - [ ] Push notifications for new messages.
  - [ ] Message history is persisted.
- **Estimated Size**: L
- **Blocked By**: Issue 7

### Issue 9: Notifications
- **Title**: Notifications
- **Description**: Implement push notifications for new book recognition completions and new messages. Allow users to manage notification preferences.
- **Acceptance Criteria**:
  - [ ] User receives push notification when book recognition is complete.
  - [ ] User receives push notification for new messages.
  - [ ] Notification preferences can be toggled in settings.
  - [ ] Tapping notification opens relevant screen.
- **Estimated Size**: S
- **Blocked By**: Issue 2, Issue 8

### Issue 10: Subscription Management UI and Feature Gating
- **Title**: Subscription Management UI and Feature Gating
- **Description**: Build UI for subscription management (view plan, cancel, restore) and implement feature gating so that non-subscribers see limited functionality (e.g., can only scan one shelf, no social features).
- **Acceptance Criteria**:
  - [ ] Subscription settings screen shows current plan and options.
  - [ ] Non-subscribers see upgrade prompts.
  - [ ] Feature gating restricts access to paid features.
  - [ ] Restore purchases works correctly.
- **Estimated Size**: M
- **Blocked By**: Issue 6

## Completion Report

```yaml
completion_report:
  what_was_done: Decomposed the Bookshelf app PRD into 10 independent issues with acceptance criteria, estimated sizes, and dependency relationships.
  key_decisions:
    - decision: Split photo capture and backend recognition into separate issues to allow parallel work on mobile and backend.
      rationale: Mobile and backend can be developed concurrently after the API contract is defined.
    - decision: Authentication is a separate issue not blocked by others.
      rationale: Auth is foundational but can be built independently and integrated later.
    - decision: Social features are split into similarity matching and messaging.
      rationale: Each is independently deliverable; similarity can be built without messaging.
    - decision: Subscription management UI is separate from IAP purchase logic.
      rationale: Backend receipt validation and frontend gating can be built after purchase flow.
  handoff_focus:
    - Implement issues in dependency order: start with Issues 1, 5, and optionally 2 in parallel.
    - Define API contract between Issue 1 and Issue 2 early.
  open_questions:
    - Should we use WebSocket or polling for messaging? (Deferred to implementation)
    - What is the exact AI service endpoint and pricing? (Needs research)
  known_constraints:
    - iOS only for initial release.
    - No manual book entry.
    - Subscription required for full features.
  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: null
```

## Context Compression Report

```yaml
context_compression_report:
  input_scope:
    artifacts_read:
      - to-prd-prd-v1
    handoffs_read:
      - handoffs/to-prd→to-issues-20260606-123438.yaml
  retained_context:
    decisions:
      - statement: 'App name: Bookshelf'
        source: semantic_node_executor
      - statement: 'Core feature: photo-based AI recognition to digitize physical bookshelves'
        source: semantic_node_executor
      - statement: 'Monetization: $1.99/month subscription'
        source: semantic_node_executor
      - statement: 'Social features: shelf similarity matching and communication'
        source: semantic_node_executor
      - statement: 'Initial platform: iOS using SwiftUI'
        source: to-prd-prd-v1
      - statement: 'AI recognition: cloud-based LLM (GPT-4o)'
        source: to-prd-prd-v1
      - statement: 'Backend: Node.js/Express with PostgreSQL'
        source: to-prd-prd-v1
      - statement: 'Authentication: email/password and OAuth (Google, Apple)'
        source: to-prd-prd-v1
      - statement: 'Subscription: Apple In-App Purchase for iOS'
        source: to-prd-prd-v1
    constraints:
      - statement: Must be mobile app (iOS/Android)
        source: semantic_node_executor
      - statement: No manual book entry
        source: semantic_node_executor
      - statement: Digital shelf must mirror physical layout
        source: semantic_node_executor
      - statement: Initial release iOS only
        source: to-prd-prd-v1
      - statement: English only for initial release
        source: to-prd-prd-v1
    assumptions:
      - statement: AI can accurately recognize books from photos and summarize content
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: Users have multiple shelves with books
        source: semantic_node_executor
        risk: Assumption may need review.
      - statement: Users are willing to pay $1.99/month
        source: semantic_node_executor
        risk: Assumption may need review.
    open_questions:
      - statement: Target platform first? (iOS decided)
        source: semantic_node_executor
        owner: runtime
      - statement: Accuracy threshold for recognition? (90%+)
        source: semantic_node_executor
        owner: runtime
      - statement: Multilingual support? (deferred)
        source: semantic_node_executor
        owner: runtime
      - statement: Minimum social feature? (shelf sharing + messaging)
        source: semantic_node_executor
        owner: runtime
      - statement: Privacy concerns?
        source: semantic_node_executor
        owner: runtime
  omitted_context:
    - source: Detailed technical architecture
      reason: background_only
    - source: Specific AI model selection details
      reason: background_only
    - source: Exact UI mockups
      reason: background_only
    - source: Marketing strategy
      reason: background_only
    - source: Out of scope items
      reason: not needed for issue decomposition
  compression_rationale:
    method: Extracted key decisions, constraints, assumptions, and open questions from PRD and handoff. Omitted implementation details not needed for issue decomposition.
    loss_notes: []
  quality_checks:
    - name: All issues have acceptance criteria
      passed: true
    - name: Dependency graph is acyclic
      passed: true
    - name: No issue is blocked by an unspecified dependency
      passed: true
    - name: Each issue is independently completable
      passed: true
```