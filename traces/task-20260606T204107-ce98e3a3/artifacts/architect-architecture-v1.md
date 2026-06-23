# Bookshelf — Architecture Decision Record

## Architecture Principles (from soul.md)

| Kahn Room | Architectural Translation |
|-----------|--------------------------|
| **Salk — Subtraction** | The system starts as a modular monolith. Nothing is split into a service until it *must* scale independently. The main surface (the photo→shelf→search flow) earns its weight by removing everything else. |
| **Kimbell — Light from arrival** | Design backward from the user's arrival. The user opens the app to find a book. Every component — mobile, API, AI pipeline — exists only to serve that terminus. The light is the book's location on a shelf. |
| **Esherick — Depth reconciles** | The deep module is the Photo Recognition Pipeline. It faces outward to the AI model and inward to the user's shelf view. Its depth (async job queue, retry, confidence scoring) is where the two worlds reconcile — out of the user's sight. |

---

## 1. System Architecture

### Pattern: Modular Monolith

```
┌─────────────────────────────────────────────────────────┐
│                    iOS App (SwiftUI)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ Camera   │ │ Shelf    │ │ Search   │ │ Settings  │ │
│  │ Module   │ │ Renderer │ │ Module   │ │ + IAP     │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘ │
│       └────────────┴────────────┴─────────────┘        │
│                        │                                │
│                   API Client                            │
└────────────────────────┼────────────────────────────────┘
                         │ HTTPS (JWT Bearer)
┌────────────────────────┼────────────────────────────────┐
│              Backend (Node.js/Express)                   │
│                         │                                │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │                 API Gateway                       │   │
│  │  /api/auth  /api/shelves  /api/books  /api/sub   │   │
│  └────┬───────────┬──────────┬──────────┬──────────┘   │
│       │           │          │          │               │
│  ┌────┴───┐ ┌────┴───┐ ┌────┴───┐ ┌────┴──────┐       │
│  │ Auth   │ │ Shelf  │ │ Book   │ │ Subscr-   │       │
│  │ Module │ │ Module │ │ Module │ │ iption    │       │
│  └───┬────┘ └───┬────┘ └───┬────┘ └─────┬─────┘       │
│      └──────────┴──────────┴────────────┘              │
│                        │                                │
│              ┌─────────┴─────────┐                      │
│              │   Data Access      │                     │
│              │   Layer (Knex)     │                     │
│              └─────────┬─────────┘                      │
└────────────────────────┼────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │    PostgreSQL       │
              │  (primary store)    │
              └─────────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                  │
┌──────┴──────┐  ┌───────┴──────┐  ┌───────┴──────┐
│  S3/Object  │  │  Job Queue   │  │  GPT-4o      │
│  Storage    │  │  (BullMQ +   │  │  Vision API  │
│  (photos)   │  │   Redis)     │  │              │
└─────────────┘  └──────────────┘  └──────────────┘
```

**Decision**: Modular monolith, not microservices.
**Rationale**: Team is small (1–3 developers). Domain boundaries are forming. No component needs independent scaling at launch. Modules are separated in code (auth/, shelves/, books/, recognition/, subscription/) with clear interfaces but deployed as a single Node.js process. Extract to services only when a module demonstrates different scaling needs.
**Alternatives rejected**:
- Microservices from day one: operational overhead (service discovery, distributed tracing, inter-service auth) would kill velocity before user #1.
- Serverless (Lambda): cold starts unacceptable for photo upload → recognition flow; vendor lock on AWS.

---

## 2. Mobile Architecture (iOS/SwiftUI)

