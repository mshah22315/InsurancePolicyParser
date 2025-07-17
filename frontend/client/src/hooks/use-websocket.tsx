import { useEffect, useRef, useState } from "react";
import { WebSocketMessage } from "@/lib/types";

export function useWebSocket(url?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = url || `${protocol}//${window.location.host}/ws`;
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      setIsConnected(true);
      console.log("WebSocket connected");
    };
    
    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        setLastMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };
    
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log("WebSocket disconnected");
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };
    
    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  const sendMessage = (message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
}
