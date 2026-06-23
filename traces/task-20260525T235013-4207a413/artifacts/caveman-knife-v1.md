# Caveman — Knife Table

The knife cuts by one measure only: **does this feature dilute the true act** ("in the seconds a machine is failing — which one, what's wrong, how long left, what to do").

| # | Feature | Verdict | Reason | What it actually wants to be |
|---|---------|---------|--------|-------------------------------|
| 1 | Realtime vitals (battery / joint temp / CPU / net / task / geo) | **YES** | In the failure seconds, these ARE the failure. | The vital-signs slab — read-only, high contrast, ordered by urgency, not by alphabet. |
| 2 | Heterogeneous data (JSON + protobuf, unit drift) | **YES** | Failure doesn't care about schema. Hide drift and you hide the signal. | A canonical view with raw-shadow on hover — never silently coerce; surface every unit. |
| 3 | Overview (donut + line + heatmap) | **DILUTES** | Aggregates bury the one failing machine. Average is noise when one Orin is on fire. | A separate "fleet health" tab. Foreground stays empty until something breaks. |
| 4 | Alerting (fall / joint-lost / low-battery) | **YES** | The voice of the machine. The very reason the room exists. | Modal interruption with three buttons: ACK / CLAIM / ESCALATE. Nothing else competes with it. |
| 5 | 30-day history per robot | **DEFERRED** | Triage needs the last 30 seconds, not 30 days. Forensics ≠ triage. | A drawer that opens after ACK or by explicit request. Last-15-minutes pinned as default zoom. |
| 6 | Config panel (threshold / sample rate / reconnect) | **DEFERRED** | You cannot tune parameters while a machine is falling. | Admin/operator drawer. Accessed pre-deployment or in calm. |
| 7 | Collab (comments / @ / "I'm on it") | **YES — but stripped** | The second question is always "who's got this?" Claim/comment is the handoff. No threading. No @ in foreground. | A two-field strip on the failing robot's card: CLAIM (single name) + one-line note. |
| 8 | PDF/Excel export | **ELSEWHERE** | Export serves compliance and post-mortem. It is a separate product. | Move to a Reports surface. Not in the dashboard navigation. |
| 9 | Theme / i18n / draggable layout | **DILUTES** | In failure seconds, no one is dragging cards. Choice is cognitive load. | System dark, follows OS. i18n only if there's actually a multilingual ops team. Layout: fixed and canonical. |

## Verdict
- **Foreground** (always visible, ordered by urgency): F1 vitals, F2 raw+canonical data, F4 alerts as modal interrupts, F7 stripped claim/comment.
- **Background / one click away**: F5 history drawer, F6 admin drawer, F3 fleet-health tab.
- **Out of the product**: F8 export (separate Reports product), F9 theme/i18n/draggable (the knife says: doing less here is not laziness, it is design).
