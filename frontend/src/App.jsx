import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getCurrentUser,
  logout,
} from "./api";
import CreateRecord from "./components/CreateRecord";
import DeleteRecord from "./components/DeleteRecord";
import Home from "./components/Home";
import Login from "./components/Login";
import UpdateRecord from "./components/UpdateRecord";
import "./App.css";

function ProtectedRoute({ user, children }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function UpdatePage({ onSaved, onCancel }) {
  const { id } = useParams();

  return (
    <UpdateRecord
      reportId={id}
      onSaved={onSaved}
      onCancel={onCancel}
    />
  );
}

function DeletePage({ onDeleted, onCancel }) {
  const { id } = useParams();

  return (
    <DeleteRecord
      reportId={id}
      onDeleted={onDeleted}
      onCancel={onCancel}
    />
  );
}

function AppContent() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function checkSession() {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        setUser(null);
      } finally {
        setCheckingSession(false);
      }
    }

    checkSession();
  }, []);

  async function handleLogout() {
    await logout();
    setUser(null);
    navigate("/login");
  }

  if (checkingSession) {
    return <main className="card">Checking session...</main>;
  }

  return (
    <>
      <header className="navbar">
        <strong>DATA-260 HW4</strong>

        {user && (
          <button className="secondary" onClick={handleLogout}>
            Logout
          </button>
        )}
      </header>

      <Routes>
        <Route
          path="/login"
          element={
            user ? (
              <Navigate to="/" replace />
            ) : (
              <Login
                onLogin={(loggedInUser) => {
                  setUser(loggedInUser);
                  navigate("/");
                }}
              />
            )
          }
        />

        <Route
          path="/"
          element={
            <ProtectedRoute user={user}>
              <Home
                user={user}
                onCreate={() => navigate("/create")}
                onEdit={(id) => navigate(`/update/${id}`)}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/create"
          element={
            <ProtectedRoute user={user}>
              <CreateRecord
                onSaved={() => navigate("/")}
                onCancel={() => navigate("/")}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/update/:id"
          element={
            <ProtectedRoute user={user}>
              <UpdatePage
                onSaved={() => navigate("/")}
                onCancel={() => navigate("/")}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/delete/:id"
          element={
            <ProtectedRoute user={user}>
              <DeletePage
                onDeleted={() => navigate("/")}
                onCancel={() => navigate("/")}
              />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}