import { Routes, Route } from 'react-router-dom';
import { AppLayout } from '@cloudscape-design/components';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {/* Training routes (Phase 3) */}
        {/* Dataset routes (Phase 4) */}
        {/* Resource routes (Phase 5) */}
        {/* Spaces routes (Phase 7) */}
      </Routes>
    </MainLayout>
  );
}

export default App;
