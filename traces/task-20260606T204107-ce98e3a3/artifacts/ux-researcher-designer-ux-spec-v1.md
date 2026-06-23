# Bookshelf — UX Research & Design Specification

## 🧑 Persona: Elena, 38 — The Serious Collector

> "I know I own it. I've held it in my hands. I just can't find it."

```yaml
persona:
  name: Elena
  age: 38
  occupation: "Architectural historian; reads across 6+ disciplines for research"
  collection:
    size: "~800 books"
    shelves: 7
    arrangement: "Roughly by discipline, then by acquisition date. The overflow shelf is chaos."
  current_behavior:
    finding_a_book: >
      Walks shelf by shelf, squinting at spines. Has been known to spend 20 minutes
      looking for a book she needs for a deadline. Sometimes buys a second copy
      because she can't find the first.
    cataloging_attempts: >
      Tried Goodreads in 2019. Entered 40 books over a weekend, quit. Tried a spreadsheet
      in 2021. Abandoned at row 23. The effort-to-value ratio is broken.
  emotional_state_before: >
    Frustrated. Ashamed at the disorganization. Her collection is a core part of
    her identity — the mess feels like a personal failure.
  emotional_state_after: >
    In command. Opens the app, types a title, sees exactly which shelf and position.
    Walks directly to the book. Feels the satisfaction of a well-managed library
    without the guilt of never having organized it.
  tech_comfort: "Comfortable with iOS. Uses Apple Pay. Subscribes to 3–4 apps monthly."
  price_sensitivity: "Will pay $1.99/month without thinking twice. Would hesitate at $4.99."
```

---

## 🗺️ Primary Journey: First Shelf Digitization

```
┌─────────────────────────────────────────────────────────────────┐
│ JOURNEY: Elena digitizes her first shelf                        │
├──────────┬──────────────────┬────────────────┬─────────────────┤
│ STEP     │ SCREEN           │ WHAT HAPPENS    │ EMOTIONAL BEAT  │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 1. Open  │ Onboarding       │ 3 screens max: │ "This might     │
│          │ (3 cards)        │ - Your library  │  actually work" │
│          │                  │   in one photo  │                 │
│          │                  │ - AI recognizes │                 │
│          │                  │   every book    │                 │
│          │                  │ - Find anything │                 │
│          │                  │   instantly     │                 │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 2. Sign  │ Sign Up /        │ Email +        │ "Standard.      │
│    Up    │ Subscribe        │ password or     │  Fine."        │
│          │                  │ Apple Sign In   │                 │
│          │                  │ → IAP prompt    │                 │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 3. Name  │ New Shelf        │ "Name this     │ "Living Room    │
│    Shelf │ creation         │ shelf" +       │  Left. Easy."   │
│          │                  │ rows × columns │                 │
│          │                  │ (auto-guessed) │                 │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 4. Photo │ Camera           │ Viewfinder      │ ⚡ ANTICIPATION │
│          │                  │ with shelf      │ "Is it really  │
│          │                  │ guide overlay   │ going to        │
│          │                  │                 │ recognize all   │
│          │                  │                 │ 43 books?"      │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 5. Upload│ Processing       │ Photo preview   │ ⏳ WAITING      │
│          │                  │ → progress bar  │ "This better    │
│          │                  │ → "Recognizing  │  work..."       │
│          │                  │   your books…"  │                 │
│          │                  │ (5–15 seconds)  │                 │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 6. Review│ Recognition      │ Grid of book    │ 🎉 DELIGHT      │
│          │ Results          │ covers + titles │ "It got ALL of  │
│          │                  │ with confidence │  them. Even the │
│          │                  │ indicators      │  obscure ones!" │
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 7. Shelf │ Shelf View       │ Digital shelf   │ 😌 COMMAND      │
│          │                  │ matching real   │ "There it is.   │
│          │                  │ layout. Scroll, │  It looks just  │
│          │                  │ tap for detail. │  like my shelf."│
├──────────┼──────────────────┼────────────────┼─────────────────┤
│ 8. Search │ Search           │ Type "Design"   │ 🔍 POWER        │
│          │                  │ → 12 books      │ "I forgot I     │
│          │                  │ across shelves  │  owned that.    │
│          │                  │ → shelf +       │  And it's right │
│          │                  │ position shown   │  there."        │
└──────────┴──────────────────┴────────────────┴─────────────────┘
```

