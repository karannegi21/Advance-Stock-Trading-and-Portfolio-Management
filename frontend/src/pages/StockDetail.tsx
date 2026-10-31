import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { createChart, CandlestickSeries } from 'lightweight-charts';

export default function StockDetail() {
  const { symbol } = useParams();
  const qc = useQueryClient();
  const chartRef = useRef<HTMLDivElement>(null);

  const [side, setSide] = useState('BUY');
  const [type, setType] = useState('MARKET');
  const [qty, setQty] = useState(1);
  const [limitPrice, setLimitPrice] = useState('');

  const { data: detail } = useQuery({
    queryKey: ['stock', symbol],
    queryFn: async () => (await api.get(`/stocks/${symbol}`)).data,
  });

  const { data: history } = useQuery({
    queryKey: ['history', symbol],
    queryFn: async () => (await api.get(`/stocks/${symbol}/history`, { params: { range: '6M' } })).data,
  });

  useEffect(() => {
    if (!chartRef.current || !history?.bars?.length) return;
    const chart = createChart(chartRef.current, { width: chartRef.current.clientWidth, height: 360, layout: { background: { color: '#0f172a' }, textColor: '#cbd5e1' } });
    const series = chart.addSeries(CandlestickSeries, { upColor: '#10b981', downColor: '#ef4444', borderVisible: false, wickUpColor: '#10b981', wickDownColor: '#ef4444' });
    series.setData(history.bars.map((b: any) => ({
      time: b.trade_date,
      open: Number(b.open),
      high: Number(b.high),
      low: Number(b.low),
      close: Number(b.close),
    })));
    chart.timeScale().fitContent();
    const handleResize = () => chart.applyOptions({ width: chartRef.current!.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [history]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload: any = { symbol, side, type, quantity: Number(qty) };
      if (type === 'LIMIT') payload.limit_price = Number(limitPrice);
      const r = await api.post('/orders', payload);
      return r.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolio'] });
      alert('Order placed');
    },
    onError: (e: any) => alert(e.response?.data?.detail || 'Order failed'),
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <h1 className="text-2xl font-bold text-emerald-400 mb-2">{symbol}</h1>
        {detail && (
          <div className="mb-4 text-sm text-slate-300">
            {detail.name} · {detail.sector} · Current: <span className="font-semibold">{detail.current_price}</span>
            {detail.change_pct != null && <span className={Number(detail.change_pct) >= 0 ? 'text-emerald-400 ml-2' : 'text-red-400 ml-2'}>{Number(detail.change_pct).toFixed(2)}%</span>}
          </div>
        )}
        <div ref={chartRef} className="bg-slate-900 border border-slate-800 rounded-lg" />
      </div>
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 h-fit">
        <h2 className="font-bold mb-4">Order Ticket</h2>
        <div className="space-y-3">
          <div className="flex gap-2">
            <button onClick={() => setSide('BUY')} className={`flex-1 py-2 rounded ${side === 'BUY' ? 'bg-emerald-600' : 'bg-slate-800'}`}>Buy</button>
            <button onClick={() => setSide('SELL')} className={`flex-1 py-2 rounded ${side === 'SELL' ? 'bg-red-600' : 'bg-slate-800'}`}>Sell</button>
          </div>
          <select value={type} onChange={(e) => setType(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2">
            <option value="MARKET">Market</option>
            <option value="LIMIT">Limit</option>
          </select>
          <input type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2" placeholder="Quantity" />
          {type === 'LIMIT' && (
            <input type="number" value={limitPrice} onChange={(e) => setLimitPrice(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2" placeholder="Limit price" />
          )}
          <button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-full bg-emerald-600 hover:bg-emerald-500 py-2 rounded font-semibold">
            {mutation.isPending ? 'Placing...' : `Place ${side} order`}
          </button>
        </div>
      </div>
    </div>
  );
}
