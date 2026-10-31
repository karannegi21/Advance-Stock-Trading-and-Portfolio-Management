import { useEffect, useRef, useState } from 'react';
import { WS_URL } from '../lib/api';

export function useWebSocket(onMessage?: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let active = true;

    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        ws.onopen = () => setConnected(true);
        ws.onclose = () => {
          setConnected(false);
          if (active) reconnectTimer = setTimeout(connect, 3000);
        };
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data);
            onMessageRef.current?.(data);
          } catch {}
        };
        wsRef.current = ws;
      } catch {
        if (active) reconnectTimer = setTimeout(connect, 3000);
      }
    };

    connect();
    return () => {
      active = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return { connected };
}
