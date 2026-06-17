#!/usr/bin/env python3
"""
Cold-start weight matrix builder.
Uses LLM knowledge of organizational role correlations as initial priors,
validated relations as corrections, Bayesian updates from traces as continuous learning.

Three layers:
  0. LLM cognitive: role-pair correlation scores → Beta priors
  1. Validated edges: ontology/relations.yaml → override corrections  
  2. Runtime learning: task traces → Thompson Sampling + Bayesian updates
"""

import yaml, json, math, sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent

# ── Load node registry ──
def load_nodes() -> dict[str, dict]:
    with open(ROOT / "ontology" / "nodes.yaml") as f:
        return {n["role"]: n for n in yaml.safe_load(f)["nodes"]}

# ── Load existing validated relations ──
def load_relations() -> list[dict]:
    with open(ROOT / "ontology" / "relations.yaml") as f:
        return yaml.safe_load(f)["relations"]

# ── LLM-based cold start: score role pair correlations ──
def build_llm_correlation_prompt(nodes: dict) -> str:
    """Build a prompt asking the LLM to score all role-pair correlations."""
    roles = sorted(nodes.keys())
    role_descriptions = []
    for role in roles:
        n = nodes[role]
        role_descriptions.append(
            f"- **{role}** (L{n['layer']}, {n.get('domain','')}): {n['title']}"
        )
    
    return f"""You are evaluating organizational role correlations for a software engineering AI organization.

Below are {len(roles)} specialized roles. For every ordered pair (from_role → to_role), score how strongly the output of from_role should trigger, constrain, or inform the work of to_role.

SCORING GUIDE:
  0    = no relationship whatsoever
  1-10 = weak contextual relevance (might be useful as background)  
  11-30 = moderate (can provide useful constraints or context)
  31-60 = strong (should frequently activate, standard handoff)
  61-90 = very strong (critical dependency, almost always relevant)
  91-100 = essential (one cannot do meaningful work without the other's output)

Consider real software engineering organizational patterns:
- Architecture decisions constrain implementation
- Code review findings feed back to architecture improvement
- Scope decisions constrain product vision
- Security findings constrain all implementation
- Testing evaluates implementation
- Product vision constrains design and architecture
- Documentation augments API design
- Diagnostics trigger testing

The roles:

{chr(10).join(role_descriptions)}

For EVERY ordered pair (from_role → to_role), output a JSON object:
```json
{{
  "pairs": [
    {{"from": "triage", "to": "architect", "score": <0-100>, "reasoning": "<one sentence>"}},
    ...
  ]
}}
```

Output ALL {len(roles)}×{len(roles)-1} = {len(roles)*(len(roles)-1)} ordered pairs. Do not skip any.
Include "reasoning" for scores >= 30. For scores < 30, reasoning can be brief.

Important structural rules:
- Information flows forward (L1→L2→L3) more strongly than backward (L3→L2)
- Evaluation/adversary nodes (L3, perspective=adversary) feed BACK to their producers for improvement
- Supports/constrains are common; triggers/activates are rarer and should score higher
- Meta nodes (graph-topologist, hrbp, skill-scout) correlate weakly with regular nodes
- Entry nodes (L1) rarely receive from downstream nodes
"""

# ── Convert scores to Beta priors ──
def score_to_beta(score: float) -> tuple[float, float]:
    """
    Convert a 0-100 correlation score to Beta(alpha, beta) prior.
    High score → high alpha, low beta → distribution centered high, tight.
    Low score → low alpha, high beta → distribution centered low.
    Mid score → moderate alpha+beta → wide distribution (uncertain, explore).
    """
    s = score / 100.0  # normalize to 0-1
    
    if s >= 0.7:       # strong: tight high prior
        alpha = 5 + s * 20
        beta = 1 + (1-s) * 5
    elif s >= 0.3:     # moderate: wide prior (explore)
        alpha = 2 + s * 5
        beta = 2 + (1-s) * 5
    else:              # weak: tight low prior
        alpha = 1 + s * 3
        beta = 5 + (1-s) * 10
    
    return round(alpha, 4), round(beta, 4)


