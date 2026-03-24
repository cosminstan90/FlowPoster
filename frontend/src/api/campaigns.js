import client from "./client";

export async function getCampaigns(projectId) {
  const { data } = await client.get("/campaigns", { params: { project_id: projectId } });
  return data;
}

export async function getCampaign(id) {
  const { data } = await client.get(`/campaigns/${id}`);
  return data;
}

export async function createCampaign(payload) {
  const { data } = await client.post("/campaigns", payload);
  return data;
}

export async function updateCampaign(id, payload) {
  const { data } = await client.put(`/campaigns/${id}`, payload);
  return data;
}
