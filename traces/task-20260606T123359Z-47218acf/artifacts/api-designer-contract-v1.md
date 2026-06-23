{
  "role": "api-designer",
  "artifact_type": "contract",
  "artifact_extension": "ts",
  "artifact_body": "// ============================================================
// Bookshelf API Contract
// Backend: Node.js/Express with TypeScript
// ============================================================

// --- Common Types ---

interface ApiResponse<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string }>;
  };
  meta: {
    requestId: string;
    timestamp: string;
  };
}

// --- Auth ---

// POST /api/auth/register
interface RegisterRequest {
  email: string; // valid email, max 255 chars
  password: string; // min 8 chars, must contain uppercase, lowercase, number
  name: string; // min 1, max 100 chars
}
interface RegisterResponse {
  userId: string;
  token: string; // JWT
  expiresIn: number; // seconds
}

// POST /api/auth/login
interface LoginRequest {
  email: string;
  password: string;
}
interface LoginResponse {
  userId: string;
  token: string;
  expiresIn: number;
}

// POST /api/auth/oauth
interface OAuthRequest {
  provider: 'google' | 'apple';
  idToken: string; // OAuth ID token
}
interface OAuthResponse {
  userId: string;
  token: string;
  expiresIn: number;
  isNewUser: boolean;
}

// POST /api/auth/logout
// Headers: Authorization: Bearer <token>
// Response: 204 No Content

// --- Shelves ---

// GET /api/shelves
interface GetShelvesResponse {
  shelves: Array<{
    id: string;
    name: string; // user-defined or auto-generated
    rowCount: number;
    columnCount: number;
    createdAt: string; // ISO 8601
    updatedAt: string;
  }>;
}

// POST /api/shelves
interface CreateShelfRequest {
  name?: string; // optional, max 100 chars
  rowCount: number; // 1-10
  columnCount: number; // 1-20
}
interface CreateShelfResponse {
  id: string;
  name: string;
  rowCount: number;
  columnCount: number;
  createdAt: string;
}

// DELETE /api/shelves/:shelfId
// Response: 204 No Content

// --- Recognition ---

// POST /api/shelves/:shelfId/recognize
// Content-Type: multipart/form-data
interface RecognizeRequest {
  image: File; // JPEG/PNG, max 20MB
}
interface RecognizeResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

// GET /api/shelves/:shelfId/recognize/:jobId
interface GetRecognitionJobResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: {
    books: Array<{
      id: string;
      title: string;
      author: string;
      summary: string; // AI-generated, max 500 chars
      position: {
        row: number; // 1-based
        column: number; // 1-based
      };
      isbn?: string;
      coverUrl?: string;
    }>;
  };
  error?: string;
}

// --- Books ---

// GET /api/shelves/:shelfId/books
interface GetBooksResponse {
  books: Array<{
    id: string;
    title: string;
    author: string;
    summary: string;
    position: { row: number; column: number };
    isbn?: string;
    coverUrl?: string;
    createdAt: string;
  }>;
}

// GET /api/books/search?q=<query>&limit=20&offset=0
interface SearchBooksResponse {
  books: Array<{
    id: string;
    title: string;
    author: string;
    shelfId: string;
    shelfName: string;
    position: { row: number; column: number };
    coverUrl?: string;
  }>;
  total: number;
}

// GET /api/books/:bookId
interface GetBookResponse {
  id: string;
  title: string;
  author: string;
  summary: string;
  isbn?: string;
  coverUrl?: string;
  shelfId: string;
  position: { row: number; column: number };
  createdAt: string;
}

// --- Social ---

// GET /api/users/similar?limit=10
interface GetSimilarUsersResponse {
  users: Array<{
    userId: string;
    name: string;
    similarityScore: number; // 0.0 - 1.0
    sharedBookCount: number;
  }>;
}

// POST /api/users/settings
interface UpdateUserSettingsRequest {
  shareShelf: boolean; // opt-in for similarity matching
}
interface UpdateUserSettingsResponse {
  shareShelf: boolean;
}

// --- Messaging ---

// GET /api/conversations
interface GetConversationsResponse {
  conversations: Array<{
    id: string;
    otherUserId: string;
    otherUserName: string;
    lastMessage: {
      text: string;
      senderId: string;
      createdAt: string;
    };
    unreadCount: number;
  }>;
}