# ── Apply validated relation overrides ──
def apply_validated_overrides(
    matrix: dict, relations: list[dict], nodes: dict
) -> dict:
    """
    Override LLM priors with our validated relation weights.
    Validated edges get higher effective samples and adjusted Beta.
    """
    for rel in relations:
        fr, to = rel["from"], rel["to"]
        if fr not in nodes or to not in nodes:
            continue
        
        w = rel.get("weights", {})
        rtype = rel["type"]
        samples = 0
        
        # Extract sample count from any weight dimension
        for dim in w.values():
            if isinstance(dim, dict) and "samples" in dim:
                samples = max(samples, dim.get("samples", 0) or 0)
        
        # Edge types that activate: higher alpha
        if rtype in ("triggers", "may_trigger"):
            prob = 0.5
            for dim_name in ("probability",):
                if dim_name in w and isinstance(w[dim_name], dict):
                    prob = max(prob, float(w[dim_name].get("value", 0.5) or 0.5))
            
            # High-confidence validated edge: override with strong prior
            alpha = 3 + prob * 15 * max(1, samples + 1)
            beta = 3 + (1-prob) * 15
            
        elif rtype == "evaluates":
            # Evaluates edges: evaluator → producer (declared direction)
            # These should NOT activate from evaluator side.
            # Instead, the REVERSE (producer → evaluator) activates when producer completes.
            # Suppress evaluator→producer to near-zero.
            alpha, beta = 0.5, 15.0
            
            # Boost the producer→evaluator reverse direction (handled below in reverse key)
        
        elif rtype == "constrains":
            strength = w.get("strength", {})
            if isinstance(strength, dict):
                val = float(strength.get("value", 0.7) or 0.7)
                alpha = 2 + val * 8 * max(1, samples + 1)
                beta = 2 + (1-val) * 8
            else:
                alpha, beta = 6, 4
        
        elif rtype == "supports":
            necessity = w.get("necessity", {})
            if isinstance(necessity, dict):
                val = float(necessity.get("value", 0.5) or 0.5)
                alpha = 2 + val * 8 * max(1, samples + 1)
                beta = 3 + (1-val) * 8
            else:
                alpha, beta = 5, 5
        
        elif rtype in ("complements", "augments"):
            alpha, beta = 6, 4
        
        else:
            continue
        
        key = f"{fr}|{to}"
        matrix[key] = {
            "alpha": round(alpha, 4),
            "beta": round(beta, 4),
            "prior_mean": round(alpha / (alpha + beta), 4),
            "source": f"validated:{rtype}",
            "samples_used": samples,
        }
        # Also mark the reverse with source note
        rev_key = f"{to}|{fr}"
        if rev_key in matrix:
            matrix[rev_key]["validated_reverse"] = rtype
            # For evaluates: boost producer→evaluator reverse direction
            if rtype == "evaluates":
                strictness = w.get("strictness", {})
                if isinstance(strictness, dict):
                    val = float(strictness.get("value", 0.7) or 0.7)
                    blocking = strictness.get("blocking", {})
                    if isinstance(blocking, dict):
                        blocking_val = blocking.get("value", "advisory")
                    else:
                        blocking_val = blocking or "advisory"
                    if blocking_val == "required":
                        boost_alpha = 5 + val * 12 * max(1, samples + 1)
                        boost_beta = 2 + (1-val) * 5
                    else:
                        boost_alpha = 3 + val * 8 * max(1, samples + 1)
                        boost_beta = 3 + (1-val) * 6
                    matrix[rev_key]["alpha"] = round(boost_alpha, 4)
                    matrix[rev_key]["beta"] = round(boost_beta, 4)
                    matrix[rev_key]["prior_mean"] = round(boost_alpha / (boost_alpha + boost_beta), 4)
                    matrix[rev_key]["source"] = "producer_feedback"
    
    # ── Domain-based suppression: backend → design edges (non-validated) ──
    DESIGN_DOMAINS = {'immersive design', 'design systems', 'platform design', 'frontend', 'user experience'}
    BACKEND_DOMAINS = {'implementation', 'data', 'interface design', 'debugging', 'testing',
                       'code health', 'infrastructure', 'monitoring', 'performance', 'security',
                       'architecture', 'intake', 'product', 'planning', 'exploration', 'comprehension',
                       'simplification', 'research', 'product-scope', 'product-vision'}
    for key, val in matrix.items():
        if val.get('source', '').startswith('validated') or val.get('source') == 'producer_feedback':
            continue
        fr, to = key.split('|')
        fr_dom = nodes.get(fr, {}).get('domain', '')
        to_dom = nodes.get(to, {}).get('domain', '')
        if fr_dom in BACKEND_DOMAINS and to_dom in DESIGN_DOMAINS:
            val['alpha'] = 0.5
            val['beta'] = 12.0
            val['prior_mean'] = round(0.5 / 12.5, 4)
            val['source'] = 'suppressed_cross_domain'
    
    return matrix


