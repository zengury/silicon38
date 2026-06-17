# Bookshelf iOS App

Your physical bookshelf, instantly digital.

## Setup

1. Open `Bookshelf.xcodeproj` in Xcode 16+
2. Set the development team in Signing & Capabilities
3. Configure `API_BASE_URL` in Build Settings (or set it in the scheme environment)
4. Build and run on iOS 17+ simulator or device

## Architecture

```
Bookshelf/
├── App/
│   ├── BookshelfApp.swift      # @main entry point
│   ├── AppState.swift           # Global state (auth, sub, navigation)
│   └── MainTabView.swift        # 3-tab layout
├── Models/
│   └── Models.swift             # All Codable types
├── Services/
│   ├── APIClient.swift          # Generic HTTP client + multipart upload
│   ├── AuthService.swift        # Login/register/OAuth
│   ├── ShelfService.swift       # Shelf CRUD
│   ├── BookService.swift        # Search + recognition
│   └── SubscriptionService.swift # StoreKit integration
├── Modules/
│   ├── Onboarding/
│   │   ├── OnboardingView.swift  # 3-card onboarding
│   │   ├── AuthView.swift        # Email/password + Apple Sign In
│   │   └── PaywallView.swift     # $1.99/month subscription
│   ├── Camera/
│   │   └── CameraView.swift      # Full camera flow (capture → preview → upload → process → done)
│   ├── Shelf/
│   │   ├── ShelfListView.swift   # Home screen — list of shelves
│   │   ├── ShelfDetailView.swift # Shelf grid + book detail sheet
│   │   └── NewShelfView.swift    # 2-step creation wizard
│   ├── Search/
│   │   └── SearchView.swift      # Full-text search with location results
│   └── Settings/
│       └── ProfileView.swift     # User profile + subscription management
└── Resources/
    └── Info.plist
```

## Design Principles (from soul.md)

- **Salk (Subtraction)**: 3 tabs only. Every screen does one thing. No decorative UI.
- **Kimbell (Light from arrival)**: The user arrives to find a book. Everything serves that terminus.
- **Esherick (Depth hidden)**: The AI recognition pipeline is invisible. The user only sees shelves appear.

## Key UX Decisions

- Search results **always** show shelf name + position (Row X, Col Y)
- Shelf grid mirrors physical layout 1:1 (LazyVGrid with row × column positions)
- Confidence ⚠️ badge on any book below 0.7 AI confidence
- Camera has shelf alignment guide overlay
- Onboarding is 3 cards, skippable
