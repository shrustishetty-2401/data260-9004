import json
from datetime import datetime
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "reports" / "hw10" / "raw"

STAGE_ORDER = [
    "cache_lookup",
    "inbox",
    "planner",
    "writer",
    "reviewer",
    "evaluation",
]


@st.cache_data
def load_json(name, default=None):
    path = RAW / name

    if not path.exists():
        return default if default is not None else {}

    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
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


def add_duration(span):
    result = dict(span)

    if result.get("duration_ms") is not None:
        return result

    start = result.get("start_time")
    end = result.get("end_time")

    try:
        start_time = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end.replace("Z", "+00:00"))

        result["duration_ms"] = round(
            (end_time - start_time).total_seconds() * 1000,
            3,
        )
    except (AttributeError, TypeError, ValueError):
        result["duration_ms"] = None

    return result


def stage_position(span):
    stage = span.get("stage", "")
    return STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)


st.set_page_config(
    page_title="HW10 Operations Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #f6f8fc !important;
        color: #202124 !important;
    }

    .main .block-container {
        background: transparent !important;
    }

    [data-testid="stMetric"] {
        background: white !important;
        color: #173b72 !important;
        border: 1px solid #dbe5f2;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(30, 60, 100, .08);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        color: #173b72 !important;
    }

    h1 {
        color: #173b72 !important;
        font-size: 14pt !important;
        font-weight: 800 !important;
        border-bottom: 5px solid #4f8cff;
        padding-bottom: 12px;
    }

    h2 {
        color: #214f91 !important;
        font-size: 12pt !important;
        background: linear-gradient(
            90deg,
            #dceaff,
            #f4f8ff,
            white
        );
        border-left: 7px solid #3478db;
        border-radius: 8px;
        padding: 10px 16px;
        margin-top: 26px;
    }

    h3 {
        color: #7138c8 !important;
        font-size: 12pt !important;
        background: #f1eaff;
        border-left: 5px solid #8a3ffc;
        border-radius: 7px;
        padding: 8px 12px;
    }

    p,
    li,
    label,
    .card {
        color: #202124 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #173b72,
            #285b9f
        ) !important;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .card {
        background: white !important;
        color: #202124 !important;
        border: 1px solid #dbe5f2;
        border-radius: 16px;
        padding: 20px;
        margin: 14px 0;
        box-shadow: 0 4px 12px rgba(30, 60, 100, .07);
    }

    .good {
        color: #137333 !important;
        background: #e6f4ea;
        border-radius: 20px;
        padding: 7px 15px;
        font-weight: 700;
        display: inline-block;
    }

    .bad {
        color: #b3261e !important;
        background: #fce8e6;
        border-radius: 20px;
        padding: 7px 15px;
        font-weight: 700;
        display: inline-block;
    }

    div[data-baseweb="select"] {
        background: white !important;
        color: #202124 !important;
    }

    div[data-baseweb="select"] > div {
        background: white !important;
        color: #202124 !important;
        border: 1px solid #b8c7dc !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="select"] * {
        color: #202124 !important;
    }

    div[data-baseweb="select"] input {
        background: white !important;
        color: #202124 !important;
        caret-color: #202124 !important;
    }

    [role="listbox"] {
        background: white !important;
        border: 1px solid #b8c7dc !important;
    }

    [role="option"] {
        background: white !important;
        color: #202124 !important;
    }

    [role="option"]:hover {
        background: #dceaff !important;
        color: #173b72 !important;
    }

    [data-testid="stTextInput"] input {
        background: white !important;
        color: #202124 !important;
        caret-color: #202124 !important;
        border: 1px solid #b8c7dc !important;
        border-radius: 8px !important;
    }

    [data-testid="stDataFrame"] {
        background: white !important;
        border-radius: 10px;
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
    [
        "Summary",
        "Evaluation",
        "Trace Lookup",
    ],
)


