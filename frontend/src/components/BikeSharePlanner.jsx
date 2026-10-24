import { useState } from "react";

const DEFAULT_PRICING_URL = "https://citibikenyc.com/pricing";

const PRICING_ASSUMPTIONS = {
  annualMembership: 239,
  classicRidePrice: 4.99,
};

function getCostSummary(result) {
  const weeklySummary = result?.csv_analysis?.data?.weekly_summary || [];

  const memberRides =
    weeklySummary.find((row) => row.member_type === "member")?.rides || 0;

  const casualRides =
    weeklySummary.find((row) => row.member_type === "casual")?.rides || 0;

  const totalRides = memberRides + casualRides;

  const weeklyMembershipCost =
    PRICING_ASSUMPTIONS.annualMembership / 52;

  const weeklyPayPerUseCost =
    totalRides * PRICING_ASSUMPTIONS.classicRidePrice;

  const breakEvenRides = Math.ceil(
    PRICING_ASSUMPTIONS.annualMembership /
      PRICING_ASSUMPTIONS.classicRidePrice,
  );

  const recommendation =
    memberRides >= casualRides
      ? "Buy Monthly Membership"
      : "Pay Per Ride/Minute";

  return {
    memberRides,
    casualRides,
    totalRides,
    weeklyMembershipCost,
    weeklyPayPerUseCost,
    breakEvenRides,
    recommendation,
  };
}

function cleanPricingUrl(sourceUrl) {
  if (!sourceUrl) {
    return DEFAULT_PRICING_URL;
  }

  const match = sourceUrl.match(/https?:\/\/[^\s\])]+/);

  return match ? match[0] : sourceUrl;
}