```
BookshelfApp
├── App/
│   ├── BookshelfApp.swift          // @main, app delegate
│   ├── AppState.swift              // global auth/subscription state
│   └── Navigation.swift            // tab + navigation routing
├── Modules/
│   ├── Camera/
│   │   ├── CameraView.swift        // AVCaptureSession wrapper
│   │   ├── PhotoPreviewView.swift  // post-capture preview + upload
│   │   └── CameraViewModel.swift   // state: idle → capturing → uploading → done
│   ├── Shelf/
│   │   ├── ShelfGridView.swift     // grid layout matching physical positions
│   │   ├── BookCellView.swift      // individual book spine/cover
│   │   ├── BookDetailView.swift    // book summary sheet
│   │   ├── ShelfListView.swift     // multiple shelves
│   │   └── ShelfViewModel.swift
│   ├── Search/
│   │   ├── SearchView.swift        // search bar + results
│   │   ├── SearchResultRow.swift   // result with shelf location hint
│   │   └── SearchViewModel.swift
│   └── Settings/
│       ├── SettingsView.swift      // profile, subscription, logout
│       ├── SubscriptionView.swift  // IAP purchase + management
│       └── SettingsViewModel.swift
├── Services/
│   ├── APIClient.swift             // URLSession wrapper, JWT injection
│   ├── AuthService.swift           // login/register/OAuth
│   ├── ShelfService.swift          // shelf CRUD + recognition trigger
│   ├── BookService.swift           // book search + detail
│   └── SubscriptionService.swift   // StoreKit integration
├── Models/
│   ├── Shelf.swift                 // Codable structs
│   ├── Book.swift
│   ├── User.swift
│   └── RecognitionJob.swift
└── Resources/
    ├── Assets.xcassets
    └── Localizable.strings         // English only for v1
```

**Pattern**: MVVM — Views observe ViewModels via `@Published`; ViewModels call Services; Services wrap APIClient.
**Key Decisions**:
- **No third-party networking library**: URLSession + async/await is sufficient. No Alamofire.
- **No CoreData**: Data is server-authoritative. Local caching via `NSCache` for shelf data only.
- **Photo upload**: Multipart form upload with progress via `URLSessionTaskDelegate`. Max 20MB per photo.
- **Shelf rendering**: Custom `LazyVGrid` with `ScrollView`. Each book cell is tappable. The grid mirrors the physical row × column layout stored on the server. No 3D or ARKit — flat grid with book spine placeholders until covers load.

---

## 3. Backend Module Structure

```
backend/
├── src/
│   ├── index.ts                    // Express app entry, middleware chain
│   ├── config.ts                   // env-based config
│   ├── middleware/
│   │   ├── auth.ts                 // JWT verification
│   │   ├── subscription.ts        // subscription gating
│   │   └── errorHandler.ts        // centralized error → ApiError
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── auth.router.ts     // POST /register, /login, /oauth, /logout
│   │   │   ├── auth.service.ts    // bcrypt, JWT sign/verify, OAuth
│   │   │   └── auth.schema.ts     // Zod validation schemas
│   │   ├── shelves/
│   │   │   ├── shelves.router.ts  // GET/POST/DELETE /shelves
│   │   │   ├── shelves.service.ts
│   │   │   └── shelves.schema.ts
│   │   ├── recognition/
│   │   │   ├── recognition.router.ts  // POST /recognize, GET /recognize/:jobId
│   │   │   ├── recognition.service.ts // queue job, poll status
│   │   │   ├── recognition.worker.ts  // BullMQ worker: call GPT-4o, parse, store
│   │   │   └── gpt4o.client.ts        // OpenAI API wrapper
│   │   ├── books/
│   │   │   ├── books.router.ts    // GET /books, /books/search, /books/:id
│   │   │   ├── books.service.ts
│   │   │   └── books.schema.ts
│   │   └── subscriptions/
│   │       ├── subscriptions.router.ts // POST /verify, GET /status
│   │       ├── subscriptions.service.ts // App Store receipt validation
│   │       └── subscriptions.schema.ts
│   └── db/
│       ├── knex.ts                 // Knex instance
│       ├── migrations/             // timestamped migration files
│       └── seeds/                  // dev seed data
├── tests/
│   ├── auth.test.ts
│   ├── shelves.test.ts
│   ├── recognition.test.ts
│   └── books.test.ts
├── knexfile.ts
├── package.json
└── tsconfig.json
```

**Module boundary rule**: Each module exposes only its `router` and `service`. Modules import other modules' services, never their internal files. This keeps the monolith modular and extraction-friendly.

---

## 4. Data Model