// POST /api/conversations
interface CreateConversationRequest {
  userId: string;
}
interface CreateConversationResponse {
  id: string;
}

// GET /api/conversations/:conversationId/messages?limit=50&before=<messageId>
interface GetMessagesResponse {
  messages: Array<{
    id: string;
    senderId: string;
    text: string;
    createdAt: string;
  }>;
}

// POST /api/conversations/:conversationId/messages
interface SendMessageRequest {
  text: string; // max 2000 chars
}
interface SendMessageResponse {
  id: string;
  createdAt: string;
}

// WebSocket /ws?token=<jwt>
// Events:
// - message: { conversationId: string, message: { id, senderId, text, createdAt } }
// - recognition_complete: { shelfId: string, jobId: string }

// --- Subscriptions ---

// POST /api/subscriptions/verify
interface VerifyReceiptRequest {
  receiptData: string; // base64-encoded App Store receipt
}
interface VerifyReceiptResponse {
  valid: boolean;
  expiresAt: string; // ISO 8601
}

// GET /api/subscriptions/status
interface GetSubscriptionStatusResponse {
  active: boolean;
  plan: 'free' | 'premium';
  expiresAt?: string;
  willRenew: boolean;
}

// --- Notifications ---

// GET /api/notifications?limit=20&offset=0
interface GetNotificationsResponse {
  notifications: Array<{
    id: string;
    type: 'recognition_complete' | 'new_message' | 'similar_user';
    title: string;
    body: string;
    data?: Record<string, string>;
    read: boolean;
    createdAt: string;
  }>;
  total: number;
}

// POST /api/notifications/:notificationId/read
// Response: 204 No Content

// PUT /api/users/notification-settings
interface UpdateNotificationSettingsRequest {
  pushEnabled: boolean;
  recognitionComplete: boolean;
  newMessage: boolean;
  similarUser: boolean;
}
interface UpdateNotificationSettingsResponse {
  pushEnabled: boolean;
  recognitionComplete: boolean;
  newMessage: boolean;
  similarUser: boolean;
}

// --- Error Codes ---
// 400 VALIDATION_ERROR - Request body/params invalid
// 401 UNAUTHORIZED - Missing or invalid token
// 403 FORBIDDEN - Insufficient permissions (e.g., not subscribed)
// 404 NOT_FOUND - Resource not found
// 409 CONFLICT - Duplicate resource
// 429 RATE_LIMITED - Too many requests
// 500 INTERNAL_ERROR - Server error

