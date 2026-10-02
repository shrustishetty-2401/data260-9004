import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchReports,
  removeReport,
} from "../store/reportSlice";

export default function Home({ user, onEdit, onCreate }) {
  const dispatch = useDispatch();

  const reports = useSelector((state) => state.reports.items);
  const status = useSelector((state) => state.reports.status);
  const error = useSelector((state) => state.reports.error);

  useEffect(() => {
    dispatch(fetchReports());
  }, [dispatch]);

  async function handleDelete(id) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this report?",
    );

    if (!confirmed) {
      return;
    }

    try {
      await dispatch(removeReport(id)).unwrap();
    } catch {
      return;
    }
  }

  if (status === "loading" || status === "idle") {
    return <main className="card">Loading reports...</main>;
  }

  return (
    <main className="card wide">
      <div className="page-heading">
        <div>
          <h1>Vulnerability Reports</h1>
          <p>Signed in as {user.email}</p>
        </div>

        <button onClick={onCreate}>Add Report</button>
      </div>

      {error && <p className="error">{error}</p>}

      {reports.length === 0 ? (
        <p>No vulnerability reports found.</p>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Vulnerability</th>
                <th>Package</th>
                <th>Category</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.id}</td>
                  <td>{report.vulnerabilityTitle}</td>
                  <td>{report.packageName}</td>
                  <td>{report.category}</td>
                  <td className="actions">
                    <button onClick={() => onEdit(report.id)}>
                      Update
                    </button>

                    <button
                      className="danger"
                      onClick={() => handleDelete(report.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}