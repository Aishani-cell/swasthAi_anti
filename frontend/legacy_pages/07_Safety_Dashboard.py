"""
SwasthAI — Safety Dashboard
=============================
Lists safety events, filters by severity, circuit breaker stats, and timeline.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Safety Dashboard · SwasthAI", page_icon="🛡️", layout="wide")

from backend.app.db.session import get_db_connection, init_db

init_db()


def require_login():
    if "user" not in st.session_state:
        st.warning("🔒 Please log in first.")
        st.stop()

require_login()


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="background:linear-gradient(135deg,#C0392B,#E74C3C);
                padding:24px 32px;border-radius:12px;color:#fff;
                margin-bottom:24px;">
        <h2 style="margin:0;color:#fff;">🛡️ Safety Dashboard</h2>
        <p style="margin:6px 0 0;opacity:0.9;">
            Deterministic Safety Engine · Circuit Breaker Monitoring
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Fetch safety data ──────────────────────────────────────────────────────
def _fetch_safety_data(severity_filter: str = "ALL") -> dict:
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Counts
        cur.execute("SELECT COUNT(*) FROM safety_events;")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE severity = 'CRITICAL';")
        critical = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE severity = 'WARNING';")
        warnings = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE circuit_breaker_halted = 1;")
        cb_halts = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM safety_events WHERE clinician_acknowledged = 1;")
        acknowledged = cur.fetchone()[0]

        # Event list
        if severity_filter and severity_filter != "ALL":
            cur.execute(
                """SELECT id, encounter_id, rule_id, ruleset_version, severity,
                          trigger_observed_value, trigger_threshold, action_taken,
                          circuit_breaker_halted, escalation_instructions,
                          clinician_acknowledged, created_at
                   FROM safety_events
                   WHERE severity = ?
                   ORDER BY created_at DESC
                   LIMIT 200;""",
                (severity_filter,),
            )
        else:
            cur.execute(
                """SELECT id, encounter_id, rule_id, ruleset_version, severity,
                          trigger_observed_value, trigger_threshold, action_taken,
                          circuit_breaker_halted, escalation_instructions,
                          clinician_acknowledged, created_at
                   FROM safety_events
                   ORDER BY created_at DESC
                   LIMIT 200;"""
            )
        events = [dict(r) for r in cur.fetchall()]

    return {
        "total": total,
        "critical": critical,
        "warnings": warnings,
        "cb_halts": cb_halts,
        "acknowledged": acknowledged,
        "events": events,
    }


# ── Severity filter ────────────────────────────────────────────────────────
filter_col, _ = st.columns([2, 3])
with filter_col:
    severity_filter = st.selectbox(
        "Filter by Severity",
        ["ALL", "CRITICAL", "WARNING", "INFO"],
        help="Filter safety events by severity level.",
    )

data = _fetch_safety_data(severity_filter)


# ── Summary metrics ────────────────────────────────────────────────────────
st.markdown("### Summary")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Events", data["total"])
m2.metric("🔴 Critical", data["critical"])
m3.metric("🟡 Warnings", data["warnings"])
m4.metric("⛔ CB Halts", data["cb_halts"])
m5.metric("✅ Acknowledged", data["acknowledged"])


# ── Circuit breaker statistics ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### Circuit Breaker Statistics")

if data["total"] > 0:
    halt_pct = (data["cb_halts"] / data["total"]) * 100
    ack_pct = (data["acknowledged"] / data["total"]) * 100

    cb1, cb2, cb3 = st.columns(3)
    cb1.metric("Halt Rate", f"{halt_pct:.1f}%")
    cb2.metric("Acknowledgment Rate", f"{ack_pct:.1f}%")
    cb3.metric("Unacknowledged", data["total"] - data["acknowledged"])

    st.progress(min(1.0, data["acknowledged"] / max(1, data["total"])),
                text=f"Clinician acknowledgment progress: {data['acknowledged']}/{data['total']}")
else:
    st.info("No safety events recorded yet.")

st.markdown("---")


# ── Events table ────────────────────────────────────────────────────────────
st.markdown("### Safety Events")

events = data["events"]
if events:
    df = pd.DataFrame(events)
    display_cols = ["id", "encounter_id", "rule_id", "severity",
                    "trigger_observed_value", "trigger_threshold",
                    "action_taken", "circuit_breaker_halted",
                    "clinician_acknowledged", "created_at"]
    available = [c for c in display_cols if c in df.columns]
    df = df[available]
    renames = {
        "id": "Event ID",
        "encounter_id": "Encounter",
        "rule_id": "Rule",
        "severity": "Severity",
        "trigger_observed_value": "Observed",
        "trigger_threshold": "Threshold",
        "action_taken": "Action",
        "circuit_breaker_halted": "CB Halted",
        "clinician_acknowledged": "Acknowledged",
        "created_at": "Timestamp",
    }
    df = df.rename(columns=renames)
    if "CB Halted" in df.columns:
        df["CB Halted"] = df["CB Halted"].map({0: "No", 1: "⛔ YES"})
    if "Acknowledged" in df.columns:
        df["Acknowledged"] = df["Acknowledged"].map({0: "❌", 1: "✅"})

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail expanders
    st.markdown("#### Event Details")
    for ev in events:
        severity = ev.get("severity", "INFO")
        icon = "🔴" if severity == "CRITICAL" else ("🟡" if severity == "WARNING" else "ℹ️")
        label = f"{icon} {ev.get('id', '?')} — {ev.get('rule_id', '?')}"

        with st.expander(label):
            ec1, ec2 = st.columns(2)
            with ec1:
                st.markdown(f"**Encounter**: `{ev.get('encounter_id', '—')}`")
                st.markdown(f"**Rule**: `{ev.get('rule_id', '—')}` (v{ev.get('ruleset_version', '?')})")
                st.markdown(f"**Severity**: `{severity}`")
                st.markdown(f"**Observed Value**: `{ev.get('trigger_observed_value', '—')}`")
                st.markdown(f"**Threshold**: `{ev.get('trigger_threshold', '—')}`")
            with ec2:
                st.markdown(f"**Action**: `{ev.get('action_taken', '—')}`")
                st.markdown(f"**CB Halted**: {'⛔ Yes' if ev.get('circuit_breaker_halted') else 'No'}")
                st.markdown(f"**Acknowledged**: {'✅ Yes' if ev.get('clinician_acknowledged') else '❌ No'}")
                st.markdown(f"**Timestamp**: {ev.get('created_at', '—')}")

            if ev.get("escalation_instructions"):
                st.error(f"🚨 **Escalation**: {ev['escalation_instructions']}")
else:
    st.info("No safety events to display.")


# ── Timeline ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Recent Safety Timeline")

if events:
    for ev in events[:15]:
        severity = ev.get("severity", "INFO")
        ts = ev.get("created_at", "—")
        rule = ev.get("rule_id", "?")
        obs = ev.get("trigger_observed_value", "?")
        halted = ev.get("circuit_breaker_halted", 0)

        if severity == "CRITICAL":
            st.markdown(
                f"🔴 **{ts}** — `{rule}` · Observed: `{obs}` "
                f"{'· ⛔ **HALTED**' if halted else ''}"
            )
        elif severity == "WARNING":
            st.markdown(f"🟡 **{ts}** — `{rule}` · Observed: `{obs}`")
        else:
            st.markdown(f"ℹ️ **{ts}** — `{rule}` · Observed: `{obs}`")
else:
    st.caption("No events in timeline.")
