# Bookshelf — Product Vision Statement

## Vision Statement

> **A serious book collector who cannot locate their own books across chaotic physical shelves uses Bookshelf to digitize their entire library with a single photo, so they feel in command of their collection rather than buried by it, unlike manual cataloging apps which demand hours of tedious data entry.**

---

## Breakdown

```yaml
target_user: >
  Serious book collectors with 100+ physical books across multiple shelves —
  people who care enough about their library to want it organized, but not
  enough to spend hours manually entering ISBNs. They value their collection
  as an intellectual identity, not just decoration.

primary_job: >
  Digitize a physical bookshelf instantly by taking a photo, then find any
  book by searching — locating its exact position on the shelf.
  The job is not "cataloging books." The job is "I need that book right now
  and I know I own it but I can't find it."

emotional_promise: >
  Command, not overwhelm. The user walks into a room full of books and feels
  the weight of disorganization. After using Bookshelf, they feel: "I know
  exactly where everything is. My library is at my fingertips." The app
  restores the sense of mastery that a large collection should provide.

beating_alternative: >
  Manual cataloging apps (Goodreads, LibraryThing, spreadsheets) that require
  typing or scanning each ISBN individually. These tools fail because the
  effort-to-value ratio is broken: 10+ hours of data entry for a collection
  you already own feels absurd. Bookshelf collapses that to 10 seconds per
  shelf.

out_of_scope_forever: >
  - Bookshelf will never be an e-book reader or e-book store. It serves
    physical book owners, not digital consumers.
  - Bookshelf will never replace the tactile experience of physical books.
    It augments, does not substitute.
  - Bookshelf will never be a general-purpose social network. Shelf sharing
    exists to connect readers around physical collections — not to generate
    engagement metrics.
  - Bookshelf will never sell user data or serve targeted ads. The
    subscription is the business model.

vision_test: |
  A downstream node can test its output by asking:
  1. "Does my output help a book collector instantly digitize their physical
     shelf and find a specific book by its physical location?"
  2. "Does my output reinforce the feeling of command over their collection,
     or does it add cognitive load?"
  3. "Does my output avoid e-book reading, e-commerce, general social
     networking, and data monetization?"
  A "no" to any question means the output does not serve the product vision.
```

---

## JTBD Layers

| Layer | Job | Evidence from PRD |
|-------|-----|-------------------|
| **Functional** | Take photo → AI recognizes books → search finds location | Core user stories #1–#4 |
| **Emotional** | From "I know I have that book somewhere" frustration → "It's third shelf, second from left" certainty | The pain statement: hundreds of books, chaotic arrangement, can't find anything |
| **Social** | Be the person whose library is impressively organized, shareable on demand | Deferred to v2, but the link-sharing path (caveman) keeps the door open |

---

## Positioning (April Dunford)

| Element | Answer |
|---------|--------|
| **Competitive alternative** | Manual ISBN entry apps (Goodreads, LibraryThing); remembering/bookmark-hopping; physical shelf-searching |
| **Differentiated value** | Photo → instant digital shelf. 10 seconds vs. 10 hours. Visual-spatial memory preserved. |
| **Target segment** | Serious physical book collectors (100–2,000 books), age 25–55, who value their library as identity |
| **Market category** | Personal library digitization (not "book tracking" or "social reading") |
| **Relevant trend** | AI vision models now capable of book spine recognition at consumer-accessible cost |

---

## Completion Report

```yaml
completion_report:
  what_was_done: >
    Synthesized to-prd (10 user stories, tech decisions) and scope-prosecutor
    (KEEP 6 / DEFER 4) into a single falsifiable product vision statement using
    JTBD discovery + April Dunford positioning. The vision anchors on "command
    over collection" as the emotional promise and "instant photo digitization"
    as the differentiated value against manual cataloging.
  key_decisions:
    - decision: "Primary job is 'find a book by its physical location' — not 'catalog books'"
      rationale: >
        The user's pain is not "I don't know what books I own." It's "I can't
        find the one I need right now." This reframes the product from a
        cataloging tool to a spatial retrieval tool.
    - decision: "Out of scope forever includes e-book reader, e-commerce, general social network, and data monetization"
      rationale: >
        These boundaries protect the subscription business model (no ads) and
        keep the product focused on physical book owners. They also prevent
        feature creep into social media territory.
    - decision: "Emotional promise is 'command, not overwhelm'"
      rationale: >
        The user's emotional state before using Bookshelf is frustration and
        helplessness. The app must produce the opposite feeling — mastery.
        Every interaction must reduce cognitive load, not add it.
  handoff_focus:
    - "Vision statement must constrain all downstream Layer 2 nodes"
    - "Architect: every system boundary must serve the photo→digitize→search→locate flow"
    - "UX Designer: every screen must reinforce 'command over collection' — no decorative complexity"
    - "Out-of-scope-forever items are hard boundaries for feature discussions"
  open_questions:
    - "Will users perceive the 'find by location' job as distinct enough from existing catalog apps to pay $1.99/month?"
    - "Does 'command over collection' resonate in user testing, or is there a stronger emotional driver?"
  known_constraints:
    - "iOS only for v1"
    - "Photo-based input only — no manual fallback"
    - "$1.99/month subscription from day one"
    - "No social features in v1 (deferred by scope-prosecutor + caveman)"
  confidence_differential: 0.15
  dissent_if_alone: null
```

---

## Vision Test Examples

| Downstream Decision | Serves Vision? | Why |
|---------------------|---------------|-----|
| Add a "Recently Viewed" shelf section | ✅ Yes | Reduces time to locate, reinforces command |
| Add a social feed of friends' books | ❌ No | Out of scope forever (general social network) |
| Add barcode scanning fallback | ⚠️ Maybe | Speeds digitization but violates "photo only" constraint — risks making manual entry the primary path |
| Add reading progress tracker | ❌ No | E-book reader territory; out of scope forever |
| Shelf similarity matching (v2) | ✅ Yes | Connects collectors around physical libraries, not social media engagement |
