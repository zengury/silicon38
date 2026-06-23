# Customer Success Plan: Demonstration-Taught Guided Tour System

## Product Overview
Manastone Tour is a voice-controlled guided tour system for humanoid robots (Unitree G1, Agibot X2). Operators teach tours by walking the robot through a path while speaking narration; the robot then autonomously replays the tour with narration. No programming required — just speak commands.

## 30/60/90 Day Success Plan

### Days 1–30: Onboarding & First Tour
- **Week 1**: Install Manastone Tour on robot (guided install script). Complete 30-minute voice command training. Record first 3-waypoint tour.
- **Week 2**: Run first guided tour for internal team. Collect feedback on narration quality and navigation smoothness.
- **Week 3**: Refine tour based on feedback. Record 5-waypoint tour with full narration.
- **Week 4**: Present tour to stakeholders. Document lessons learned.
- **Milestone**: Operator can independently create and run a tour. At least one tour is production-ready.

### Days 31–60: Adoption & Expansion
- **Week 5–6**: Train 2 additional operators (train-the-trainer). Each creates a tour.
- **Week 7**: Deploy tour for live customer-facing use (e.g., facility tour, product demo).
- **Week 8**: Collect usage metrics (tours created, tours run, operator satisfaction). Identify top use cases.
- **Milestone**: 3+ operators trained. Tours used in at least one customer-facing scenario.

### Days 61–90: Optimization & ROI
- **Week 9–10**: Analyze tour performance data. Optimize narration scripts and waypoint placement.
- **Week 11**: Create tour library (5+ reusable tours). Document best practices.
- **Week 12**: Present ROI report to leadership. Plan next phase (multi-language tours, integration with scheduling).
- **Milestone**: Tour library established. ROI demonstrated with time savings.

## Training Plan

| Role | Training Content | Duration | Date |
|------|-----------------|----------|------|
| Lead Operator (1 person) | Voice commands, teaching workflow, troubleshooting | 2 hours | Day 1 |
| Additional Operators (2 people) | Same as above, plus shadowing lead | 3 hours | Day 30–35 |
| Manager/Stakeholder | Tour capabilities, use cases, ROI metrics | 30 min | Day 7 |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Voice recognition fails in noisy environment | Medium | High | Use headset microphone; test in target environment |
| Navigation drift during guiding | Low | Medium | Regular odometry calibration; manual override available |
| Operator forgets commands | Medium | Low | Provide command cheat sheet; in-app help |
| Audio narration files corrupted | Low | Medium | Backup narration files; system skips corrupted waypoint |
| Robot hardware failure during tour | Low | High | Pre-tour health check; abort and retry procedure |

## Communication Cadence

- **Weekly**: 15-min check-in with lead operator (first 30 days)
- **Bi-weekly**: 30-min review with team (days 30–90)
- **Monthly**: Stakeholder email update with metrics
- **Ad-hoc**: Slack channel for quick questions

## KPI Framework

| Category | Metric | Baseline | Target | Measurement Method |
|----------|--------|----------|--------|-------------------|
| **Efficiency** | Time to create a 5-waypoint tour | 60 min (manual) | 15 min (with Tour) | Stopwatch during creation |
| **Efficiency** | Time to run a guided tour | 30 min (human guide) | 10 min (robot) | Tour duration log |
| **Quality** | Tour completion rate | N/A | >90% | Tours started vs completed |
| **Quality** | Operator error rate (commands misunderstood) | N/A | <5% | Log analysis |
| **Cost** | Labor cost per tour (operator time) | $50 (human guide) | $15 (robot) | Time × hourly rate |
| **Satisfaction** | Operator NPS (0–10) | N/A | >8 | Survey after 30 days |
| **Satisfaction** | Audience satisfaction (tour quality) | N/A | >4/5 | Post-tour survey |

## ROI Calculation

**Assumptions:**
- Human guide cost: $50/hour (fully loaded)
- Robot operator cost: $30/hour (lower skill required)
- Tours per month: 20 (conservative), 40 (optimistic)
- Tour duration: 30 min human, 10 min robot
- Implementation cost: $5,000 (software + training, one-time)
- Robot hardware cost excluded (already owned)

**Monthly Savings (Conservative):**
- Human: 20 tours × 0.5 hr × $50 = $500
- Robot: 20 tours × 0.17 hr × $30 = $102
- Monthly savings: $398
- Payback period: $5,000 / $398 ≈ 12.6 months

**Monthly Savings (Optimistic):**
- Human: 40 tours × 0.5 hr × $50 = $1,000
- Robot: 40 tours × 0.17 hr × $30 = $204
- Monthly savings: $796
- Payback period: $5,000 / $796 ≈ 6.3 months

**Additional Benefits (Qualitative):**
- 24/7 tour availability (no human scheduling)
- Consistent narration quality (no fatigue)
- Multi-language tours (future capability)
- Data collection for tour optimization

## Onboarding Guide (Quick Start)

### Step 1: Install
Run `bash bootstrap/install.sh` on the robot. Follow prompts.

### Step 2: Learn Commands
| Command | Action |
|---------|--------|
| "Start teaching" | Enter teaching mode |
| "Record waypoint" | Save current position + narration |
| "Stop recording" | End narration for current waypoint |
| "Finish tour" | Save tour and return to idle |
| "Start guiding [tour name]" | Begin autonomous tour |
| "Pause" | Pause guiding |
| "Resume" | Resume guiding |
| "Abort" | Stop and return to idle |
| "List tours" | Show saved tours |

### Step 3: Teach Your First Tour
1. Say "Start teaching"
2. Walk robot to first location
3. Say "Record waypoint" then speak narration (e.g., "This is the main entrance")
4. Say "Stop recording"
5. Move to next location, repeat steps 3–4
6. Say "Finish tour" and name it (e.g., "Lobby tour")

### Step 4: Run the Tour
1. Say "Start guiding Lobby tour"
2. Robot navigates to each waypoint and plays narration
3. Say "Abort" to stop early

### Troubleshooting
- **Robot doesn't respond**: Check microphone connection. Say commands clearly.
- **Navigation fails**: Robot says "Navigation failed. Waiting for instruction." Say "Retry" or "Abort".
- **Wrong narration**: Delete tour and re-teach.

### Glossary
- **Waypoint**: A specific location (pose) the robot navigates to.
- **Narration**: Audio recording played at each waypoint.
- **Teaching mode**: Operator walks robot through path.
- **Guiding mode**: Robot autonomously replays tour.