```sql
-- Users
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT,                          -- NULL for OAuth-only users
  name          TEXT NOT NULL,
  oauth_provider TEXT,                         -- 'google' | 'apple' | NULL
  oauth_id      TEXT,                          -- OAuth provider's user ID
  share_shelf   BOOLEAN DEFAULT FALSE,         -- opt-in for future social
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Shelves — one per physical bookshelf
CREATE TABLE shelves (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,                 -- "Living Room Left"
  row_count     INTEGER NOT NULL CHECK (row_count BETWEEN 1 AND 10),
  column_count  INTEGER NOT NULL CHECK (column_count BETWEEN 1 AND 20),
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shelves_user ON shelves(user_id);

-- Books — recognized from a shelf photo
CREATE TABLE books (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shelf_id      UUID NOT NULL REFERENCES shelves(id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  author        TEXT NOT NULL DEFAULT 'Unknown',
  summary       TEXT,                          -- AI-generated, max 500 chars
  isbn          TEXT,                          -- when recognized
  cover_url     TEXT,                          -- S3 URL for book cover
  position_row  INTEGER NOT NULL,              -- 1-based
  position_col  INTEGER NOT NULL,              -- 1-based
  confidence    REAL DEFAULT 1.0,              -- AI recognition confidence 0-1
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_books_shelf ON books(shelf_id);
CREATE INDEX idx_books_user_search ON books(shelf_id, title, author);

-- Use PostgreSQL full-text search for book search
CREATE INDEX idx_books_fts ON books USING GIN(
  to_tsvector('english', coalesce(title,'') || ' ' || coalesce(author,''))
);

-- Recognition jobs — async photo processing
CREATE TABLE recognition_jobs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  shelf_id      UUID NOT NULL REFERENCES shelves(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  photo_key     TEXT NOT NULL,                 -- S3 object key
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','processing','completed','failed')),
  error_message TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recognition_jobs_shelf ON recognition_jobs(shelf_id);

-- Subscriptions
CREATE TABLE subscriptions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  status          TEXT NOT NULL DEFAULT 'inactive'
                  CHECK (status IN ('active','inactive','expired','grace_period')),
  plan            TEXT NOT NULL DEFAULT 'free'
                  CHECK (plan IN ('free','premium')),
  original_transaction_id TEXT,               -- App Store original_transaction_id
  latest_receipt  TEXT,                       -- base64 encoded
  expires_at      TIMESTAMPTZ,
  will_renew      BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**Key decisions**:
- **UUIDs not auto-increment**: avoids enumeration attacks, works for future sharding.
- **position_row/col 1-based**: matches user intuition ("first shelf, third book").
- **PostgreSQL FTS not Elasticsearch**: sufficient for v1 scale; no additional infrastructure.
- **confidence field**: books below 0.7 confidence are flagged for user confirmation in the UI.
- **No genres/tags table yet**: deferred. When social features arrive, add with migration.

---

## 5. AI Recognition Pipeline (the deep module — Esherick)

```
User takes photo
       │
       ▼
┌─────────────────┐
│  iOS Camera      │  JPEG, max 20MB
│  → multipart     │
│    upload         │
└────────┬────────┘
         │ POST /api/shelves/:id/recognize
         ▼
┌─────────────────┐
│  API Gateway     │  validate JWT + subscription
│  → store photo   │
│    in S3          │
│  → create job     │
└────────┬────────┘
         │
    ┌────┴────┐
    │  Redis   │  BullMQ job queued
    │  Queue   │
    └────┬────┘
         │
         ▼
┌──────────────────┐
│  Recognition      │  BullMQ Worker
│  Worker           │
│                   │
│  1. Download      │
│     photo from S3 │
│  2. Resize to     │
│     2048px max    │
│  3. Send to       │
│     GPT-4o Vision │
│  4. Parse JSON    │
│     response      │
│  5. Store books   │
│     in PostgreSQL │
│  6. Update job    │
│     status        │
└──────────────────┘
         │
         ▼
   GET /api/shelves/:id/recognize/:jobId
   → client polls until status=completed
