import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "reports" / "hw10" / "raw"


def load_json(name, default=None):
    path = RAW / name
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(name):
    path = RAW / name
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def fmt(value, digits=2):
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return "—"


st.set_page_config(
    page_title="HW10 Operations Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(
            135deg,
            #f7f9fc 0%,
            #eef4ff 100%
        );
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dbe5f2;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(30, 60, 100, .08);
    }

    h1 {
        color: #173b72 !important;
        font-weight: 800 !important;
        border-bottom: 5px solid #4f8cff;
        padding-bottom: 12px;
    }

    h2 {
        color: #214f91 !important;
        background: linear-gradient(
            90deg,
            #dceaff,
            #f4f8ff,
            transparent
        );
        border-left: 7px solid #3478db;
        border-radius: 8px;
        padding: 10px 16px;
        margin-top: 26px;
    }

    h3 {
        color: #8a3ffc !important;
        background: #f1eaff;
        border-left: 5px solid #8a3ffc;
        border-radius: 7px;
        padding: 8px 12px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #173b72,
            #285b9f
        );
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .card {
        background: white;
        border: 1px solid #dbe5f2;
        border-radius: 16px;
        padding: 20px;
        margin: 14px 0;
        box-shadow: 0 4px 12px rgba(30, 60, 100, .07);
    }

    .good {
        color: #137333;
        background: #e6f4ea;
        border-radius: 20px;
        padding: 7px 15px;
        font-weight: 700;
        display: inline-block;
    }

    .bad {
        color: #b3261e;
        background: #fce8e6;
        border-radius: 20px;
        padding: 7px 15px;
        font-weight: 700;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

traces = load_jsonl("traces.jsonl")
latency = load_json("latency_benchmark.json")
evaluation = load_json("pipeline_evaluation.json")
judge = load_json("judge_validation.json")
examples = load_json("trace_examples.json")

st.title("📊 DATA-260 HW10 Operations Dashboard")
st.caption("Kafka multi-agent pipeline • semantic cache • evaluator • trace evidence")

page = st.sidebar.radio(
    "Dashboard pages",
    ["Summary", "Evaluation", "Trace Lookup"],
)


if page == "Summary":
    st.header("Operations Summary")

    st.write("Evidence source: local Kafka and evaluator experiment outputs")
    st.write("Window: timestamps recorded during HW10 experiments")

    hit_count = sum(
        row.get("metadata", {}).get("cache_status") == "hit" for row in traces
    )

    miss_count = sum(
        row.get("metadata", {}).get("cache_status") == "miss" for row in traces
    )

    failed_count = sum(row.get("status") == "failed" for row in traces)

    trace_count = len({row.get("trace_id") for row in traces})

    metrics = latency.get("metrics", {})
    total = metrics.get("total", {})

    columns = st.columns(5)

    columns[0].metric("Traces", trace_count)
    columns[1].metric("Cache hits", hit_count)
    columns[2].metric("Cache misses", miss_count)
    columns[3].metric("Failed spans", failed_count)
    columns[4].metric(
        "Total p95",
        f"{fmt(total.get('p95_ms'))} ms",
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.subheader("System Health")

    if failed_count:
        st.markdown(
            '<span class="bad">⚠ Failure trace captured</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="good">✓ All traces successful</span>',
            unsafe_allow_html=True,
        )

    st.write(
        f"The dashboard contains {trace_count} traces, "
        f"{hit_count} cache hit, {miss_count} cache-miss paths, "
        f"and {failed_count} failed span."
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.subheader("Latency by Stage")

    chart_data = {
        stage: metrics.get(stage, {}).get("p95_ms", 0)
        for stage in [
            "queue_wait",
            "planner",
            "writer",
            "reviewer",
            "total",
        ]
    }

    st.bar_chart(chart_data)

    for stage in [
        "queue_wait",
        "planner",
        "writer",
        "reviewer",
        "total",
    ]:
        values = metrics.get(stage, {})

        st.write(
            f"**{stage.replace('_', ' ').title()}** — "
            f"p50: {fmt(values.get('p50_ms'))} ms | "
            f"p95: {fmt(values.get('p95_ms'))} ms"
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.subheader("Cache-Miss Benchmark")

    st.write(
        f"Confirmed cache misses: **{latency.get('confirmed_cache_miss_count', '—')}**"
    )

    st.write(
        f"Dominant p95 contributor: **{latency.get('p95_dominant_contributor', '—')}**"
    )

    st.write(f"Contributor share: **{fmt(latency.get('p95_contributor_percent'))}%**")

    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Evaluation":
    st.header("Evaluation and Judge Validation")

    st.info(
        "The local Ollama judge evaluated the Planner, Writer, "
        "and final response. The tested final answer did not improve "
        "over the draft."
    )

    for key, label in [
        ("plan_quality", "Plan Quality"),
        ("writer_helpfulness", "Writer Helpfulness"),
        (
            "final_answer_helpfulness",
            "Final Answer Helpfulness",
        ),
    ]:
        result = evaluation.get(key, {})

        st.subheader(label)

        st.metric(
            "Judge score",
            result.get("score", "—"),
        )

        st.write(
            result.get(
                "reason",
                "No explanation available.",
            )
        )

    st.subheader("Final Versus Draft")

    comparison = evaluation.get(
        "final_vs_draft",
        {},
    )

    st.write(f"Draft score: **{comparison.get('draft_score', '—')}**")

    st.write(f"Final score: **{comparison.get('final_score', '—')}**")

    st.write(
        comparison.get(
            "interpretation",
            "No comparison available.",
        )
    )

    st.subheader("Judge Validation Repeats")

    repeats = judge.get("repeats", [])

    if repeats:
        for item in repeats:
            summary = item.get("summary", {})

            st.write(
                f"Repeat {item.get('repeat')}: "
                f"Spearman = "
                f"{fmt(summary.get('spearman_correlation'), 3)}, "
                f"MAD = "
                f"{fmt(summary.get('mean_absolute_difference'), 3)}"
            )
    else:
        st.warning("Judge validation repeat results are not available.")

    st.write(
        "The same correlation ID was preserved across Planner, "
        "Writer, Reviewer, and evaluator stages."
    )


else:
    st.header("Trace Lookup")

    st.write(
        "Inspect the complete journey of a cache hit, cache miss, or failed trace."
    )

    trace_ids = [value for value in examples.values() if isinstance(value, str)]

    if not trace_ids:
        st.error("No example trace IDs were found.")
    else:
        selected = st.selectbox(
            "Choose an example trace",
            trace_ids,
        )

        matches = [row for row in traces if row.get("trace_id") == selected]

        if not matches:
            st.error("This trace ID was not found in traces.jsonl.")
        else:
            failed = any(row.get("status") == "failed" for row in matches)

            if failed:
                st.markdown(
                    '<span class="bad">⚠ Failed trace</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="good">✓ Trace captured</span>',
                    unsafe_allow_html=True,
                )

            st.write(f"Trace ID: `{selected}`")

            for row in matches:
                with st.expander(
                    f"{row.get('stage')} — {row.get('status')}",
                    expanded=True,
                ):
                    st.json(row)


st.sidebar.caption(f"Loaded {len(traces)} trace spans")
