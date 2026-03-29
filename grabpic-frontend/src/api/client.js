import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

const api = axios.create({
  baseURL,
});

export const createEvent = () => api.post("/events");

export const uploadImages = (eventId, formData) =>
  api.post(`/events/${eventId}/upload`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

export const searchImages = (eventId, formData, page = 1, size = 20) =>
  api.post(`/events/${eventId}/search?page=${page}&size=${size}`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

export const getImageUrl = (eventId, imageId) =>
  `${baseURL}/events/${eventId}/images/${imageId}`;

export const downloadAllImages = (eventId) => {
  window.open(`${baseURL}/events/${eventId}/download`, "_blank");
};

export default api;
