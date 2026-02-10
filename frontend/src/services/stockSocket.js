import { io } from "socket.io-client";

let socket;

const getSocketUrl = () => {
  const baseUrl = import.meta.env.VITE_API_URL;
  return baseUrl && baseUrl.trim().length > 0 ? baseUrl : undefined;
};

export const getStockSocket = () => {
  if (!socket) {
    socket = io(getSocketUrl(), {
      withCredentials: false,
      transports: ["polling", "websocket"],
      upgrade: true,
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
