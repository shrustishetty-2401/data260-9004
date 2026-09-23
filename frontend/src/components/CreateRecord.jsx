import { useState } from "react";
import { createReport } from "../api";

const initialForm = {
  vulnerabilityTitle: "",
  packageName: "",
  submitterEmail: "student@example.com",
  description: "",
  category: "",
  termsAccepted: false,
};

export default function CreateRecord({ onSaved, onCancel }) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      await createReport(form);
      onSaved();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to create the report.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="card">
      <h1>Add Vulnerability Report</h1>

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

        <label>
          Submitter email
          <input
            type="email"
            name="submitterEmail"
            value={form.submitterEmail}
            onChange={updateField}
            required
          />
        </label>

        <label>
          Description
          <textarea
            name="description"
            value={form.description}
            onChange={updateField}
            minLength={26}
            required
          />
        </label>

        <label>
          Category
          <input
            name="category"
            value={form.category}
            onChange={updateField}
            required
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            name="termsAccepted"
            checked={form.termsAccepted}
            onChange={updateField}
            required
          />
          I accept the terms.
        </label>

        {error && <p className="error">{error}</p>}

        <div className="button-row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Create Report"}
          </button>

          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </main>
  );
}