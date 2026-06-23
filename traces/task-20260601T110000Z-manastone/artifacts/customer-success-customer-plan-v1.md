# Customer Success Plan: Manastone Robot Agent Platform

## Executive Summary
Manastone is a robot agent platform that lets you control and diagnose robots using natural language. No coding required. One install command, zero configuration, and you're up and running. This plan outlines how we'll ensure your team gets maximum value from Manastone in the first 90 days.

## 30/60/90 Day Milestones

### Days 1–30: Foundation & First Robot
- **Week 1**: Install Manastone on one robot (X2 or G1). Run `manastone doctor` to verify. Complete onboarding guide.
- **Week 2**: Basic natural language commands: move, stop, check status. Team lead completes training.
- **Week 3**: Explore diagnosis features: run `manastone diagnose` on a known issue. Log first success story.
- **Week 4**: Review with CSM. Measure: time to first successful command, number of commands used.

### Days 31–60: Adoption & Expansion
- **Week 5–6**: Install on additional robots (up to 3). Train 2 more team members.
- **Week 7–8**: Integrate into daily workflow: use Manastone for routine checks and troubleshooting.
- **Week 8**: Mid-point review. Measure: commands per day, robot uptime improvement, support ticket reduction.

### Days 61–90: Optimization & ROI
- **Week 9–10**: Advanced features: custom diagnostics, multi-robot commands.
- **Week 11**: Full team training (all operators).
- **Week 12**: Final review. Measure: time saved per week, cost savings, NPS score.

## Training Plan

| Role | Training Content | Date | Duration |
|------|------------------|------|----------|
| Robot Operator (Lead) | Install, basic commands, diagnosis | Day 1 | 2 hours |
| Robot Operator (Team) | Daily workflow, troubleshooting | Day 30 | 1 hour |
| All Operators | Advanced features, best practices | Day 60 | 1 hour |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Installation fails due to network/OS | Medium | High | Pre-flight check in install script; fallback manual steps documented |
| Team resistance to new tool | Medium | Medium | Show quick wins in week 1; assign champion |
| Robot compatibility issues | Low | High | Test on target robot before install; `manastone doctor` validates |
| Feature gaps discovered | Medium | Medium | Prioritize in v1.1; provide workaround |

## Communication Cadence

- **Weekly**: 15-min check-in (first 30 days)
- **Bi-weekly**: 30-min review (days 31–90)
- **Monthly**: Email summary with metrics
- **Ad-hoc**: Slack/email for urgent issues

## KPI Framework

| Category | Metric | Baseline | Target | Measurement Method |
|----------|--------|----------|--------|--------------------|
| Efficiency | Time to diagnose robot issue | 30 min (manual) | 5 min | `manastone diagnose` log timestamps |
| Efficiency | Commands per day per operator | 0 | 10 | Usage analytics |
| Quality | Robot uptime | 85% | 95% | Robot logs |
| Quality | Successful command rate | N/A | 95% | Command success logs |
| Cost | Support tickets per week | 5 | 2 | Support system |
| Cost | Operator training time | 4 hours | 1 hour | Training logs |
| Satisfaction | NPS score | N/A | 50+ | Survey at day 90 |

## ROI Calculation

**Assumptions**:
- Team size: 3 operators
- Robot fleet: 3 robots (X2 or G1)
- Current diagnostic time: 30 min/issue, 10 issues/week
- Operator hourly cost: $50
- Manastone license: $0 (open source, self-hosted)
- Implementation cost: 8 hours of operator time ($400)

**Cost Savings**:
- Diagnostic time reduction: from 30 min to 5 min = 25 min saved per issue
- Weekly savings: 10 issues × 25 min = 250 min = 4.17 hours
- Weekly cost savings: 4.17 hours × $50 = $208.50
- Monthly savings: $834
- Annual savings: $10,008

**Payback Period**:
- Implementation cost: $400
- Weekly savings: $208.50
- Payback: 400 / 208.50 = 1.92 weeks (≈2 weeks)

