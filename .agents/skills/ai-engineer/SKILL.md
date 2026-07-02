---
name: ai-engineer
description: Specify the LLM layer of a system — context budget, retrieval pipeline, model selection, hallucination mitigation, cost model, and fallbacks — with every tradeoff made explicit; use when a task involves LLMs, RAG, embeddings, agents, or model context.
---

## Purpose

Mastery of this skill produces an AI integration specification with the same
rigor an architect applies to service topology. It covers the decisions that
determine whether an AI-powered system actually works in production: how context
is budgeted, how retrieval pipelines are tuned, how hallucination risk is
managed, and how cost compounds at volume. Every decision names what it
optimizes for and what it gives up. An AI component without a stated context
budget, fallback, and cost model is not specified — it is a sketch.

## When to use

- A task mentions AI features, LLMs, RAG, embeddings, vector stores, agents, or
  model context.
- An architecture document references AI or LLM components to be designed.
- A product spec requires AI-powered features that need a concrete design.

## Method

1. Set the context budget. State explicitly what is always in context, what is
   retrieved on demand, and what is never included. Verify the always-in-context
   portion plus retrieved content sums to less than the chosen model's context
   limit.
2. Design the retrieval pipeline. Specify chunking strategy, embedding model,
   index type, retrieval k, and whether retrieval is dense or hybrid — each with
   a rationale, not a default.
3. Select the model with justification. Name not just which model but why this
   capability tier at this latency and cost point. State the tradeoff you are
   accepting.
4. Build the cost model. Estimate tokens per call at P50 volume against the
   chosen model's specific pricing tier; extend to P95 with sensitivity analysis
   where volume is uncertain.
5. Address hallucination risk. Name the grounding mechanism and confidence
   threshold, or explicitly acknowledge that the use case tolerates hallucination
   and why. Define the degradation path when confidence is low.
6. Decide RAG versus fine-tuning. If both were genuinely considered, document
   the decision and its rationale.
7. Name orchestration patterns. If more than one model is used, specify the
   router and specialist roles and justify the split.
8. Define a fallback for every AI component. For each, state its failure mode
   and the fallback behavior when the model is unavailable or returns output
   outside the expected schema. Every AI component appears in the fallback table.
9. Draw the pipeline. Include a text-form ASCII or Mermaid diagram of the flow.

## Quality bar

- RAG design states chunking, embedding model, index type, and retrieval k with
  rationale.
- Context budget is explicit and sums to less than the model's context limit.
- Cost model states estimated tokens per call at P50 against a named pricing
  tier.
- Hallucination risk is grounded or its tolerance is explicitly acknowledged.
- Model selection is justified by capability tier, latency, and cost — not name.
- Every AI component has a stated fallback and appears in the fallback table.
- RAG-versus-fine-tune and multi-model orchestration are documented if relevant.

## Output

An inline AI integration specification covering context budget, retrieval
pipeline, model selection, hallucination mitigation, RAG-versus-fine-tune
decision, orchestration pattern, and a fallback table, plus a text-form pipeline
diagram. Optionally, a cost analysis at P50 and P95 volume with sensitivity
analysis.

## Anti-patterns

- Recommending a model, chunking strategy, or architecture with no stated
  tradeoff.
- Deferring context budget, fallback, or cost decisions to implementation.
- Leaving hallucination risk unaddressed and unacknowledged.
- Sizing cost with no reference to a specific model's pricing tier.
- Omitting the fallback for a component, so schema-invalid model output crashes
  the flow.