```

**GPT-4o Vision prompt contract**:
```json
{
  "model": "gpt-4o",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "Identify every book in this bookshelf photo. For each book, return: title, author, row number (1=top), column number (1=left). Generate a 2-3 sentence summary of each book's content. Format as JSON array."},
      {"type": "image_url", "image_url": {"url": "<presigned S3 URL>"}}
    ]
  }],
  "response_format": {"type": "json_object"}
}
```

**Expected response**:
```json
{
  "books": [
    {"title": "The Design of Everyday Things", "author": "Don Norman", "row": 1, "column": 1, "summary": "Explores how good design makes products understandable and usable..."},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "row": 1, "column": 2, "summary": "Examines the two systems of human thought..."}
  ]
}
```

**Failure handling**:
- GPT-4o timeout (30s): retry once; if still fails, mark job `failed`.
- Unparseable response: mark job `failed` with `error_message`.
- Partial recognition (some books missing): store recognized books; flag shelf as `needs_review`. UI shows "X books recognized, Y uncertain — tap to confirm."
- Confidence below 0.7: book is stored but marked for user review.

**Cost estimate** (GPT-4o Vision):
- ~$0.005–0.01 per shelf photo (at current pricing)
- 100 shelves scanned = ~$1.00
- Well within $1.99/month subscription margin

---

## 6. Authentication & Authorization

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Email/   │     │ Google   │     │ Apple    │
│ Password │     │ OAuth    │     │ Sign In  │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      │ POST /api/auth/*
                      ▼
              ┌───────────────┐
              │ Auth Service   │
              │ → bcrypt hash  │
              │ → OAuth verify │
              │ → JWT sign     │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ JWT Token      │
              │ {sub, email,   │
              │  sub_active}   │
              │ 24h expiry     │
              └───────────────┘
```

**JWT Payload**:
```typescript
interface JwtPayload {
  sub: string;        // user UUID
  email: string;
  sub_active: boolean; // subscription status (checked on every request)
  iat: number;
  exp: number;
}
```

**Subscription gating middleware**: On every request, if `sub_active === false`:
- Allow: auth endpoints, GET /subscriptions/status, POST /subscriptions/verify
- Allow but limited: 1 shelf creation, 1 recognition job (feature gating)
- Block: additional shelves, social features (when implemented)

**Apple Sign In**: Mandatory for App Store compliance. Uses `ASAuthorizationAppleIDProvider` on iOS. Backend verifies `identityToken` with Apple's `/auth/keys` endpoint. Users who sign in with Apple may not have an email visible — backend stores `apple_private_email` from the token.

---

## 7. Deployment Architecture

```
                     ┌──────────────┐
                     │   Apple CDN  │  App Store distribution
                     └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │  iOS App     │  User's device
                     └──────┬───────┘
                            │ HTTPS
                     ┌──────┴───────┐
                     │  Render /    │  PaaS (or single VPS)
                     │  Fly.io      │
                     │              │
                     │  ┌────────┐  │
                     │  │ Express│  │  Node.js process
                     │  │ API    │  │  (single instance)
                     │  └───┬────┘  │
                     │      │       │
                     │  ┌───┴────┐  │
                     │  │ Redis  │  │  BullMQ + session cache
                     │  └────────┘  │  (managed or sidecar)
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
       ┌──────┴──────┐ ┌───┴────┐ ┌─────┴──────┐
       │ PostgreSQL  │ │  S3    │ │  OpenAI    │
       │ (managed)   │ │ (photos│ │  GPT-4o    │
       │             │ │  only) │ │  Vision API │
       └─────────────┘ └────────┘ └────────────┘
```

**Decision**: Render or Fly.io for v1. Single $25–50/month instance runs Express + Redis sidecar. Managed PostgreSQL ($15–20/month). S3-compatible storage ($5–10/month estimated).
**Total infra cost estimate**: $50–85/month at launch.
**Alternatives rejected**:
- AWS ECS/EKS: overkill; operational complexity too high
- Vercel Edge Functions: not suitable for long-running photo processing jobs
- Heroku: acceptable alternative but higher cost at scale

---

## 8. API Versioning & Evolution

- **URL prefix**: `/api/v1/` (explicit in URL, not header-based)
- **Deprecation**: Old versions supported for 6 months after v2 release
- **Breaking change rule**: New field additions are non-breaking. Field removal or type change requires new version.
- **Migration strategy for v2 social features**: New endpoints added at `/api/v2/`. v1 endpoints unchanged. Mobile app gates v2 endpoints behind a feature flag until user base validates social demand.

---

## 9. Security Boundaries

