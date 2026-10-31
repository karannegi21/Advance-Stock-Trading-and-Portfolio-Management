import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_URL } from '../lib/api';

export function useWebSocket(onMessage?: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          onMessage?.(data);
        } catch {}
      };
      wsRef.current = ws;
    } catch {
      setTimeout(connect, 3000);
    }
  }, [onMessage]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { connected };
}