# ── Main ──
def build_matrix(
    llm_scores: Optional[dict] = None,
    output_path: Optional[Path] = None,
) -> dict:
    nodes = load_nodes()
    relations = load_relations()
    roles = sorted(nodes.keys())
    
    matrix = {}
    
    if llm_scores:
        # Use LLM-provided scores
        for pair in llm_scores.get("pairs", []):
            fr, to, score = pair["from"], pair["to"], pair["score"]
            if fr == to:
                continue
            alpha, beta = score_to_beta(score)
            key = f"{fr}|{to}"
            matrix[key] = {
                "alpha": alpha,
                "beta": beta,
                "prior_mean": round(alpha / (alpha + beta), 4),
                "source": "llm_cognitive",
                "llm_score": score,
                "reasoning": pair.get("reasoning", ""),
            }
    else:
        # No LLM scores: uniform weak prior with forbiddenness for backward edges
        for fr in roles:
            for to in roles:
                if fr == to:
                    continue
                n_fr, n_to = nodes[fr], nodes[to]
                # Structural priors
                if n_fr["layer"] == 3 and n_to["layer"] == 1:
                    # L3→L1: nearly forbidden
                    alpha, beta = 0.5, 20.0
                elif n_fr["layer"] > n_to["layer"]:
                    # Backward: weak, wide prior
                    alpha, beta = 1.0, 8.0
                elif n_fr["layer"] == 1 and n_to["layer"] == 3:
                    # L1→L3: rare but possible (e.g., scope-prosecutor evaluating L1 output)
                    alpha, beta = 1.0, 6.0
                elif n_fr.get("meta") or n_to.get("meta"):
                    # Meta nodes: weak correlation
                    alpha, beta = 1.0, 10.0
                else:
                    # Forward L1→L2, L2→L3: moderate, wide prior
                    alpha, beta = 2.0, 5.0
                
                key = f"{fr}|{to}"
                matrix[key] = {
                    "alpha": alpha,
                    "beta": beta,
                    "prior_mean": round(alpha / (alpha + beta), 4),
                    "source": "structural_prior",
                }
    
    # Apply validated edge overrides
    matrix = apply_validated_overrides(matrix, relations, nodes)
    
    # Stats
    validated = sum(1 for v in matrix.values() if v["source"].startswith("validated"))
    llm_sourced = sum(1 for v in matrix.values() if v["source"] == "llm_cognitive")
    structural = sum(1 for v in matrix.values() if v["source"] == "structural_prior")
    
    result = {
        "schema": "silicon_org.weight_matrix.v1",
        "nodes": len(roles),
        "total_edges": len(matrix),
        "sources": {
            "validated": validated,
            "llm_cognitive": llm_sourced,
            "structural_prior": structural,
        },
        "matrix": matrix,
    }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
    
    return result


if __name__ == "__main__":
    # Without LLM: generate structural priors + validated overrides
    result = build_matrix(output_path=ROOT / "ontology" / "weight_matrix.json")
    print(f"Built {result['nodes']}×{result['nodes']} = {result['total_edges']} edge matrix")
    print(f"  validated: {result['sources']['validated']}")
    print(f"  structural_prior: {result['sources']['structural_prior']}")
    
    # Print top 20 edges by prior mean
    pairs = sorted(result["matrix"].items(), key=lambda x: -x[1]["prior_mean"])
    print("\nTop edges by prior mean:")
    for key, val in pairs[:20]:
        fr, to = key.split("|")
        print(f"  {fr:25s} → {to:25s} mean={val['prior_mean']:.3f} α={val['alpha']:.1f} β={val['beta']:.1f} [{val['source']}]")
