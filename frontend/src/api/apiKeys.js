import client from "./client";

export async function listAPIKeys() {
  const { data } = await client.get("/api-keys");
  return data;
}

export async function createAPIKey(payload) {
  const { data } = await client.post("/api-keys", payload);
  return data;
}

export async function revokeAPIKey(id) {
  const { data } = await client.delete(`/api-keys/${id}`);
  return data;
}