| Boundary | Mechanism |
|----------|-----------|
| User → API | HTTPS only; JWT in Authorization header; 24h expiry |
| API → PostgreSQL | TLS connection; credentials via env vars only |
| API → S3 | Presigned URLs (5 min expiry) for upload; server-side access for download |
| API → GPT-4o | API key via env var; requests logged but photos not stored by OpenAI (per API terms) |
| API → App Store | Server-to-server receipt validation; no client-side trust |
| Photo storage | S3 bucket with server-side encryption; lifecycle policy deletes photos after 30 days |
| User data deletion | Cascade delete: user → shelves → books → recognition_jobs; S3 objects deleted async |

---

## 10. What We Are Explicitly NOT Building (v1)

Per product-vision-anchor `out_of_scope_forever` and scope-prosecutor DEFER:

- ❌ No real-time messaging (WebSocket not deployed)
- ❌ No shelf similarity matching engine
- ❌ No push notification infrastructure (APNs certificates deferred)
- ❌ No multi-language support
- ❌ No Android app
- ❌ No admin dashboard
- ❌ No analytics beyond server logs
- ❌ No Redis Cluster (single Redis instance)
- ❌ No read replicas
- ❌ No CDN for book covers (S3 direct)

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Designed the complete system architecture for Bookshelf v1 as a modular
    monolith: iOS SwiftUI app + Node.js/Express backend + PostgreSQL + Redis
    (BullMQ) + GPT-4o Vision pipeline + S3 photo storage. Documented data model
    (5 tables), module boundaries, AI recognition pipeline contract, auth flow,
    deployment topology, security boundaries, and explicit anti-scope.
  key_decisions:
    - decision: "Modular monolith, not microservices"
      rationale: >
        Team is 1–3 developers. No component needs independent scaling at
        launch. Code is separated into modules (auth, shelves, books,
        recognition, subscriptions) with clear interfaces. Extract to services
        only when scaling demands it.
    - decision: "PostgreSQL full-text search, not Elasticsearch"
      rationale: >
        Sufficient for v1 scale (thousands of books per user, hundreds of
        users). No additional infrastructure. Can migrate to Elasticsearch if
        search becomes a bottleneck.
    - decision: "BullMQ + Redis for async recognition jobs"
      rationale: >
        GPT-4o Vision may take 5–15 seconds per shelf. Async job pattern
        prevents HTTP timeouts. BullMQ provides retry, monitoring, and
        concurrency control. Redis is also used for session caching.
    - decision: "1-based row/column positions mirroring physical shelf layout"
      rationale: >
        Users think in "third shelf from top, fifth book from left." 1-based
        numbering matches intuition. The shelf grid renderer maps these
        directly to SwiftUI LazyVGrid positions.
    - decision: "Presigned S3 URLs for photo upload, server-side GPT-4o proxy"
      rationale: >
        Mobile app never holds S3 or OpenAI credentials. Backend generates
        presigned upload URLs (5 min TTL). GPT-4o calls are server-side only,
        with the photo sent as a presigned URL (not uploaded to OpenAI).
  handoff_focus:
    - "UX Designer: shelf grid mirrors physical layout — design the grid view, book cell, and search highlight that make the user feel 'in command'"
    - "Senior Engineer (Backend): implement modules in order: auth → shelves → recognition → books → subscriptions"
    - "Senior Engineer (iOS): implement Camera → Shelf Grid → Search → Settings"
    - "Prototype: validate GPT-4o Vision recognition accuracy on real shelf photos before committing to the pipeline"
    - "Database Engineer: schema in section 4 is the authoritative data model"
  open_questions:
    - "What is the exact GPT-4o Vision API latency for shelf photos? (5–15s estimate)"
    - "What S3-compatible provider? (AWS S3, Cloudflare R2, Backblaze B2)"
    - "Should Redis be managed (Upstash) or self-hosted sidecar?"
    - "What is the target iOS minimum version? (iOS 17+ recommended for SwiftUI maturity)"
  known_constraints:
    - "iOS only for v1"
    - "Photo-based input only"
    - "English only"
    - "$1.99/month subscription"
    - "No social features"
    - "Single backend instance (scale vertically first)"
  confidence_differential: 0.10
  dissent_if_alone: null
```
