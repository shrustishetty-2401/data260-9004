import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { editReport, fetchReports } from "../store/reportSlice";

export default function UpdateRecord({ reportId, onSaved, onCancel }) {
  const dispatch = useDispatch();

  const [form, setForm] = useState({
    vulnerabilityTitle: "",
    packageName: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadReport() {
      try {
        const reports = await dispatch(
          fetchReports({
            skip: 0,
            limit: 200,
          }),
        ).unwrap();

        const report = reports.find(
          (item) => item.id === Number(reportId),
        );

        if (!report) {
          setError("Report not found.");
          return;
        }

        setForm({
          vulnerabilityTitle: report.vulnerabilityTitle,
          packageName: report.packageName,
        });
      } catch (requestError) {
        setError(
          requestError?.message ||
            requestError ||
            "Unable to load the report.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadReport();
  }, [dispatch, reportId]);

  function updateField(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await dispatch(
        editReport({
          id: reportId,
          payload: form,
        }),
      ).unwrap();

      onSaved();
    } catch (requestError) {
      setError(
        requestError?.message ||
          requestError ||
          "Unable to update the report.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <main className="card">Loading report...</main>;
  }

  return (
    <main className="card">
      <h1>Update Vulnerability Report</h1>

      <form onSubmit={handleSubmit}>
        <label>
          Vulnerability title
          <input
            name="vulnerabilityTitle"
            value={form.vulnerabilityTitle}
            onChange={updateField}
            required
          />
        </label>

        <label>
          Package name
          <input
            name="packageName"
            value={form.packageName}
            onChange={updateField}
            required
          />
        </label>

        {error && <p className="error">{error}</p>}

        <div className="button-row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </button>

          <button
            type="button"
            className="secondary"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </main>
  );
}