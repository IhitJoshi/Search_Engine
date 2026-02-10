import { io } from "socket.io-client";

let socket;

const normalizeBaseUrl = (value) => {
  if (!value) return value;
  return value.trim().replace(/\/+$/, "");
};

const stripApiSuffix = (value) => {
  if (!value) return value;
  return value.replace(/\/api\/?$/i, "");
};

const getSocketUrl = () => {
  const apiUrl = normalizeBaseUrl(import.meta.env.VITE_API_URL);
  return apiUrl ? stripApiSuffix(apiUrl) : undefined;
};

export const getStockSocket = () => {
  if (!socket) {
    socket = io(getSocketUrl(), {
      transports: ["websocket", "polling"],
      withCredentials: false,
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });
  }
  return socket;
};

export const subscribeSymbols = (symbols, options = {}) => {
  const socketInstance = getStockSocket();
  if (!Array.isArray(symbols) || symbols.length === 0) return;
  socketInstance.emit("subscribe", {
    symbols,
    interval: options.interval,
  });
};

export const unsubscribeSymbols = (symbols) => {
  const socketInstance = getStockSocket();
  if (!Array.isArray(symbols) || symbols.length === 0) return;
  socketInstance.emit("unsubscribe", { symbols });
};
