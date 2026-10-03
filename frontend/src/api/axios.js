import axios from "axios";



const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000/api/",
});

function clearSession() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = localStorage.getItem("refreshToken");
  if (!refresh) throw new Error("No refresh token");

  // Use plain axios so a failed refresh is not intercepted recursively.
  const response = await axios.post(`${API_BASE_URL}auth/refresh/`, { refresh });
  localStorage.setItem("accessToken", response.data.access);
  if (response.data.refresh) localStorage.setItem("refreshToken", response.data.refresh);
  return response.data.access;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isUnauthorized = error.response?.status === 401;
    const isRefreshRequest = original?.url?.includes("auth/refresh/");

    if (isUnauthorized && original && !original._retry && !isRefreshRequest) {
      original._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccessToken = await refreshPromise;
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(original);
      } catch (refreshError) {
        clearSession();
        if (window.location.pathname !== "/login") {
          window.location.replace("/login?session=expired");
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
