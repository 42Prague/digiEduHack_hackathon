import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

interface AnalystRouteProps {
  children: ReactNode;
}

export function AnalystRoute({ children }: AnalystRouteProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user.role !== "analyst") {
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
