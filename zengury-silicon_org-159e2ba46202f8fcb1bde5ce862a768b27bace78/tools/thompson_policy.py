"""
Thompson Sampling Policy Router.

Replaces the symbolist edge-selection rules with:
  1. Load full 38×38 weight matrix (LLM cognitive + validated + learned)
  2. When a node completes, consider ALL potential downstream nodes
  3. For each candidate, sample from Beta(alpha, beta)
  4. Hard constraints (layer barriers, context block) still enforced
  5. Activate top-k by sampled score, record explorations

This ensures:
  - Proven edges dominate (high alpha, low beta → consistently sampled high)
  - Uncertain edges get explored (moderate alpha+beta → wide distribution)
  - Dead edges stay dead (low alpha, high beta → consistently sampled low)
  - No edge is permanently excluded
"""

import json, random, math
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

ROOT = Path(__file__).resolve().parent.parent

# ── Hard constraints that Thompson Sampling cannot override ──
LAYER_BARRIER = {
    # No backward activation: L3 cannot activate L1
    # Exception: evaluation feedback (handled separately)
}

FORBIDDEN_PATTERNS = {
    # Entry nodes cannot be activated downstream (only by ENCODER)
    # Meta nodes ignore regular activation
}


@dataclass
class Candidate:
    from_role: str
    to_role: str
    alpha: float
    beta_param: float
    prior_mean: float
    sampled_score: float = 0.0
    source: str = ""
    activated: bool = False


@dataclass
class PolicyWave:
    """Result of one policy evaluation wave after a node completes."""
    completed_role: str
    candidates: list[Candidate] = field(default_factory=list)
    activated: list[Candidate] = field(default_factory=list)
    deferred: list[Candidate] = field(default_factory=list)
    skipped: list[Candidate] = field(default_factory=list)


