import { useState } from "react";
import { useDispatch } from "react-redux";
import { removeReport } from "../store/reportSlice";

export default function DeleteRecord({ reportId, onDeleted, onCancel }) {
  const dispatch = useDispatch();
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setError("");
    setDeleting(true);

    try {
      await dispatch(removeReport(Number(reportId))).unwrap();
      onDeleted();
    } catch (requestError) {
      setError(
        requestError?.message ||
          requestError ||
          "Unable to delete the report.",
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <main className="card">
      <h1>Delete Vulnerability Report</h1>

      <p>
        Are you sure you want to delete report #{reportId}?
      </p>

      {error && <p className="error">{error}</p>}

      <div className="button-row">
        <button
          className="danger"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? "Deleting..." : "Confirm Delete"}
        </button>

        <button
          className="secondary"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </main>
  );
}