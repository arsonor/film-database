import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { checkAuth, loginAdmin } from "@/api/client";

interface AuthContextValue {
  isAdmin: boolean;
  loading: boolean;
  login: (password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  isAdmin: false,
  loading: true,
  login: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    if (!token) {
      setLoading(false);
      return;
    }
    checkAuth().then((valid) => {
      setIsAdmin(valid);
      if (!valid) localStorage.removeItem("admin_token");
      setLoading(false);
    });
  }, []);

  const login = useCallback(async (password: string) => {
    const token = await loginAdmin(password);
    localStorage.setItem("admin_token", token);
    setIsAdmin(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("admin_token");
    setIsAdmin(false);
  }, []);

  if (loading) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ isAdmin, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
