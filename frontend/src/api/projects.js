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

export async function getSiteContext(projectId) {
  const { data } = await client.get(`/projects/${projectId}/context`);
  return data;
}

export async function upsertSiteContext(projectId, payload) {
  const { data } = await client.put(`/projects/${projectId}/context`, payload);
  return data;
}

export async function analyzeSite(projectId, siteUrl = null) {
  const { data } = await client.post(`/projects/${projectId}/context/analyze`, { site_url: siteUrl });
  return data;
}