---

## 📱 Screen Design — The Three Tabs (Salk: subtraction)

```
┌─────────────────────────────────┐
│  Bookshelf          [?] [⚙️]   │  ← minimal chrome
├─────────────────────────────────┤
│                                 │
│   ┌──────────────────────────┐  │
│   │     TAB BAR (3 items)    │  │  ← only three entry points
│   │  📚 Shelves  🔍 Search  │  │
│   │        👤 Profile       │  │
│   └──────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

### Tab 1: 📚 Shelves (the home screen)

```
┌─────────────────────────────────┐
│  My Library                     │
│                                 │
│  ┌───────────────────────────┐  │  ← shelf card
│  │ Living Room Left          │  │
│  │ ████████████████████████  │  │     miniature book spines
│  │ 43 books · Added Jun 4    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Study - Main Wall         │  │
│  │ ████████████████████░░░░  │  │     gray = unprocessed area
│  │ 28 books · Added Jun 5    │  │
│  └───────────────────────────┘  │
│                                 │
│  [+ Add a Shelf]                │  ← primary CTA
│                                 │
└─────────────────────────────────┘
```

**Tap shelf card → Shelf Detail View:**

```
┌─────────────────────────────────┐
│  ← Living Room Left             │
│                                 │
│  ┌───┬───┬───┬───┬───┬───┐     │
│  │ 📕│ 📗│ 📘│ 📙│ 📕│ 📗│     │  ← LazyVGrid, 1 column
│  │   │   │   │   │   │   │     │     per physical column
│  ├───┼───┼───┼───┼───┼───┤     │
│  │ 📘│ 📙│ 📕│ 📗│ 📘│ 📙│     │  ← Row 2
│  │   │   │   │   │   │   │     │
│  └───┴───┴───┴───┴───┴───┘     │
│                                 │
│  [Search this shelf...]  🔍     │
│                                 │
└─────────────────────────────────┘
```

**Book cell anatomy:**
```
┌──────────┐
│          │
│  📗      │  ← cover thumbnail (loaded async) or placeholder
│          │
│ Thinking │  ← title truncated to 2 lines
│ Fast...  │
│          │
│ Kahneman │  ← author, 1 line
│ ⚠️       │  ← confidence indicator (only if < 0.7)
└──────────┘
```

**Tap book cell → Book Detail Sheet (half-screen):**
```
┌─────────────────────────────────┐
│  ← Books                        │  ← swipe down to dismiss
│                                 │
│  ┌──────────┐                   │
│  │          │  Thinking, Fast   │
│  │  📗      │  and Slow        │
│  │          │                   │
│  │          │  Daniel Kahneman  │
│  └──────────┘                   │
│                                 │
│  Shelf: Living Room Left        │  ← location info
│  Position: Row 1, Column 3      │
│                                 │
│  ─────────────────────────      │
│  Summary                        │
│                                 │
│  Explores the two systems of    │
│  human thought: the fast,       │
│  intuitive System 1 and the     │
│  slow, deliberate System 2...   │
│                                 │
│  [Mark Uncertain] [✓ Confirm]   │  ← only if confidence < 0.7
└─────────────────────────────────┘
```

---

### Tab 2: 🔍 Search

```
┌─────────────────────────────────┐
│  [Search your library...]  🔍   │  ← auto-focus on tap
│                                 │
│  ── Recent Searches ──          │
│  "design"                       │
│  "philosophy"                   │
│  "kahneman"                     │
│                                 │
│  [Start typing to search        │
│   across all shelves...]        │
└─────────────────────────────────┘
```

**After search:**
```
┌─────────────────────────────────┐
│  [design                 ]  ✕   │
│                                 │
│  12 results                     │
│                                 │
│  ┌───────────────────────────┐  │
│  │ The Design of Everyday... │  │
│  │ Don Norman                │  │
│  │ 📚 Living Room Left       │  │  ← shelf name
│  │ 📍 Row 2, Col 4           │  │  ← position
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Design Patterns           │  │
│  │ Gamma, Helm, Johnson...   │  │
│  │ 📚 Study - Main Wall      │  │
│  │ 📍 Row 1, Col 2           │  │
│  └───────────────────────────┘  │
│  ...                            │
└─────────────────────────────────┘
```

**Key UX decision**: Search results always show the physical location. The user's job is not "find the metadata" — it's "go to the shelf and grab the book." The location is the primary action signal.

---

### Tab 3: 👤 Profile

```
┌─────────────────────────────────┐
│  Elena M.                       │
│  elena@email.com                │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Your Library              │  │
│  │ 7 shelves · 312 books     │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Subscription              │  │
│  │ Premium · $1.99/month     │  │
│  │ [Manage]                  │  │
│  └───────────────────────────┘  │
│                                 │
│  ─────────────────────────      │
│                                 │
│  Settings                       │
│  > Notification Preferences     │  ← (v2: push for recognition complete)
│  > Privacy                      │
│  > Delete Account               │
│                                 │
│  [Log Out]                      │
└─────────────────────────────────┘
```

---

## 📸 Camera Experience (the critical moment)

```
┌─────────────────────────────────┐
│                                 │
│                                 │
│         ┌─────────────┐         │
│         │             │         │
│         │  📷 LIVE    │         │  ← camera viewfinder
│         │  PREVIEW    │         │
│         │             │         │
│         │ ═══════════ │         │  ← shelf alignment guide
│         │ ═══════════ │         │     (horizontal lines
│         │ ═══════════ │         │      showing shelf rows)
│         │             │         │
│         └─────────────┘         │
│                                 │
│  "Frame your shelf so all       │  ← instructional text
│   books are visible"            │     (only shown first 3 uses)
│                                 │
│         [ ○ CAPTURE ]           │  ← shutter button
│                                 │
└─────────────────────────────────┘
```

**Post-capture:**
```
┌─────────────────────────────────┐
│  ← Retake          Use Photo →  │
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │     PHOTO PREVIEW         │  │  ← captured image
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│  "Does this show the full      │
│   shelf clearly?"               │
│                                 │
│  [Retake]    [Looks Good →]     │  ← confirmation
└─────────────────────────────────┘
```

**Upload processing state:**
```
┌─────────────────────────────────┐
│                                 │
│         📚 📚 📚                │
│                                 │
│    Recognizing your books...    │
│                                 │
│    ████████████░░░░░░  65%      │  ← progress indicator
│                                 │
│    "This usually takes about    │
│     10 seconds"                 │
│                                 │
└─────────────────────────────────┘
```

---

## 🆕 New Shelf Creation Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Name your shelf  │     │ Shelf dimensions │     │ Take photo       │
│                  │     │                  │     │                  │
│ [Living Room     │     │ Rows: [3]  ▲    │     │ → Camera flow    │
│  Left________]   │ ──→ │          │▼│    │ ──→ │   (see above)    │
│                  │     │                  │     │                  │
│ Quick names:     │     │ Columns: [6] ▲   │     │                  │
│ ┌────────────┐   │     │           │▼│   │     │                  │
│ │Living Room │   │     │                  │     │                  │
│ │Study       │   │     │ "Count the       │     │                  │
│ │Bedroom     │   │     │  shelves and     │     │                  │
│ │Office      │   │     │  estimate columns│     │                  │
│ └────────────┘   │     │  — you can       │     │                  │
│                  │     │  adjust later"   │     │                  │
│ [Continue]       │     │                  │     │                  │
│                  │     │ [Continue]       │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## ⚠️ Edge Cases & Error States

| State | Visual Treatment | User Action |
|-------|-----------------|-------------|
| **Recognition failed** | Shelf card shows ⚠️ badge. Detail: "Recognition didn't complete. Tap to retry." | Tap → re-upload photo |
| **Partial recognition** (some books, some missed) | Grid shows recognized books + empty slots with "?" placeholder | "We found 28 of ~35 books. Tap any ? to add manually or Retake photo." |
| **Low confidence** (<0.7) | Book cell shows ⚠️ badge in corner; detail sheet shows "AI is uncertain about this book" | "Tap ✓ to confirm or ✏️ to edit title/author" |
| **No internet during upload** | Banner: "Waiting for connection..." Photo cached locally | Auto-retry when connection returns |
| **Subscription expired** | Full-screen card on app open: "Your premium access has ended." Shelf view is read-only. | "Resubscribe" button → IAP flow |
| **Empty state (new user)** | Shelves tab: large illustration of a bookshelf + "Take a photo of your first shelf →" | CTA to camera |
| **Camera permission denied** | "Bookshelf needs camera access to photograph your shelves. Enable in Settings." | "Open Settings" button |
| **Very large shelf** (>10 rows, >20 cols) | After capture: "This shelf is larger than we can process in one photo. Try capturing it in sections." | Split into multiple shelves |

---

## 🎨 UX Principles (derived from vision)

| Principle | Source | Application |
|-----------|--------|-------------|
| **"Where is it?" is the only question** | Vision JTBD | Every screen answers "where is this book?" or leads to that answer. Search results always show position. |
| **Photo → Shelf. Nothing between.** | Salk (subtraction) | No intermediate steps after capture. No tagging, no categorization, no "add details." The photo alone is enough. |
| **Confidence, not perfection** | Kimbell (truth) | Show the AI's uncertainty. Don't pretend 100% accuracy. The ⚠️ badge builds trust, not doubt. |
| **The shelf is the interface** | Esherick (depth hidden) | The digital shelf looks like the real shelf. The AI pipeline is invisible. Users navigate spatially, not through lists. |
| **3 tabs maximum** | Salk | Shelves, Search, Profile. Anything else hides in Profile > Settings. |
| **No decorative UI** | Vision ("no seamless/intuitive/powerful") | Every element earns its place. No animated transitions that don't serve a function. No gradient backgrounds. Typography and spacing do the work. |

---

## ♿ Accessibility

- All book cells have accessibility labels: "Thinking, Fast and Slow by Daniel Kahneman. Row 2, Column 3."
- Search results: VoiceOver reads: "The Design of Everyday Things. Living Room Left shelf, row 2, column 4."
- Minimum tap target: 44×44pt (Apple HIG)
- Dynamic Type support: all text scales with system font size
- Color is never the only differentiator (confidence ⚠️ always paired with text label)
- Camera guide uses both visual lines and haptic feedback when aligned

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Designed the complete UX for Bookshelf v1: persona (Elena, 38, architectural
    historian with 800 books), primary journey map (8 steps from onboarding to
    search), 3-tab screen architecture with full screen designs (Shelves grid,
    Search with location, Profile), camera experience flow (3 screens: capture →
    preview → processing), new shelf creation flow (3 steps), 8 edge case/error
    state treatments, 6 UX principles derived from product vision and soul, and
    accessibility specifications.
  key_decisions:
    - decision: "Three tabs only: Shelves, Search, Profile"
      rationale: >
        Directly from Salk (subtraction) and product vision. Every additional
        navigation item is a cognitive tax the user didn't ask for. Shelves is
        home, Search is the primary job, Profile is the necessary utility.
    - decision: "Shelf grid mirrors physical layout 1:1"
      rationale: >
        Users navigate their physical shelves spatially, not through lists.
        Row × column grid preserves spatial memory. When Search says "Row 2,
        Col 4," the user walks directly there — they don't scroll a list.
    - decision: "Search results always show shelf name + position"
      rationale: >
        The user's job ends at the physical book. Showing the location in
        every search result is the single most important UX decision. Without
        it, search is just a catalog lookup — with it, search is a retrieval
        command.
    - decision: "Confidence indicators are always visible, never hidden"
      rationale: >
        Per Kimbell — truth builds trust. A ⚠️ badge saying "AI is uncertain
        about this book" with a confirm/edit action is honest. Hiding
        uncertainty produces silent errors that erode trust over time.
    - decision: "Onboarding is 3 cards max, skippable"
      rationale: >
        Every onboarding screen is friction. The user came to digitize their
        shelf, not to read marketing. Three cards: what it does, how it works,
        get started. Apple Sign In on the subscription screen collapses
        signup+payment into one step.
  handoff_focus:
    - "senior-frontend: implement the 3-tab layout, shelf grid, search with location, and camera flow per screen designs above"
    - "ui-design-system: extract design tokens from this spec (colors, typography, spacing, ⚠️ badge, book cell)"
    - "prototype: validate the camera → processing → shelf flow with real users before committing to development"
  open_questions:
    - "Should the shelf grid auto-detect rows/columns from the photo, eliminating the manual dimension step?"
    - "Should book covers be fetched from an external API (Google Books, OpenLibrary) or only use AI-recognized metadata?"
    - "Should the app support barcode scanning as a fallback for missed books?"
  known_constraints:
    - "iOS only"
    - "3 tabs maximum"
    - "Photo-based input only"
    - "English only"
    - "No social features in v1"
  confidence_differential: 0.10
  dissent_if_alone: null
```
