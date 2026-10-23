import { useState } from "react";

const DEFAULT_PRICING_URL = "https://citibikenyc.com/pricing";

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

      {result && (
        <>
          <section style={styles.card}>
            <h2>Decision</h2>
            <h3 style={styles.decision}>
              {result.decision.decision}
            </h3>
            <p>{result.decision.reason}</p>
            <p>
              Member rides: <strong>{result.decision.member_rides}</strong>
              {" | "}
              Casual rides: <strong>{result.decision.casual_rides}</strong>
            </p>
          </section>

          <section style={styles.card}>
            <h2>ReAct Tool Timeline</h2>

            {result.timeline.map((item) => (
              <article key={item.step} style={styles.timelineItem}>
                <strong>
                  Step {item.step}: {item.tool}
                </strong>
                <span style={styles.completed}>{item.status}</span>
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
                {result.csv_analysis.data.weekly_summary.map((row) => (
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
            <h2>Evidence</h2>
            <p>
              Pricing source:{" "}
              <a
                href={result.pricing_policy.data.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {result.pricing_policy.data.source_url}
              </a>
            </p>

            <p>
              Pricing snapshot SHA-256:
              <br />
              <code>{result.pricing_policy.data.sha256}</code>
            </p>

            <p>
              Stop reason: <strong>{result.stop_reason}</strong>
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