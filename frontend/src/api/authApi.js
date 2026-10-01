import api from "./axios";

export async function getPublicOffices() {
  const response = await api.get("auth/offices/");

  if (Array.isArray(response.data)) {
    return response.data;
  }

  if (Array.isArray(response.data?.results)) {
    return response.data.results;
  }

  return [];
}

export async function signupUser(form) {
  const response = await api.post("auth/signup/", form);
  return response.data;
}

export async function loginUser(credentials) {
  const response = await api.post("auth/login/", credentials);
  return response.data;
}