export default function BikeSharePlanner() {
  const [file, setFile] = useState(null);
  const [pricingUrl, setPricingUrl] = useState(DEFAULT_PRICING_URL);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!file) {
      setError("Please choose a CSV file.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("pricing_url", pricingUrl);

    try {
      const response = await fetch(
        "http://127.0.0.1:8004/api/bikeshare/analyze",
        {
          method: "POST",
          body: formData,
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Bike-share analysis failed.");
      }

      setResult(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  const costSummary = result ? getCostSummary(result) : null;

  const pricingData = result?.pricing_policy?.data;
  const pricingSource = cleanPricingUrl(pricingData?.source_url);
  const stepCount = result?.timeline?.length || 0;
  const totalTime =
    result?.total_time_ms ||
    result?.elapsed_ms ||
    result?.duration_ms ||
    "Not returned by API";

  return (
    <main style={styles.page}>
      <section style={styles.card}>
        <h1>Bike-Share Decision Assistant</h1>

        <p style={styles.subtitle}>
          Upload trip history and compare membership with pay-per-use pricing.
        </p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Trip CSV
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setFile(event.target.files[0])}
            />
          </label>

          <label style={styles.label}>
            Pricing policy URL
            <input
              type="url"
              value={pricingUrl}
              onChange={(event) => setPricingUrl(event.target.value)}
              required
              style={styles.input}
            />
          </label>

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Running..." : "Run Analysis"}
          </button>
        </form>

        {error && <p style={styles.error}>{error}</p>}
      </section>

      {result && costSummary && (
        <>
          <section style={styles.card}>
            <h2>Final Decision</h2>

            <h3 style={styles.decision}>
              {costSummary.recommendation}
            </h3>

            <p>
              {result.decision?.reason ||
                "The recommendation is based on the uploaded trip history."}
            </p>

            <div style={styles.decisionGrid}>
              <div style={styles.metric}>
                <span>Member rides</span>
                <strong>{costSummary.memberRides}</strong>
              </div>

              <div style={styles.metric}>
                <span>Casual rides</span>
                <strong>{costSummary.casualRides}</strong>
              </div>

              <div style={styles.metric}>
                <span>Total rides</span>
                <strong>{costSummary.totalRides}</strong>
              </div>
            </div>
          </section>

          <section style={styles.card}>
            <h2>Cost Comparison</h2>

            <div style={styles.costGrid}>
              <div style={styles.costBox}>
                <h3>Membership</h3>
                <p>
                  Annual price:{" "}
                  <strong>
                    ${PRICING_ASSUMPTIONS.annualMembership.toFixed(2)}
                  </strong>
                </p>
                <p>
                  Weekly equivalent:{" "}
                  <strong>
                    ${costSummary.weeklyMembershipCost.toFixed(2)}
                  </strong>
                </p>
              </div>

              <div style={styles.costBox}>
                <h3>Pay Per Ride/Minute</h3>
                <p>
                  Classic ride price:{" "}
                  <strong>
                    ${PRICING_ASSUMPTIONS.classicRidePrice.toFixed(2)}
                  </strong>
                </p>
                <p>
                  Estimated weekly cost:{" "}
                  <strong>
                    ${costSummary.weeklyPayPerUseCost.toFixed(2)}
                  </strong>
                </p>
              </div>
            </div>

            <p style={styles.breakEven}>
              Break-even point: approximately{" "}
              <strong>{costSummary.breakEvenRides} rides per year</strong>{" "}
              at the current classic-ride price.
            </p>

            <p style={styles.assumption}>
              Assumption: the calculation uses the retrieved Citi Bike pricing
              snapshot and the classic-bike pay-per-ride price.
            </p>
          </section>

          <section style={styles.card}>
            <h2>ReAct Tool Timeline</h2>

            <p>
              Steps completed: <strong>{stepCount}</strong>
              {" | "}
              Total time: <strong>{totalTime}</strong>
              {" | "}
              Stop reason:{" "}
              <strong>{result.stop_reason || "completed"}</strong>
            </p>

            {result.timeline?.map((item) => (
              <article key={item.step} style={styles.timelineItem}>
                <div>
                  <strong>
                    Step {item.step}: {item.tool}
                  </strong>

                  <span style={styles.completed}>
                    {item.status}
                  </span>
                </div>

                <pre style={styles.pre}>
                  {JSON.stringify(item.result, null, 2)}
                </pre>
              </article>
            ))}
          </section>

          <section style={styles.card}>
            <h2>Weekly Comparison</h2>

            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Rides</th>
                  <th>Total Minutes</th>
                  <th>Average Minutes</th>
                </tr>
              </thead>

              <tbody>
                {result.csv_analysis?.data?.weekly_summary?.map((row) => (
                  <tr key={row.member_type}>
                    <td>{row.member_type}</td>
                    <td>{row.rides}</td>
                    <td>{row.total_minutes}</td>
                    <td>{row.average_minutes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section style={styles.card}>
            <h2>Evidence and Provenance</h2>

            <p>
              Uploaded file:{" "}
              <strong>{file?.name || "Uploaded CSV"}</strong>
            </p>

            <p>
              Pricing source:{" "}
              <a
                href={pricingSource}
                target="_blank"
                rel="noreferrer"
              >
                {pricingSource}
              </a>
            </p>

            <p>
              Pricing captured at:{" "}
              <strong>
                {pricingData?.retrieved_at || "Not returned"}
              </strong>
            </p>

            <p>
              Pricing snapshot SHA-256:
              <br />
              <code>{pricingData?.sha256 || "Not returned"}</code>
            </p>

            <p>
              Snapshot file:{" "}
              <code>
                {pricingData?.snapshot_file || "Not returned"}
              </code>
            </p>

            <p>
              Stop reason:{" "}
              <strong>{result.stop_reason || "completed"}</strong>
            </p>
          </section>
        </>
      )}
    </main>
  );
}

const styles = {
  page: {
    maxWidth: "1000px",
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "Arial, sans-serif",
    background: "#f4f7fb",
    minHeight: "100vh",
  },

  card: {
    marginBottom: "24px",
    padding: "24px",
    border: "1px solid #d8dee9",
    borderRadius: "12px",
    background: "#ffffff",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.06)",
  },

  subtitle: {
    color: "#59636e",
  },

  form: {
    display: "grid",
    gap: "16px",
    marginTop: "20px",
  },

  label: {
    display: "grid",
    gap: "8px",
    fontWeight: "600",
  },

  input: {
    padding: "10px",
    border: "1px solid #b8c1cc",
    borderRadius: "6px",
    fontSize: "15px",
  },

  button: {
    width: "fit-content",
    padding: "11px 18px",
    border: "none",
    borderRadius: "6px",
    background: "#1769aa",
    color: "white",
    fontWeight: "700",
    cursor: "pointer",
  },

  error: {
    marginTop: "16px",
    color: "#b42318",
    fontWeight: "600",
  },

  decision: {
    color: "#1769aa",
    fontSize: "28px",
  },

  decisionGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "14px",
    marginTop: "20px",
  },

  metric: {
    padding: "16px",
    borderRadius: "8px",
    background: "#eef6ff",
    display: "grid",
    gap: "6px",
  },

  costGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "18px",
  },

  costBox: {
    padding: "18px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    background: "#f8fafc",
  },

  breakEven: {
    marginTop: "20px",
    padding: "14px",
    borderRadius: "8px",
    background: "#ecfdf3",
    color: "#166534",
  },

  assumption: {
    color: "#59636e",
    fontSize: "14px",
  },

  timelineItem: {
    marginBottom: "18px",
    padding: "14px",
    borderLeft: "4px solid #1769aa",
    background: "#f6f9fc",
  },

  completed: {
    marginLeft: "12px",
    color: "#16803c",
    fontWeight: "600",
  },

  pre: {
    maxHeight: "260px",
    overflow: "auto",
    padding: "12px",
    background: "#111827",
    color: "#e5e7eb",
    borderRadius: "6px",
    fontSize: "12px",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
};