"""Skill Planner — generates coordinated action sequences from natural language.

The planner reads robot_context() (skills + constraints + capabilities),
sends it to an LLM, and returns a validated plan that respects all
coordination constraints from INDEX.yaml.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..composer import Bootstrap
from ..brain import chat as llm_chat, get_config


PLAN_SYSTEM_PROMPT = """You are a robot action planner. You receive:
1. A user's instruction in natural language
2. The robot's current skills (what it can do)
3. Coordination constraints between skills

Generate a plan as a JSON array of steps. Each step is:
{
  "skill": "<skill_name>",
  "action": "<action_name>",
  "params": {<action parameters>},
  "facial": "<optional: smile|neutral|concerned|happy>",
  "reason": "<one-line explanation of why this step>"
}

Available actions (MUST use these EXACT names, no alternatives):
  skill=move  → action=set_forward_velocity  params={forward_velocity: number 0.0~1.0}
  skill=move  → action=rotate              params={angular_velocity: number -0.5~0.5}
  skill=move  → action=stop                params={}
  skill=speak → action=speak               params={text: "string"}
  skill=perception, safety, diagnostics, pilot → observation skills, no actions
  skill=grip  → action=grip                params={target: "string"}
  skill=grip  → action=place               params={target: "string"}

Rules:
- Only use skills and actions listed above.
- Respect ALL coordination constraints:
  - conflicts_with: never schedule two conflicting skills in the same step
  - requires: ensure required skills are available before using a skill
  - priority: when unsure, higher-priority skill takes precedence
