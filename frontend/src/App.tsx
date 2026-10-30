export function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-400 font-bold text-2xl mb-4">
          📈
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
          Stock Trading Platform
        </h1>
        <p className="text-slate-400 text-sm mb-6">
          Advanced Paper Trading & Portfolio Management with Real-Time NSE Simulation
        </p>
        <div className="grid grid-cols-2 gap-4 text-left p-4 bg-slate-950/60 rounded-lg border border-slate-800/80 mb-6">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Frontend Status</p>
            <p className="text-emerald-400 font-medium flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Vite + React Active
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Backend Target</p>
            <p className="text-slate-300 font-medium mt-1">FastAPI (/api/v1)</p>
          </div>
        </div>
        <p className="text-xs text-slate-500">
          Phase 1 Environment & Scaffolding initialized.
        </p>
      </div>
    </div>
  )
}

export default App
