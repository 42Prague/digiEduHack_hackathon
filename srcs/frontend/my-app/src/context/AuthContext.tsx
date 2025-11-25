import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { addUser, findUser } from "../utils/yamlStore";
import type { StoredUser, UserRole } from "../utils/yamlStore";

interface AuthUser {
  username: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  register: (
    username: string,
    password: string,
    role: UserRole
  ) => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  initialized: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const CURRENT_USER_KEY = "current-user";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem(CURRENT_USER_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed?.username && parsed?.role) {
          setUser(parsed);
        }
      } catch {}
    }
    setInitialized(true);
  }, []);

  const persistUser = (u: AuthUser | null) => {
    setUser(u);
    if (u) {
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(u));
    } else {
      localStorage.removeItem(CURRENT_USER_KEY);
    }
  };

  const register = async (
    username: string,
    password: string,
    role: UserRole
  ) => {
    const newUser: StoredUser = { username, password, role };
    addUser(newUser);
  };

  const login = async (username: string, password: string) => {
    const stored = findUser(username);
    if (!stored || stored.password !== password) {
      throw new Error("Invalid credentials");
    }
    persistUser({ username: stored.username, role: stored.role });
  };

  const logout = () => {
    persistUser(null);
  };

  const value: AuthContextValue = {
    user,
    register,
    login,
    logout,
    initialized,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