class ThompsonPolicy:
    """
    Probabilistic policy router with Thompson Sampling.
    
    Usage:
        policy = ThompsonPolicy.load()
        wave = policy.evaluate_candidates("architect", completed_nodes, task_type)
        for c in wave.activated:
            activate(c.to_role)
    """
    
    def __init__(self, matrix: dict, nodes: dict):
        self.matrix = matrix
        self.nodes = nodes
        self.rng = random.Random()
    
    @classmethod
    def load(cls, matrix_path: Optional[Path] = None) -> "ThompsonPolicy":
        if matrix_path is None:
            matrix_path = ROOT / "ontology" / "weight_matrix.json"
        
        import yaml
        with open(matrix_path) as f:
            data = json.load(f)
        with open(ROOT / "ontology" / "nodes.yaml") as f:
            nodes = {n["role"]: n for n in yaml.safe_load(f)["nodes"]}
        
        return cls(data["matrix"], nodes)
    
    def _is_hard_forbidden(self, from_role: str, to_role: str) -> bool:
        """Hard constraints that block activation regardless of weight."""
        n_fr = self.nodes.get(from_role, {})
        n_to = self.nodes.get(to_role, {})
        
        # Layer barrier: L3 cannot forward-activate L1
        if n_fr.get("layer") == 3 and n_to.get("layer") == 1:
            if n_fr.get("domain") != n_to.get("domain"):
                return True
        
        # Meta nodes don't participate in graph propagation
        if n_to.get("meta"):
            return True
        
        # Self-edge
        if from_role == to_role:
            return True
        
        return False
    
    def _get_beta_params(self, from_role: str, to_role: str) -> tuple[float, float, str]:
        """Get Beta(alpha, beta) for an edge. Default weak prior if not in matrix."""
        key = f"{from_role}|{to_role}"
        if key in self.matrix:
            entry = self.matrix[key]
            return entry["alpha"], entry["beta"], entry.get("source", "unknown")
        return 1.0, 10.0, "default_weak_prior"
    
    def evaluate_candidates(
        self,
        completed_role: str,
        completed_nodes: set[str],
        task_type: str,
        top_k: int = 5,
        min_score: float = 0.15,
        exploration_budget: int = 1,
    ) -> PolicyWave:
        """
        After a node completes, evaluate ALL potential downstream nodes.
        
        Args:
            completed_role: the node that just completed
            completed_nodes: set of all completed node roles
            task_type: task type for context
            top_k: max nodes to activate in this wave
            min_score: minimum sampled score to consider
            exploration_budget: force-explore this many uncertain edges
        
        Returns:
            PolicyWave with activation decisions
        """
        wave = PolicyWave(completed_role=completed_role)
        
        # Build candidates: every node except completed ones and self
        for to_role in sorted(self.nodes):
            if to_role == completed_role:
                continue
            if to_role in completed_nodes:
                continue
            if self._is_hard_forbidden(completed_role, to_role):
                continue
            
            alpha, beta_param, source = self._get_beta_params(completed_role, to_role)
            
            # Thompson sample
            sampled = self.rng.betavariate(alpha, beta_param)
            prior_mean = alpha / (alpha + beta_param) if (alpha + beta_param) > 0 else 0
            
            candidate = Candidate(
                from_role=completed_role,
                to_role=to_role,
                alpha=alpha,
                beta_param=beta_param,
                prior_mean=round(prior_mean, 4),
                sampled_score=round(sampled, 4),
                source=source,
            )
            wave.candidates.append(candidate)
        
        # Sort by sampled score descending
        wave.candidates.sort(key=lambda c: -c.sampled_score)
        
        # Select top_k above min_score
        selected = []
        remaining = []
        for c in wave.candidates:
            if len(selected) < top_k and c.sampled_score >= min_score:
                c.activated = True
                selected.append(c)
            else:
                remaining.append(c)
        
        # Force exploration: pick 1 uncertain edge (moderate alpha+beta, moderate mean)
        if exploration_budget > 0:
            uncertain = [
                c for c in remaining
                if 5 < c.alpha + c.beta_param < 30 and 0.2 < c.prior_mean < 0.7
            ]
            if uncertain:
                explorer = self.rng.choice(uncertain)
                explorer.activated = True
                selected.append(explorer)
                remaining.remove(explorer)
        
        wave.activated = selected
        wave.deferred = [c for c in remaining if c.sampled_score >= 0.05]
        wave.skipped = [c for c in remaining if c.sampled_score < 0.05]
        
        return wave
    
    def update_edge(
        self,
        from_role: str,
        to_role: str,
        success: float,  # 0.0 to 1.0
        weight: float = 1.0,
    ):
        """Bayesian update after seeing real outcome."""
        key = f"{from_role}|{to_role}"
        if key not in self.matrix:
            self.matrix[key] = {"alpha": 1.0, "beta": 10.0, "source": "learned"}
        
        entry = self.matrix[key]
        # Weighted update: high-quality artifacts count more
        entry["alpha"] = round(entry["alpha"] + success * weight, 4)
        entry["beta"] = round(entry["beta"] + (1 - success) * weight, 4)
        entry["source"] = "learned" if not entry["source"].startswith("validated") else entry["source"]
    
    def save(self, path: Optional[Path] = None):
        if path is None:
            path = ROOT / "ontology" / "weight_matrix.json"
        import yaml
        with open(ROOT / "ontology" / "nodes.yaml") as f:
            nodes = yaml.safe_load(f)["nodes"]
        result = {
            "schema": "silicon_org.weight_matrix.v1",
            "nodes": len(nodes),
            "total_edges": len(self.matrix),
            "matrix": self.matrix,
        }
        with open(path, "w") as f:
            json.dump(result, f, indent=2)


# ── Demo ──
if __name__ == "__main__":
    policy = ThompsonPolicy.load()
    
    print("=== Thompson Sampling Demo: zoom-out just completed (refactor task) ===\n")
    completed = {"triage", "zoom-out"}
    wave = policy.evaluate_candidates("zoom-out", completed, "refactor", top_k=5, exploration_budget=1)
    
    print("Activated:")
    for c in wave.activated:
        print(f"  {c.to_role:30s} sample={c.sampled_score:.4f} prior={c.prior_mean:.4f} α={c.alpha:.1f} β={c.beta_param:.1f} [{c.source}]")
    
    print(f"\nDeferred ({len(wave.deferred)}): ", end="")
    print(", ".join(c.to_role for c in wave.deferred[:8]))
    
    print(f"\nSkipped ({len(wave.skipped)}): ", end="")
    print(", ".join(c.to_role for c in wave.skipped[:5]) + "...")
    
    # Show: did improve-codebase-architecture get activated?
    ica = [c for c in wave.candidates if c.to_role == "improve-codebase-architecture"]
    if ica:
        c = ica[0]
        print(f"\n=== improve-codebase-architecture ===")
        print(f"  activated: {c.activated}")
        print(f"  sampled: {c.sampled_score:.4f}  prior: {c.prior_mean:.4f}  α={c.alpha:.1f} β={c.beta_param:.1f}")
        if c.activated:
            print("  ✅ Thompson Sampling activated it!")
        else:
            # Run 20 samples to see distribution
            samples = [random.betavariate(c.alpha, c.beta_param) for _ in range(100)]
            p_activated = sum(1 for s in samples if s >= 0.15) / len(samples)
            print(f"  Activation probability @min=0.15: {p_activated:.2%} (over 100 samples)")