if page == "Summary":
    st.header("Operations Summary")

    st.write("Evidence source: local Kafka and evaluator experiment outputs.")

    st.write("Time window: timestamps recorded during the HW10 experiments.")

    hit_count = sum(
        row.get("metadata", {}).get("cache_status") == "hit" for row in traces
    )

    miss_count = sum(
        row.get("metadata", {}).get("cache_status") == "miss" for row in traces
    )

    cache_total = hit_count + miss_count

    cache_hit_rate = hit_count / cache_total if cache_total else 0

    failed_count = sum(row.get("status") == "failed" for row in traces)

    trace_count = len({row.get("trace_id") for row in traces if row.get("trace_id")})

    error_rate = failed_count / trace_count if trace_count else 0

    metrics = latency.get("metrics", {})
    total = metrics.get("total", {})

    columns = st.columns(6)

    columns[0].metric(
        "Traces",
        trace_count,
    )

    columns[1].metric(
        "Cache hits",
        hit_count,
    )

    columns[2].metric(
        "Cache misses",
        miss_count,
    )

    columns[3].metric(
        "Failed spans",
        failed_count,
    )

    columns[4].metric(
        "Total p95",
        f"{fmt(total.get('p95_ms'))} ms",
    )

    columns[5].metric(
        "Error rate",
        f"{error_rate:.1%}",
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

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.subheader("Semantic Cache Summary")

    st.write(
        "Cache-hit rate: "
        f"**{cache_hit_rate:.1%}** "
        f"({hit_count} hits out of {cache_total} cache requests)"
    )

    st.write(
        "Cache misses are shown separately because the latency benchmark "
        "used confirmed cache-miss requests only."
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

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

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.subheader("Cache-Miss Benchmark")

    st.write(
        f"Confirmed cache misses: **{latency.get('confirmed_cache_miss_count', '—')}**"
    )

    dominant = latency.get(
        "p95_dominant_contributor",
        "—",
    )

    contributor_percent = latency.get("p95_contributor_percent")

    if contributor_percent is None:
        contributor_percent = latency.get(
            "p95_percent_of_total",
            {},
        ).get(dominant)

    st.write(f"Dominant p95 contributor: **{dominant}**")

    st.write(f"Contributor share: **{fmt(contributor_percent)}%**")

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


elif page == "Evaluation":
    st.header("Evaluation and Judge Validation")

    st.info(
        "The local Ollama judge evaluated the Planner, Writer, "
        "and final response. The tested final answer did not improve "
        "over the draft."
    )

    st.subheader("Pipeline Stage Scores")

    stage_scores = []

    for key, label in [
        ("plan_quality", "Plan Quality"),
        ("writer_helpfulness", "Writer Helpfulness"),
        (
            "final_answer_helpfulness",
            "Final Answer Helpfulness",
        ),
    ]:
        result = evaluation.get(key, {})

        stage_scores.append(
            {
                "Stage": label,
                "Score": result.get("score", "—"),
                "Reason": result.get(
                    "reason",
                    "No explanation available.",
                ),
            }
        )

    st.dataframe(
        stage_scores,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Final Versus Draft")

    comparison = evaluation.get(
        "final_vs_draft",
        {},
    )

    st.write(f"Draft score: **{comparison.get('draft_score', '—')}**")

    st.write(f"Final score: **{comparison.get('final_score', '—')}**")

    st.write(f"Score difference: **{comparison.get('difference', '—')}**")

    st.write(
        comparison.get(
            "interpretation",
            "No comparison available.",
        )
    )

    st.subheader("Judge Validation")

    repeats = judge.get("repeats", [])

    if repeats:
        repeat_rows = []

        for item in repeats:
            summary = item.get("summary", {})

            repeat_rows.append(
                {
                    "Repeat": item.get("repeat"),
                    "Spearman": fmt(
                        summary.get("spearman_correlation"),
                        3,
                    ),
                    "MAD": fmt(
                        summary.get("mean_absolute_difference"),
                        3,
                    ),
                    "Cases": summary.get(
                        "case_count",
                        "—",
                    ),
                }
            )

        st.dataframe(
            repeat_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.warning("Judge validation repeat results are not available.")

    st.write(
        f"Score changes across repeats: **{judge.get('repeated_score_changes', '—')}**"
    )

    st.write(
        "Mean absolute repeat change: "
        f"**{fmt(judge.get('mean_absolute_repeat_change'), 3)}**"
    )

    st.write(
        "Maximum absolute repeat change: "
        f"**{fmt(judge.get('maximum_absolute_repeat_change'), 3)}**"
    )

    st.subheader("Per-Case Judge Results")

    cases = []

    if repeats:
        cases = repeats[0].get("cases", [])

    if cases:
        case_rows = [
            {
                "Case ID": case.get("case_id"),
                "Human Label": case.get("human_label"),
                "Judge Score": case.get("judge_score"),
                "Normalized Score": case.get("normalized_score"),
                "Question": case.get("question"),
                "Reason": case.get("reason"),
            }
            for case in cases
        ]

        st.dataframe(
            case_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Per-case judge results are not available.")

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
        selected_example = st.selectbox(
            "Choose an example trace",
            trace_ids,
        )

        selected = st.text_input(
            "Enter trace_id",
            value=selected_example,
        ).strip()

        matches = [
            add_duration(row) for row in traces if row.get("trace_id") == selected
        ]

        matches.sort(key=stage_position)

        if not matches:
            st.warning("Trace ID not found. Use one of the example IDs:")

            st.code("\n".join(trace_ids))
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
                duration = row.get("duration_ms")

                duration_text = (
                    f"{fmt(duration, 3)} ms"
                    if isinstance(
                        duration,
                        (int, float),
                    )
                    else "—"
                )

                with st.expander(
                    f"{row.get('stage')} — {row.get('status')} — {duration_text}",
                    expanded=True,
                ):
                    st.write(f"Duration: **{duration_text}**")

                    st.json(row)


st.sidebar.caption(f"Loaded {len(traces)} trace spans")
