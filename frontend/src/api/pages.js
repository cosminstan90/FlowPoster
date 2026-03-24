import api from "./client";

export const getPage = (id) => api.get(`/pages/${id}`);
export const getPageByKeyword = (keywordId) => api.get(`/pages/by-keyword/${keywordId}`);
export const updatePage = (id, data) => api.put(`/pages/${id}`, data);
export const updatePageStatus = (id, status) => api.put(`/pages/${id}/status`, { status });
export const findPageImage = (id) => api.post(`/pages/${id}/find-image`);
export const regenerateSection = (id, section) => api.post(`/pages/${id}/regenerate`, { section });
