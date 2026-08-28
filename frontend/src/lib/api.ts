import axios from 'axios';

// All API requests now pass through the Next.js API route proxy
// which automatically attaches the secure HttpOnly cookie.
export const api = axios.create({
  baseURL: '/api/proxy',
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("isAuthenticated");
        localStorage.removeItem("username");
        localStorage.removeItem("pl_advisor_last_index");
        window.dispatchEvent(new Event("auth-logout"));
        if (!window.location.pathname.startsWith("/login") && window.location.pathname !== "/") {
          window.location.href = "/";
        }
      }
    }
    return Promise.reject(error);
  }
);
