import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/axios";
import { loginUser } from "../api/authApi";

const AuthContext = createContext(null);

function readSavedUser() {
  try {
    const value = localStorage.getItem("user");
    return value ? JSON.parse(value) : null;
  } catch {
    localStorage.removeItem("user");
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readSavedUser);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const refreshToken = localStorage.getItem("refreshToken");
      const savedUser = readSavedUser();

      if (!refreshToken || !savedUser) {
        if (active) { setUser(null); setLoading(false); }
        return;
      }

      try {
        // /me/ also proves the token is usable. The axios interceptor will
        // transparently refresh an expired access token once.
        const response = await api.get("me/");
        if (!active) return;
        localStorage.setItem("user", JSON.stringify(response.data));
        setUser(response.data);
      } catch {
        if (!active) return;
        setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    restoreSession();
    return () => { active = false; };
  }, []);

  async function login(credentials) {
    const data = await loginUser(credentials);
    localStorage.setItem("accessToken", data.access);
    localStorage.setItem("refreshToken", data.refresh);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }

  function logout() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
