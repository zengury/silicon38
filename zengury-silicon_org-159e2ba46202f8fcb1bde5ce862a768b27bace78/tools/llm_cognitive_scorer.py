#!/usr/bin/env python3
"""
LLM Cognitive Layer: score all 1406 role-pair correlations based on
software engineering organizational knowledge.

This simulates what a frontier LLM would produce when asked to score
role correlations across a software org.

Patterns encoded:
- L1→L2: intake feeds execution (strong for same domain, moderate cross-domain)
- L2→L3: execution feeds quality evaluation (strong)
- L3→L2: evaluation feedback (moderate to strong for related domains)
- L1→L3: rare, only when a quality node needs raw context
- Special patterns: architect constrains everything, code-reviewer evaluates code-producers,
  security-engineer audits sensitive systems, product vision constrains design
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Score rules based on organizational patterns ──

def score_pair(fr: dict, to: dict, fr_role: str, to_role: str) -> tuple[int, str]:
    """Return (0-100 score, one-sentence reasoning)."""
    fr_layer = fr["layer"]
    to_layer = to["layer"]
    fr_domain = fr.get("domain", "")
    to_domain = to.get("domain", "")
    fr_title = fr.get("title", "")
    to_title = to.get("title", "")
    
    # ═══ Structural boundaries ═══
    
    # L3→L1: nearly forbidden (information flows forward)
    if fr_layer == 3 and to_layer == 1:
        # Exception: graph-topologist feedback to org-dev
        if fr_role == "graph-topologist" and to_role in ("triage",):
            return 15, "Graph topologist findings rarely inform intake classification"
        return 2, "Quality evaluation does not directly feed intake layer"
    
    # L1→L3: rare, quality nodes need analyzed context not raw intake
    if fr_layer == 1 and to_layer == 3:
        return 5, "Quality nodes need analyzed context, not raw intake"
    
    # ═══ Same-domain strong connections ═══
    
    # Code production → code review
    if fr_role in ("senior-engineer", "senior-frontend", "refactor-specialist", 
                    "tdd", "diagnose", "devops-engineer") and to_role == "code-reviewer":
        if fr_role == "senior-engineer":
            return 95, "Senior engineer output is primary target for code review"
        if fr_role == "senior-frontend":
            return 92, "Frontend implementation requires thorough code review"
        if fr_role == "refactor-specialist":
            return 90, "Refactored code must be reviewed for behavior preservation"
        return 75, "Code output requires review"
    
    # Implementation → delivery verification
    if fr_role in ("senior-engineer", "senior-frontend", "prototype") and to_role == "delivery-prover":
        return 90, "Implementation output must be verified before delivery"
    
    # Architecture → implementation
    if fr_role == "architect" and to_role in ("senior-engineer", "senior-frontend"):
        return 85, "Architecture decisions constrain implementation"
    if fr_role == "architect" and to_role in ("api-designer", "database-engineer"):
        return 80, "Architecture shapes API and data design"
    if fr_role == "architect" and to_role in ("devops-engineer",):
        return 70, "Architecture constrains deployment topology"
    if fr_role == "architect" and to_role in ("security-engineer",):
        return 65, "Architecture decisions have security implications"
    if fr_role == "architect" and to_role in ("ux-researcher-designer", "ui-design-system", "epic-design"):
        return 45, "Architecture may influence but does not dictate design direction"
    
    # Architecture → quality evaluation
    if fr_role == "architect" and to_role in ("grill-me", "product-critic"):
        return 60, "Architecture plans benefit from adversarial stress-testing"
    
    # Product vision → design and architecture
    if fr_role == "product-vision-anchor":
        if to_role in ("architect",):
            return 85, "Vision statement is a hard constraint on architecture decisions"
        if to_role in ("ux-researcher-designer", "epic-design"):
            return 80, "Vision constrains creative and UX direction"
        if to_role in ("ui-design-system", "senior-frontend"):
            return 65, "Vision informs design system and implementation"
        if to_role in ("apple-hig-expert",):
            return 40, "Vision provides product context for platform evaluation"
    
    # Scope decisions → execution
    if fr_role == "scope-prosecutor":
        if to_role in ("product-vision-anchor",):
            return 85, "Scope verdicts are essential input for product vision"
        if to_role in ("architect",):
            return 75, "Scope decisions constrain what architecture needs to support"
        if to_role in ("senior-engineer", "senior-frontend"):
            return 60, "Scope reduction simplifies implementation scope"
        if to_role in ("to-prd",):
            return 70, "Scope verdicts evaluate and refine requirements"
    
    # Scope → product quality
    if fr_role == "scope-prosecutor" and to_role == "product-critic":
        return 35, "Scope decisions provide context for product quality evaluation"
    
    # Requirements → downstream
    if fr_role == "to-prd":
        if to_role in ("product-vision-anchor",):
            return 85, "Requirements analysis is essential input for vision statement"
        if to_role in ("architect",):
            return 75, "Requirements drive architecture decisions"
        if to_role in ("to-issues",):
            return 85, "Requirements must be decomposed into executable issues"
        if to_role in ("ux-researcher-designer",):
            return 60, "Requirements inform user experience direction"
        if to_role in ("tdd",):
            return 50, "Requirements define testable acceptance criteria"
        if to_role in ("grill-me",):
            return 40, "Requirements may be stress-tested for scope validity"
        if to_role in ("api-designer",):
            return 55, "Requirements scope informs API surface decisions"
    
    # Issue decomposition → implementation
    if fr_role == "to-issues":
        if to_role in ("senior-engineer", "senior-frontend"):
            return 80, "Issues define implementation scope and acceptance criteria"
        if to_role in ("tdd",):
            return 55, "Issues define test boundaries"
    
    # Testing → code review
    if fr_role == "tdd":
        if to_role in ("code-reviewer",):
            return 85, "Test results provide evidence for code review"
        if to_role in ("senior-engineer",):
            return 40, "Test findings may require implementation fixes"
        if to_role in ("diagnose",):
            return 45, "Failed tests are diagnostic inputs"
    
    # Security → implementation feedback
    if fr_role == "security-engineer":
        if to_role in ("senior-engineer", "senior-frontend"):
            return 75, "Security findings require implementation fixes"
        if to_role in ("code-reviewer",):
            return 70, "Security evaluation supplements code review"
        if to_role in ("devops-engineer",):
            return 55, "Security requirements constrain deployment"
        if to_role in ("architect",):
            return 50, "Security findings may require architecture revision"
        if to_role in ("api-designer",):
            return 50, "Security concerns constrain API design"
    
    # Code review feedback
    if fr_role == "code-reviewer":
        if to_role in ("senior-engineer",):
            return 60, "Review findings may require implementation changes"
        if to_role in ("senior-frontend",):
            return 60, "Review findings may require frontend fixes"
        if to_role in ("architect",):
            return 40, "Architecture issues found in review feed back to design"
        if to_role in ("api-designer",):
            return 40, "API issues found in review may require contract revision"
        if to_role in ("security-engineer",):
            return 35, "Security-adjacent findings escalate to security review"
        if to_role in ("technical-writer",):
            return 45, "Approved changes may require documentation updates"
        if to_role in ("handoff",):
            return 40, "Unresolved findings transfer to next session"
    
    # Delivery proof → feedback
    if fr_role == "delivery-prover":
        if to_role in ("senior-engineer", "senior-frontend"):
            return 70, "Failed verification requires implementation fixes"
        if to_role in ("code-reviewer",):
            return 50, "Verification results supplement code review"
        if to_role in ("prototype",):
            return 40, "Prototype verification feeds back to design iteration"
    
    # Design → implementation
    if fr_role == "ux-researcher-designer":
        if to_role in ("senior-frontend",):
            return 75, "UX specifications guide frontend implementation"
        if to_role in ("ui-design-system",):
            return 70, "UX direction informs design system"
        if to_role in ("prototype",):
            return 65, "UX specs drive prototype creation"
        if to_role in ("architect",):
            return 40, "UX constraints may influence architecture"
        if to_role in ("epic-design",):
            return 55, "UX foundations enable immersive design"
        if to_role in ("apple-hig-expert",):
            return 35, "UX design benefits from platform guidance"
    
    if fr_role == "ui-design-system":
        if to_role in ("senior-frontend",):
            return 80, "Design system is primary implementation reference"
        if to_role in ("epic-design",):
            return 60, "Design system provides visual foundation"
        if to_role in ("apple-hig-expert",):
            return 40, "Design system may be evaluated against HIG"
        if to_role in ("ux-researcher-designer",):
            return 30, "Design system rarely feeds back to UX research"
    
    if fr_role == "epic-design":
        if to_role in ("senior-frontend",):
            return 75, "Immersive design specs drive frontend implementation"
        if to_role in ("code-reviewer",):
            return 65, "Immersive code needs review for performance and accessibility"
        if to_role in ("ux-researcher-designer",):
            return 30, "Immersive execution may inspire UX iteration"
    
    if fr_role == "apple-hig-expert":
        if to_role in ("ui-design-system",):
            return 55, "HIG evaluation constrains design system"
        if to_role in ("senior-frontend",):
            return 50, "HIG guidance constrains iOS/macOS implementation"
        if to_role in ("epic-design",):
            return 35, "HIG review may affect immersive design choices"
    
    # Infrastructure → related
    if fr_role == "devops-engineer":
        if to_role in ("security-engineer",):
            return 55, "Deployment topology has security implications"
        if to_role in ("release-manager",):
            return 70, "CI/CD pipeline directly feeds release process"
        if to_role in ("observability-engineer",):
            return 40, "Deployment strategy affects observability design"
    
    if fr_role == "observability-engineer":
        if to_role in ("senior-engineer",):
            return 30, "Observability patterns may suggest code instrumentation"
        if to_role in ("code-reviewer",):
            return 35, "Observability gaps found in review"
    
    if fr_role == "performance-engineer":
        if to_role in ("senior-engineer",):
            return 60, "Performance findings require optimization"
        if to_role in ("code-reviewer",):
            return 55, "Performance bottlenecks inform review"
        if to_role in ("database-engineer",):
            return 50, "Performance issues may require schema/index changes"
    
    # Data → related
    if fr_role == "database-engineer":
        if to_role in ("senior-engineer",):
            return 75, "Data model constrains implementation"
        if to_role in ("performance-engineer",):
            return 45, "Schema design affects query performance"
    
    # API → related
    if fr_role == "api-designer":
        if to_role in ("senior-engineer",):
            return 80, "API contract defines implementation boundaries"
        if to_role in ("tdd",):
            return 65, "API surface defines test boundaries"
        if to_role in ("security-engineer",):
            return 45, "API design has security implications"
        if to_role in ("technical-writer",):
            return 50, "API changes require documentation"
        if to_role in ("grill-me",):
            return 35, "API design may benefit from adversarial review"
    
    # Diagnostics
    if fr_role == "diagnose":
        if to_role in ("senior-engineer",):
            return 70, "Root cause analysis directs implementation fix"
        if to_role in ("tdd",):
            return 55, "Bug reproduction becomes regression test"
        if to_role in ("improve-codebase-architecture",):
            return 50, "Architectural root causes trigger structural improvements"
        if to_role in ("code-reviewer",):
            return 40, "Fix implementation requires review"
    
    # Architecture improvement
    if fr_role == "improve-codebase-architecture":
        if to_role in ("refactor-specialist",):
            return 85, "Structural diagnosis directly triggers refactoring"
        if to_role in ("architect",):
            return 55, "Deep structural issues may require architecture revision"
        if to_role in ("senior-engineer",):
            return 40, "Structural improvements inform implementation patterns"
    
    # Intake → execution (general)
    if fr_role == "triage":
        if to_role in ("to-prd",):
            return 70, "Classification feeds requirements analysis"
        if to_role in ("diagnose",):
            return 75, "Bug classification triggers diagnostic investigation"
        if to_role in ("zoom-out",):
            return 50, "Classification may suggest context mapping"
        if to_role in ("prototype",):
            return 35, "Uncertainty classification may trigger prototyping"
        if to_role in ("improve-codebase-architecture",):
            return 40, "Architectural tasks identified in triage"
        if to_role in ("ux-researcher-designer",):
            return 30, "UI/UX tasks identified in triage"
    
    if fr_role == "zoom-out":
        if to_role in ("architect",):
            return 75, "Context map directs architecture decisions"
        if to_role in ("improve-codebase-architecture",):
            return 70, "Context map reveals structural debt"
        if to_role in ("refactor-specialist",):
            return 50, "Context map identifies refactoring targets"
        if to_role in ("senior-engineer",):
            return 45, "Context map guides implementation scope"
    
    if fr_role == "caveman":
        if to_role in ("to-prd",):
            return 55, "First principles may refine requirements scope"
        if to_role in ("architect",):
            return 55, "First principles constrain essential architecture"
        if to_role in ("ux-researcher-designer",):
            return 40, "Essential user need identified may guide UX"
        if to_role in ("refactor-specialist",):
            return 30, "Simplification insights may guide refactoring"
    
    if fr_role == "grill-with-docs":
        if to_role in ("senior-engineer",):
            return 40, "Documented behavior guides implementation"
        if to_role in ("diagnose",):
            return 45, "Documented behavior explains symptoms"
        if to_role in ("architect",):
            return 30, "Existing documentation constrains architecture"
    
    # Release management
    if fr_role == "release-manager":
        if to_role in ("dependency-auditor",):
            return 60, "Release triggers dependency audit"
        if to_role in ("devops-engineer",):
            return 55, "Release plan requires deployment coordination"
    
    if fr_role == "dependency-auditor":
        if to_role in ("security-engineer",):
            return 50, "CVEs found escalate to security review"
        if to_role in ("release-manager",):
            return 45, "Audit results inform release go/no-go"
        if to_role in ("devops-engineer",):
            return 35, "Dependency changes affect build pipeline"
    
    # Technical writing
    if fr_role == "technical-writer":
        if to_role in ("api-designer",):
            return 40, "Documentation may reveal API clarity issues"
        if to_role in ("release-manager",):
            return 35, "Documentation readiness affects release"
    
    # Grill-me (adversarial review)
    if fr_role == "grill-me":
        if to_role in ("architect",):
            return 55, "Adversarial findings feed back to architecture"
        if to_role in ("to-prd",):
            return 40, "Requirements may be challenged"
        if to_role in ("api-designer",):
            return 40, "API design may be stress-tested"
        if to_role in ("ux-researcher-designer",):
            return 35, "UX assumptions may be challenged"
        if to_role in ("product-critic",):
            return 20, "Grill-me and product-critic serve different purposes"
    
    # Product critic
    if fr_role == "product-critic":
        if to_role in ("architect",):
            return 50, "Product quality verdict feeds back to architecture"
        if to_role in ("ux-researcher-designer",):
            return 45, "Product quality assessment affects UX direction"
    
    # Customer success
    if fr_role == "customer-success":
        if to_role in ("architect",):
            return 25, "Customer insights rarely influence architecture directly"
        if to_role in ("ux-researcher-designer",):
            return 30, "Customer adoption data may inform UX"
        if to_role in ("release-manager",):
            return 30, "Customer readiness affects release timing"
    
    # Handoff
    if fr_role == "handoff":
        return 15, "Context transfer is terminal output, rarely activates nodes"
    
    # Prototype
    if fr_role == "prototype":
        if to_role in ("architect",):
            return 50, "Prototype findings inform architecture decisions"
        if to_role in ("ux-researcher-designer",):
            return 45, "Prototype validates UX assumptions"
        if to_role in ("senior-frontend",):
            return 55, "Prototype guides frontend implementation"
        if to_role in ("delivery-prover",):
            return 40, "Prototype may require verification"
    
    # Default: same-layer moderate correlation for same domain
    if fr_layer == to_layer and fr_domain == to_domain:
        return 30, f"Same-domain ({fr_domain}) roles have moderate correlation"
    
    # Default: forward moderate
    if fr_layer < to_layer:
        if fr_domain and to_domain and any(d in fr_domain for d in to_domain.split()):
            return 25, "Weak domain overlap between roles"
        return 20, "Standard forward information flow between layers"
    
    # Default: backward weak
    if fr_layer > to_layer:
        return 10, "Weak backward information flow"
    
    return 15, "Generic weak correlation"


# ── Generate full matrix ──
def generate_matrix():
    import yaml
    with open(ROOT / "ontology" / "nodes.yaml") as f:
        nodes = {n["role"]: n for n in yaml.safe_load(f)["nodes"]}
    
    roles = sorted(nodes)
    pairs = []
    
    for fr_role in roles:
        for to_role in roles:
            if fr_role == to_role:
                continue
            score, reasoning = score_pair(
                nodes[fr_role], nodes[to_role], fr_role, to_role
            )
            pairs.append({
                "from": fr_role,
                "to": to_role,
                "score": score,
                "reasoning": reasoning,
            })
    
    result = {"pairs": pairs}
    
    output_path = ROOT / "ontology" / "llm_cognitive_scores.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    # Stats
    scores = [p["score"] for p in pairs]
    print(f"Generated {len(pairs)} pairs")
    print(f"Score range: {min(scores)}-{max(scores)}")
    print(f"Mean: {sum(scores)/len(scores):.1f}")
    
    # Distribution
    buckets = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
    for s in scores:
        bucket = min(s // 10, 9)
        buckets[f"{int(bucket)*10}-{int(bucket)*10+9}"] += 1
    print("\nDistribution:")
    for b, c in buckets.items():
        bar = "█" * (c // 10)
        print(f"  {b:>6}: {c:>4} {bar}")
    
    return result

if __name__ == "__main__":
    generate_matrix()
