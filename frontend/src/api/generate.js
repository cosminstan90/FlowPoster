import client from "./client";

export async function generateSingle(keywordId) {
  const { data } = await client.post(`/generate/${keywordId}`);
  return data;
}

export async function generateBulk(campaignId, keywordIds, confirm = false) {
  const { data } = await client.post(
    "/generate/bulk",
    { campaign_id: campaignId, keyword_ids: keywordIds },
    { params: { confirm } },
  );
  return data;
}
