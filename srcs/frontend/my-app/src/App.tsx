import { Route, Routes, Navigate } from "react-router-dom";
import { LoginPage } from "./routes/LoginPage";
import { RegisterPage } from "./routes/RegisterPage";
import { MainPage } from "./routes/MainPage";
import { AnalystPage } from "./routes/AnalystPage";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { AnalystRoute } from "./components/auth/AnalystRoute";

function App() {
  return (
    <div className="app-shell">
      <AppLayout>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/analyst"
            element={
              <AnalystRoute>
                <AnalystPage />
              </AnalystRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </div>
  );
}

export default App;