// --- Versioning ---
// All endpoints are versioned via URL prefix /api/v1/ (omitted for brevity).
// Breaking changes will be introduced in new versions; old versions deprecated with 6 months notice.
",
  "context_report": {
    "context_compression_report": {
      "input_scope": {
        "artifacts_read": [
          "to-issues-decomposition-v1"
        ],
        "handoffs_read": [
          "handoffs/to-issues→api-designer-20260606-123516.yaml"
        ]
      },
      "retained_context": {
        "decisions": [
          {
            "statement": "App name: Bookshelf",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Core feature: photo-based AI recognition to digitize physical bookshelves",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Monetization: $1.99/month subscription",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Social features: shelf similarity matching and communication",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Initial platform: iOS using SwiftUI",
            "source": "to-prd-prd-v1"
          },
          {
            "statement": "AI recognition: cloud-based LLM (GPT-4o)",
            "source": "to-prd-prd-v1"
          },
          {
            "statement": "Backend: Node.js/Express with PostgreSQL",
            "source": "to-prd-prd-v1"
          },
          {
            "statement": "Authentication: email/password and OAuth (Google, Apple)",
            "source": "to-prd-prd-v1"
          },
          {
            "statement": "Subscription: Apple In-App Purchase for iOS",
            "source": "to-prd-prd-v1"
          }
        ],
        "constraints": [
          {
            "statement": "Must be mobile app (iOS/Android)",
            "source": "semantic_node_executor"
          },
          {
            "statement": "No manual book entry",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Digital shelf must mirror physical layout",
            "source": "semantic_node_executor"
          },
          {
            "statement": "Initial release iOS only",
            "source": "to-prd-prd-v1"
          },
          {
            "statement": "English only for initial release",
            "source": "to-prd-prd-v1"
          }
        ],
        "assumptions": [
          {
            "statement": "AI can accurately recognize books from photos and summarize content",
            "source": "semantic_node_executor",
            "risk": "Assumption may need review."
          },
          {
            "statement": "Users have multiple shelves with books",
            "source": "semantic_node_executor",
            "risk": "Assumption may need review."
          },
          {
            "statement": "Users are willing to pay $1.99/month",
            "source": "semantic_node_executor",
            "risk": "Assumption may need review."
          }
        ],
        "open_questions": [
          {
            "statement": "Target platform first? (iOS decided)",
            "source": "semantic_node_executor",
            "owner": "runtime"
          },
          {
            "statement": "Accuracy threshold for recognition? (90%+)",
            "source": "semantic_node_executor",
            "owner": "runtime"
          },
          {
            "statement": "Multilingual support? (deferred)",
            "source": "semantic_node_executor",
            "owner": "runtime"
          },
          {
            "statement": "Minimum social feature? (shelf sharing + messaging)",
            "source": "semantic_node_executor",
            "owner": "runtime"
          },
          {
            "statement": "Privacy concerns?",
            "source": "semantic_node_executor",
            "owner": "runtime"
          }
        ]
      },
      "omitted_context": [
        {
          "source": "Detailed technical architecture",
          "reason": "background_only"
        },
        {
          "source": "Specific AI model selection details",
          "reason": "background_only"
        },
        {
          "source": "Exact UI mockups",
          "reason": "background_only"
        },
        {
          "source": "Marketing strategy",
          "reason": "background_only"
        },
        {
          "source": "Out of scope items",
          "reason": "not needed for API design"
        }
      ],
      "compression_rationale": {
        "method": "Extracted key decisions, constraints, assumptions, and open questions from handoff and issue decomposition. Omitted implementation details not needed for API contract design.",
        "loss_notes": []
      },
      "quality_checks": [
        {
          "name": "All endpoints have request/response types",
          "passed": true
        },
        {
          "name": "Error contract present with typed codes",
          "passed": true
        },
        {
          "name": "Versioning strategy stated",
          "passed": true
        },
        {
          "name": "Nullable and optional fields explicit",
          "passed": true
        },
        {
          "name": "No god object parameters",
          "passed": true
        }
      ]
    }
  },
  "semantic_execution": true,
  "metadata": {
    "completion_report": {
      "what_was_done": "Designed the complete API contract for the Bookshelf app in TypeScript, covering auth, shelves, recognition, books, social features, messaging, subscriptions, and notifications. Included error codes, versioning strategy, and WebSocket events.",
      "key_decisions": [
        {
          "decision": "Use REST with WebSocket for real-time messaging and notifications",
          "rationale": "REST is simple and stateless for CRUD; WebSocket provides low-latency messaging and push without polling."
        },
        {
          "decision": "Recognition is async with job polling",
          "rationale": "AI processing may take seconds; async pattern avoids timeout and allows progress tracking."
        },
        {
          "decision": "Shelf positions are 1-based row/column",
          "rationale": "Matches physical shelf layout and is intuitive for users."
        },
        {
          "decision": "Subscription verification via backend receipt validation",
          "rationale": "Prevents fraud; backend validates receipt with Apple before granting access."
        },
        {
          "decision": "Social similarity uses cosine similarity on genre vectors",
          "rationale": "Simple, interpretable, and efficient for initial release."
        }
      ],
      "handoff_focus": [
        "Implement auth endpoints first (Issue 5) as they are foundational.",
        "Implement recognition endpoints (Issue 2) with async job pattern.",
        "Implement shelf CRUD and book search (Issue 4) after recognition.",
        "Implement social and messaging endpoints (Issues 7, 8) last."
      ],
      "open_questions": [
        "Should we use WebSocket or polling for messaging? (Deferred to implementation - WebSocket chosen for real-time)",
        "What is the exact AI service endpoint and pricing? (Needs research)",
        "How to handle book cover image storage? (S3 or similar)"
      ],
      "known_constraints": [
        "iOS only for initial release.",
        "No manual book entry.",
        "Subscription required for full features.",
        "English only for initial release."
      ],
      "confidence_differential": 0.9,
      "dissent_if_alone": null,
      "iteration_context": null
    }
  }
}