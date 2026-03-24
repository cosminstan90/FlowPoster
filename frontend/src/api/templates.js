import api from "./client";

export const getTemplates = () => api.get("/templates");
export const getTemplate = (id) => api.get(`/templates/${id}`);
export const createTemplate = (data) => api.post("/templates", data);
export const updateTemplate = (id, data) => api.put(`/templates/${id}`, data);
export const deleteTemplate = (id) => api.delete(`/templates/${id}`);
export const testTemplate = (id, payload) => api.post(`/templates/${id}/test`, payload);
