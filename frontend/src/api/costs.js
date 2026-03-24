import client from "./client";

export async function getCostSummary() {
  const { data } = await client.get("/costs/summary");
  return data;
}

export async function getProjectCost(projectId, month) {
  const params = month ? { month } : {};
  const { data } = await client.get(`/costs/project/${projectId}`, { params });
  return data;
}

export async function estimateCost(campaignId, keywordCount) {
  const { data } = await client.post("/costs/estimate", {
    campaign_id: campaignId,
    keyword_count: keywordCount,
  });
  return data;
}
