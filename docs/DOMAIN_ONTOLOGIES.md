# Domain Ontology Reference

Reference library for domain modeling in Silicon Org. Use when `architect`,
`database-engineer`, or `ai-engineer` needs to model a new domain — start
from the relevant template before designing from scratch.

Source: neo4j-labs/create-context-graph (667 ⭐, official Neo4j Labs repo)

---

## Foundation: POLE+O Model

All 27 domain templates extend a shared base. When no domain template fits,
start here and extend.

```yaml
entity_types:
  Person:
    required: [name]
    optional: [email, role, description]

  Organization:
    required: [name]
    optional: [description, industry]

  Location:
    required: [name]
    optional: [address, latitude, longitude]

  Event:
    required: [name]
    optional: [date, description]

  Object:
    required: [name]
    optional: [description]

base_relationships:
  - WORKS_FOR: Person → Organization
  - LOCATED_AT: Organization → Location
  - PARTICIPATED_IN: Person → Event
```

POLE+O = **P**erson, **O**rganization, **L**ocation, **E**vent + **O**bject.
Every domain adds domain-specific entity subtypes and relationship types on top
of this foundation.

---

## Available Domain Templates

27 pre-built domains covering common industry verticals. Most relevant to
Silicon Org workloads are starred.

| Domain | File | Notes |
|---|---|---|
| ⭐ Software Engineering | `software-engineering.yaml` | Repo, Service, Issue, PR, Deployment, Incident |
| ⭐ GenAI / LLM Ops | `genai-llm-ops.yaml` | Model, Experiment, Dataset, Prompt, Evaluation |
| ⭐ Product Management | `product-management.yaml` | Feature, Roadmap, Sprint, Stakeholder |
| Agent Memory | `agent-memory.yaml` | Memory, Context, Session, Knowledge |
| Personal Knowledge | `personal-knowledge.yaml` | Note, Concept, Source, Connection |
| Financial Services | `financial-services.yaml` | |
| Healthcare | `healthcare.yaml` | Patient, Provider, Diagnosis, Treatment |
| Retail & E-Commerce | `retail-ecommerce.yaml` | |
| Manufacturing | `manufacturing.yaml` | |
| Scientific Research | `scientific-research.yaml` | |
| Cybersecurity | `cybersecurity.yaml` | |
| Legal | `legal.yaml` | |
| Education | `education.yaml` | |
| Government | `government.yaml` | |
| Real Estate | `real-estate.yaml` | |
| Digital Twin | `digital-twin.yaml` | |
| Options Intelligence | `options-intelligence.yaml` | |
| Data Journalism | `data-journalism.yaml` | |
| GIS & Cartography | `gis-cartography.yaml` | |
| Oil & Gas | `oil-gas.yaml` | |
| Wildlife Management | `wildlife-management.yaml` | |
| Conservation | `conservation.yaml` | |
| Gaming | `gaming.yaml` | |
| Golf & Sports Mgmt | `golf-sports.yaml` | |
| Trip Planning | `trip-planning.yaml` | |
| Vacation & Hospitality | `vacation-industry.yaml` | |
| Hospitality | `hospitality.yaml` | |

Full templates: https://github.com/neo4j-labs/create-context-graph/tree/main/src/create_context_graph/domains

---

## Software Engineering Domain (detail)

Most directly applicable to Silicon Org tasks.

```yaml
entity_types:
  # Objects
  Repository:   [language, visibility, default_branch]
  Service:      [type, health_status, owner_team]

  # Events
  Issue:        [priority, status]
  PullRequest:  [status, review_count, merged]
  Deployment:   [environment, success, timestamp]
  Incident:     [severity, resolved, resolution_time]

key_relationships:
  - PullRequest FIXES Issue
  - Deployment TRIGGERED_BY PullRequest
  - Deployment CAUSED_INCIDENT
  - Incident AFFECTED Service
  - Service DEPENDS_ON Service         # dependency mapping
  - PullRequest BELONGS_TO Repository
```

---

## GenAI / LLM Ops Domain (detail)

Applicable when `ai-engineer` is designing ML/LLM infrastructure.

```yaml
entity_types:
  Model:       [architecture, parameter_count, status]
  Experiment:  [hypothesis, outcome, metrics]
  Dataset:     [format, size, split_type]
  Prompt:      [type, version, template]          # type: system|user|few-shot
  Evaluation:  [benchmark, metric, score]
  Deployment:  [environment, canary_weight]       # dev|staging|canary|production

key_relationships:
  - Model FINE_TUNED_FROM Model        # model lineage
  - Model TRAINED_ON Dataset
  - Experiment USES Prompt
  - Evaluation ASSESSES Model
  - Model DEPLOYED_TO Deployment
```

---

## How to Use These Templates

1. **Identify the closest domain** from the table above
2. **Extend POLE+O** — add your domain-specific entity subtypes as Object
   or Event subclasses; reuse Person/Organization/Location as-is where possible
3. **Name relationships with VERB_NOUN convention** (FINE_TUNED_FROM, not
   "finetuned") — matches the silicon org ontology edge naming convention
4. **Minimum viable ontology**: 3–6 entity types, 5–10 relationship types.
   More is not better — every entity type added is a modeling commitment that
   costs downstream query complexity.
5. **Record the domain template used** in `key_decisions` of the architect
   or database-engineer completion report

---

## Silicon Org Graph vs. Domain Ontology

Silicon Org's `ontology/nodes.yaml` + `ontology/relations.yaml` is itself an
ontology of agent roles and activation relations — not a domain data model.
The templates above are for **task-level domain modeling**: when a task
involves designing the data schema for a new product or service.

Do not conflate the two. The role graph topology is maintained by
`graph-topologist`; domain data models for user products are what these
templates support.
