import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CreateBetSlip from './pages/CreateBetSlip';
import Analysis from './pages/Analysis';
import HalftimeAnalyzer from './pages/HalftimeAnalyzer';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/create" element={<CreateBetSlip />} />
        <Route path="/analysis/:id" element={<Analysis />} />
        <Route path="/halftime" element={<HalftimeAnalyzer />} />
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