- If a constraint forces serial execution (e.g. grip + move can't run together),
  break them into sequential steps.
- Include speak actions for any communication with humans.
- facial is optional: smile for greetings/welcome, concerned for warnings/problems.
- For move, always use safe speeds (0.2-0.5).
- Output ONLY the JSON array, no markdown, no explanation outside the array.
"""


@dataclass
class PlanStep:
    skill: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    facial: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = {"skill": self.skill, "action": self.action, "params": self.params, "reason": self.reason}
        if self.facial:
            d["facial"] = self.facial
        return d


@dataclass
class PlanResult:
    plan: list[PlanStep]
    raw_response: str
    warnings: list[str] = field(default_factory=list)
    valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "plan": [s.to_dict() for s in self.plan],
            "warnings": self.warnings,
        }


class Planner:
    """Generates and validates action plans from natural language."""

    def __init__(self, runtime: Bootstrap, *, model: str | None = None):
        self.runtime = runtime
        self.model = model  # None = auto-detect from engine config
        self._constraints = self._build_constraint_index()

    def _build_constraint_index(self) -> dict[str, dict[str, Any]]:
        """Build a lookup of constraint data per skill."""
        idx: dict[str, dict[str, Any]] = {}
        for s in self.runtime.skills_index:
            name = s.get("name", "")
            idx[name] = {
                "conflicts_with": s.get("conflicts_with", []),
                "requires": s.get("requires", []),
                "priority_lower_than": s.get("priority_lower_than", []),
                "interferes_with": s.get("interferes_with", []),
                "governs": s.get("governs", []),
            }
        return idx

    def build_prompt(self, instruction: str) -> str:
        """Build the LLM prompt with robot context."""
        ctx = self.runtime.robot_context()
        skills_summary = []
        for s in self.runtime.skills_index:
            name = s["name"]
            desc = s.get("description", "")
            constr = self._constraints.get(name, {})
            parts = [f"  {name}: {desc}"]
            if constr.get("conflicts_with"):
                parts.append(f"    conflicts_with: {constr['conflicts_with']}")
            if constr.get("requires"):
                parts.append(f"    requires: {constr['requires']}")
            skills_summary.append("\n".join(parts))

        actions_summary = ctx.get("capabilities", {}).get("actions", [])
        action_lines = []
        for a in actions_summary[:20]:  # limit to avoid context overflow
            action_lines.append(
                f"  {a.get('id','?')} "
                f"[{a.get('safety_class','?')}]: {a.get('description','')}"
            )

        prompt = f"""Instruction: {instruction}

Robot Skills:
{chr(10).join(skills_summary)}

Available Actions:
{chr(10).join(action_lines) if action_lines else "  (see ontology for full list)"}

Generate a plan as JSON array. Rules in system prompt."""
        return prompt

    async def generate_plan(self, instruction: str) -> PlanResult:
        """Generate and validate a plan from natural language instruction."""
        prompt = self.build_prompt(instruction)
        try:
            config = get_config()
            provider = config.get("provider", "")
            model = self.model or config.get("model", "")
            # Reasoning models (deepseek-v4-pro) output thinking text, not JSON.
            # Fall back to chat model.
            if "v4-pro" in model or "reasoner" in model.lower():
                model = "deepseek-chat"
            response = await llm_chat(
                prompt,
                system=PLAN_SYSTEM_PROMPT,
                max_tokens=1024,
                temperature=0.3,
                provider=provider,
                model=model,
            )
        except Exception as e:
            return PlanResult(plan=[], raw_response="", warnings=[f"LLM call failed: {e}"], valid=False)

        raw = response.get("reply", "")
        if not raw:
            return PlanResult(plan=[], raw_response=raw, warnings=["LLM returned empty response"], valid=False)

        steps = self._parse_plan(raw)
        if not steps:
            return PlanResult(plan=[], raw_response=raw,
                            warnings=[f"Failed to parse plan from LLM response. Raw: {raw[:300]}"], valid=False)

        warnings = self._validate(steps)
        return PlanResult(plan=steps, raw_response=raw, warnings=warnings, valid=len(warnings) == 0)

    def _parse_plan(self, raw: str) -> list[PlanStep]:
        """Extract plan JSON from LLM response."""
        # Try direct JSON parse first
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [PlanStep(**s) for s in data]
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting JSON array
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                if isinstance(data, list):
                    return [PlanStep(**s) for s in data]
            except (json.JSONDecodeError, TypeError):
                pass

        # Try wrapping in array
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group())
                if isinstance(obj, dict):
                    return [PlanStep(**obj)]
            except (json.JSONDecodeError, TypeError):
                pass

        return []

    def _validate(self, steps: list[PlanStep]) -> list[str]:
        """Validate plan against coordination constraints. Returns warnings."""
        warnings = []
        skill_names = {s["name"] for s in self.runtime.skills_index}
        action_ids = set()
        ontology_available = False
        try:
            actions = self.runtime.describe_resources(kind="ontology.action")
            action_ids = {a["id"] for a in actions}
            ontology_available = len(action_ids) > 0
        except Exception:
            pass

        for i, step in enumerate(steps):
            # Skill exists?
            if step.skill not in skill_names:
                warnings.append(f"Step {i+1}: unknown skill '{step.skill}'")

            # Action exists? (only check if ontology is loaded)
            if ontology_available and step.action not in action_ids:
                # Allow common actions that are known to exist
                common_actions = {"speak", "set_forward_velocity", "rotate", "stop",
                                  "grip", "place", "observe"}
                if step.action not in common_actions:
                    warnings.append(f"Step {i+1}: unknown action '{step.action}'")

            # Conflicts check — adjacent steps cannot START conflicting skills
            # without releasing the previous one first.
            c = self._constraints.get(step.skill, {})
            if i > 0:
                prev = steps[i - 1]
                releases = {"move": "stop", "grip": "place"}
                if prev.skill in c.get("conflicts_with", []):
                    # Previous skill's release action? ok
                    release_action = releases.get(prev.skill)
                    if prev.action == release_action:
                        pass  # move.stop → grip is fine
                    elif step.action == release_action:
                        pass  # grip.place → move is fine
                    else:
                        warnings.append(
                            f"Step {i+1}: '{step.skill}' after '{prev.skill}' — "
                            f"these conflict. Release '{prev.skill}' before '{step.skill}'."
                        )

            # Requires check
            for req in c.get("requires", []):
                if req not in [s.skill for s in steps]:
                    warnings.append(
                        f"Step {i+1}: skill '{step.skill}' requires '{req}' "
                        f"but '{req}' is not in the plan."
                    )

        return warnings

    # ── Synchronous wrapper for daemon dispatch ──

    def plan(self, instruction: str) -> dict[str, Any]:
        """Synchronous wrapper for daemon command dispatch."""
        async def _run():
            return await self.generate_plan(instruction)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    fut = pool.submit(asyncio.run, _run())
                    return fut.result(timeout=120).to_dict()
            return loop.run_until_complete(_run()).to_dict()
        except RuntimeError:
            return asyncio.run(_run()).to_dict()
