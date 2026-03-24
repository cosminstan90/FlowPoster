import client from "./client";

export async function getKeywords(campaignId, { status, page = 1, limit = 50 } = {}) {
  const params = { campaign_id: campaignId, page, limit };
  if (status) params.status = status;
  const { data } = await client.get("/keywords", { params });
  return data;
}

export async function importCSV(campaignId, file, { columnMapping = null, source = "manual" } = {}) {
  const form = new FormData();
  form.append("campaign_id", campaignId);
  form.append("file", file);
  form.append("source", source);
  if (columnMapping) form.append("column_mapping", JSON.stringify(columnMapping));
  const { data } = await client.post("/keywords/import/csv", form);
  return data;
}

export async function importPaste(campaignId, text) {
  const { data } = await client.post("/keywords/import/paste", {
    campaign_id: campaignId,
    text,
  });
  return data;
}

export async function createKeyword(payload) {
  const { data } = await client.post("/keywords/manual", payload);
  return data;
}

export async function deleteKeyword(id) {
  const { data } = await client.delete(`/keywords/${id}`);
  return data;
}

export async function updateKeywordStatus(id, status) {
  const { data } = await client.put(`/keywords/${id}/status`, { status });
  return data;
}
