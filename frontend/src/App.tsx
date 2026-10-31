import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Market from './pages/Market';
import StockDetail from './pages/StockDetail';
import Portfolio from './pages/Portfolio';
import Orders from './pages/Orders';
import Analytics from './pages/Analytics';
import Watchlist from './pages/Watchlist';
import Leaderboard from './pages/Leaderboard';
import AdminPanel from './pages/AdminPanel';
import { useAuthStore } from './store/authStore';

const qc = new QueryClient();

function Protected({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Navigate to="/market" replace />} />
            <Route path="/market" element={<Protected><Market /></Protected>} />
            <Route path="/stocks/:symbol" element={<Protected><StockDetail /></Protected>} />
            <Route path="/portfolio" element={<Protected><Portfolio /></Protected>} />
            <Route path="/orders" element={<Protected><Orders /></Protected>} />
            <Route path="/analytics" element={<Protected><Analytics /></Protected>} />
            <Route path="/watchlist" element={<Protected><Watchlist /></Protected>} />
            <Route path="/leaderboard" element={<Protected><Leaderboard /></Protected>} />
            <Route path="/admin" element={<Protected><AdminPanel /></Protected>} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
