import client from "./client";

export async function getProjects() {
  const { data } = await client.get("/projects");
  return data;
}

export async function getProject(id) {
  const { data } = await client.get(`/projects/${id}`);
  return data;
}

export async function createProject(payload) {
  const { data } = await client.post("/projects", payload);
  return data;
}
