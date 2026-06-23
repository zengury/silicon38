## Plain-Language Explanation

Bookshelf is a phone app. User takes photo of bookshelf. App uses AI to see each book, remember title, author, summary. App shows digital copy of shelf that looks same as real shelf. User can search for book, app shows where it sits. Users can see other users with similar shelves, chat with them. Cost: $1.99/month.

## Minimum Viable Version

1. User opens app, takes photo of one shelf.
2. App sends photo to cloud AI. AI returns list of books with titles, authors, positions.
3. App shows shelf as grid of book spines. Each book tappable for summary.
4. User can search by title. App highlights book on shelf.
5. User can share shelf link. No matching, no chat. Just link sharing.
6. Payment: $1.99/month via app store.

That's it. No social matching, no messaging, no multi-shelf management, no notifications.

## Complexity Assessment

### Justified Complexity
- AI photo recognition: core feature, can't skip.
- Cloud backend: needed for AI processing and data sync.
- Subscription payment: required for revenue.

### Unnecessary Complexity
- Social matching (shelf similarity): not needed for MVP. Users can share links manually.
- In-app messaging: not needed. Users can exchange contact info outside app.
- Multi-shelf layout mirroring: single shelf photo is enough. Multiple shelves can be added later.
- Notifications: not needed for MVP.
- OAuth: email/password is simpler for MVP.
- Redis caching: not needed at low scale.
- Cosine similarity vectors: overkill. Simple tag overlap works.

## Minimum Viable Version Named

"Single-Shelf Photo Search"

## Complexity Tradeoff Named

"Social features add 3x complexity for uncertain engagement. Drop until user base > 10k."