"""
Inference engine quality: test corpus + feedback collector + learning bridge.

Design:
  - test_corpus.yaml: fixed regression tests, grows with every discovered failure.
  - Every Encoder run records (description, inferred, used, triage_output) in
    the manifest. Graph Topologist reads these to propose pattern changes.
  - Conflict detector: catches ambiguous patterns before they ship.
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TEST_CORPUS_PATH = ROOT / "ontology" / "encoder_test_corpus.yaml"
LEARNING_SIGNALS_PATH = ROOT / "traces" / "encoder_learning_signals.yaml"


# ── Pattern quality checks ──

def check_pattern_conflicts(patterns: list[tuple[list[str], str]]) -> list[str]:
    """Return warnings when a phrase could match multiple task types."""
    issues: list[str] = []
    test_phrases = [
        ("design the architecture for microservices", ["design", "architecture"]),
        ("build a new ui design system", ["feature", "design"]),
        ("refactor the deployment pipeline", ["refactor", "ops"]),
        ("fix the broken ci/cd pipeline", ["bug_fix", "ops"]),
    ]
    for phrase, possible_types in test_phrases:
        text = phrase.lower()
        matches = []
        for pat_list, ttype in patterns:
            for p in pat_list:
                if re.search(p, text):
                    matches.append(ttype)
                    break
        # If multiple match, check that the first (highest priority) is correct
        if len(matches) > 1 and matches[0] not in possible_types[:1]:
            issues.append(
                f"CONFLICT: '{phrase}' matched {matches}; "
                f"first={matches[0]} may not be the intended type ({possible_types})"
            )
    return issues


# ── Test corpus ──

def load_test_corpus() -> dict[str, Any]:
    if TEST_CORPUS_PATH.exists():
        with open(TEST_CORPUS_PATH) as f:
            return yaml.safe_load(f) or {}
    return {"version": 1, "cases": []}


def save_test_corpus(corpus: dict[str, Any]) -> None:
    TEST_CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TEST_CORPUS_PATH, "w") as f:
        yaml.dump(corpus, f, allow_unicode=True, sort_keys=False)


def add_test_case(description: str, expected: str, source: str = "manual") -> None:
    """Add a regression test case to the corpus."""
    corpus = load_test_corpus()
    # Avoid duplicates
    for case in corpus.get("cases", []):
        if case.get("description") == description:
            return
    corpus.setdefault("cases", []).append({
        "description": description,
        "expected": expected,
        "source": source,
        "added": __import__("datetime").datetime.now().isoformat(),
    })
    save_test_corpus(corpus)


def run_test_corpus(patterns: list[tuple[list[str], str]]) -> dict[str, Any]:
    """Run all test cases against the current patterns. Return pass/fail report."""
    corpus = load_test_corpus()
    results = {"passed": 0, "failed": 0, "failures": []}
    for case in corpus.get("cases", []):
        desc = case["description"]
        expected = case["expected"]
        actual = _infer(patterns, desc)
        if actual == expected:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append({
                "description": desc,
                "expected": expected,
                "actual": actual,
            })
    return results


def _infer(patterns: list[tuple[list[str], str]], description: str) -> str | None:
    text = description.lower()
    for pat_list, ttype in patterns:
        for pat in pat_list:
            if re.search(pat, text):
                return ttype
    return None


# ── Learning signal collector ──

def record_encoder_signal(
    task_id: str,
    description: str,
    inferred: str | None,
    used: bool,
    triage_type: str | None = None,
) -> None:
    """Record an Encoder decision for later learning analysis."""
    LEARNING_SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    signals = {}
    if LEARNING_SIGNALS_PATH.exists():
        with open(LEARNING_SIGNALS_PATH) as f:
            signals = yaml.safe_load(f) or {}

    signals.setdefault("signals", []).append({
        "task_id": task_id,
        "description": description[:200],
        "inferred": inferred,
        "used": used,
        "triage_type": triage_type,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    })

    # Keep only last 200 signals
    if len(signals.get("signals", [])) > 200:
        signals["signals"] = signals["signals"][-200:]

    with open(LEARNING_SIGNALS_PATH, "w") as f:
        yaml.dump(signals, f, allow_unicode=True)


def get_learning_proposals() -> list[dict[str, Any]]:
    """Analyze signals and propose pattern changes.

    Returns proposals like:
      - Add new keyword: "performance" → bug_fix or new performance type?
      - Reorder patterns: "design" vs "architecture" ambiguity
      - Missing pattern: phrases that consistently get None but triage says feature
    """
    if not LEARNING_SIGNALS_PATH.exists():
        return []

    with open(LEARNING_SIGNALS_PATH) as f:
        data = yaml.safe_load(f) or {}

    signals = data.get("signals", [])
    proposals: list[dict[str, Any]] = []

    # Find: inferred=None but triage consistently says X
    triage_overrides: dict[str, list[str]] = {}
    for s in signals:
        if s.get("inferred") is None and s.get("triage_type"):
            tt = s["triage_type"]
            triage_overrides.setdefault(tt, []).append(s["description"])

    for tt, descs in triage_overrides.items():
        if len(descs) >= 3:  # pattern: 3+ times infer=None but triage=tt
            # Extract common words from descriptions
            words: dict[str, int] = {}
            for d in descs:
                for w in re.findall(r"\w+", d.lower()):
                    if len(w) > 3:
                        words[w] = words.get(w, 0) + 1
            top_words = sorted(words, key=words.get, reverse=True)[:5]
            proposals.append({
                "type": "missing_pattern",
                "suggested_type": tt,
                "sample_count": len(descs),
                "common_words": top_words,
                "sample_descriptions": descs[:3],
            })

    return proposals


# ── CLI ──

if __name__ == "__main__":
    import sys
    from tools.silicon_task import TASK_TYPE_PATTERNS

    if len(sys.argv) > 1 and sys.argv[1] == "check":
        issues = check_pattern_conflicts(TASK_TYPE_PATTERNS)
        if issues:
            print("⚠️  Pattern conflicts found:")
            for i in issues:
                print(f"  {i}")
        else:
            print("✅ No pattern conflicts.")

    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        results = run_test_corpus(TASK_TYPE_PATTERNS)
        print(f"Test Corpus: {results['passed']} passed, {results['failed']} failed")
        for f in results["failures"]:
            print(f"  ❌ \"{f['description'][:60]}...\" → {f['actual']} (expected: {f['expected']})")

    elif len(sys.argv) > 1 and sys.argv[1] == "learn":
        proposals = get_learning_proposals()
        if proposals:
            print(f"Learning proposals ({len(proposals)}):")
            for p in proposals:
                print(f"  📝 {p['type']}: {p['suggested_type']} ({p['sample_count']} samples)")
                print(f"     words: {p['common_words']}")
                print(f"     e.g.: \"{p['sample_descriptions'][0][:80]}...\"")
        else:
            print("No learning proposals yet. Need more signals.")

    elif len(sys.argv) > 1 and sys.argv[1] == "add-case":
        if len(sys.argv) < 4:
            print("Usage: python encoder_quality.py add-case '<description>' <expected_type>")
            sys.exit(1)
        add_test_case(sys.argv[2], sys.argv[3])
        print(f"Added test case: {sys.argv[2][:60]}... → {sys.argv[3]}")

    else:
        print("Usage: python encoder_quality.py [check|test|learn|add-case]")