**Scenarios**:
| Scenario | Annual Savings | Payback Period |
|----------|----------------|----------------|
| Conservative (5 issues/week) | $5,004 | 3.8 weeks |
| Expected (10 issues/week) | $10,008 | 1.9 weeks |
| Optimistic (15 issues/week) | $15,012 | 1.3 weeks |

## Onboarding Guide (Getting Started)

### Step 1: Install Manastone
Open a terminal on your robot's computer and run:
```bash
bash <(curl -s https://manastone.dev/install.sh)
```
Follow the on-screen prompts. The installer will:
- Check prerequisites (Python, Node.js)
- Install the conversation engine (hidden, no action needed)
- Install Manastone and robot-specific tools
- Auto-detect your robot model
- Verify everything works with `manastone doctor`

### Step 2: Verify Installation
Run:
```bash
manastone doctor
```
You should see a green checkmark for all checks. If not, follow the suggested fix.

### Step 3: Chat with Your Robot
Run:
```bash
manastone-chat
```
You'll see a welcome message. Try these commands:
- "What is the current status of the robot?"
- "Move forward 0.5 meters"
- "Check joint temperatures"
- "Diagnose any issues"

### Step 4: Daily Workflow
1. Start your day: `manastone doctor` to check robot health
2. During operation: use natural language commands
3. If issue arises: `manastone diagnose` to get instant analysis
4. End of day: review logs with `manastone recall`

### Troubleshooting
| Problem | Solution |
|---------|----------|
| `manastone` command not found | Re-run install script or add `~/.manastone/bin` to PATH |
| Robot not detected | Check robot is powered on and connected; run `manastone doctor` |
| Command fails | Check robot model in `~/.manastone/config.yaml` |
| Engine not responding | Restart with `manastone-launcher restart` |

### Glossary
- **Manastone**: The robot agent platform
- **Engine**: The conversation AI that understands your commands
- **Doctor**: Health check tool
- **Diagnose**: Troubleshooting tool
- **Robot Pack**: Pre-built configuration for your robot model

## Brand Independence Audit

All user-facing touchpoints use "Manastone" branding exclusively. The pi coding agent is installed as a hidden dependency under `~/.manastone/engine/` and is never exposed. Audit checklist:
- [ ] CLI output uses "Manastone" in all messages
- [ ] Error messages reference Manastone, not pi
- [ ] Log files prefix with `[Manastone]`
- [ ] TUI title shows "Manastone"
- [ ] Install script shows "Manastone" throughout
- [ ] `manastone doctor` reports "Manastone"
- [ ] No pi logo or name in any user-facing output

## Completion Report

```yaml
completion_report:
  what_was_done: Produced customer success plan with 30/60/90 milestones, training plan, risk register, communication cadence, KPI framework with baselines and targets, ROI calculation with conservative/expected/optimistic scenarios, onboarding guide for non-technical users, and brand independence audit checklist.
  key_decisions:
    - decision: Focus on time-to-value in first 30 days with single-robot install
      rationale: Quick wins build confidence and adoption momentum
    - decision: KPI baselines set to current manual process metrics
      rationale: Enables clear before/after comparison for ROI
    - decision: Training phased by role (lead first, then team)
      rationale: Champion-led adoption reduces resistance
  handoff_focus:
    - Implement brand audit script (brand_audit.py)
    - Update install script to ensure pi brand is hidden
    - Create GETTING_STARTED.md with onboarding content
    - Extend manastone doctor checks for brand compliance
  open_questions:
    - What specific user guidance materials are needed beyond the install script?
    - How will brand independence be audited across all touchpoints?
  known_constraints:
    - Must hide pi brand and present Manastone as independent
    - Install must include all dependencies (pi coding agent)
    - User guidance must be optimized for clarity
    - Internal build tools and daemon deployment are deferred to v1.1
  confidence_differential: 0.90
  dissent_if_alone: null
```