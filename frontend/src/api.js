import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BASE}/api`;

export const api = axios.create({
  baseURL: API,
  timeout: 60000,
});

export const WS_URL = `${BASE.replace(/^http/, "ws")}/api/logs/stream`;
