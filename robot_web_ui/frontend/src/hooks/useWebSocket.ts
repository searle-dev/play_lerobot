import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
) => {
  const {
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 3000
  } = options;

  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setReadyState(WebSocket.OPEN);
        onOpen?.();
      };

      ws.current.onclose = () => {
        setReadyState(WebSocket.CLOSED);
        onClose?.();

        if (reconnect) {
          reconnectTimer.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        onError?.(error);
      };

      ws.current.onmessage = (event) => {
        setLastMessage(event);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, [url, reconnect, reconnectInterval, onOpen, onClose, onError]);

  const sendMessage = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not open. Cannot send message.');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    ws.current?.close();
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    sendMessage,
    lastMessage,
    readyState,
    disconnect
  };
};
