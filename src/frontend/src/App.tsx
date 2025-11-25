import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { DataUploadPage } from './pages/DataUploadPage';
import { UploadAudioPage } from './pages/UploadAudioPage';
import { TranscriptAnalysisPage } from './pages/TranscriptAnalysisPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { SchoolComparisonPage } from './pages/SchoolComparisonPage';
import { RegionInsightsPage } from './pages/RegionInsightsPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { useState } from 'react';

export default function App() {
  const [isAuthenticated] = useState(true); // Skip auth for hackathon demo

  if (!isAuthenticated) {
    return <LoginPage onLogin={() => {}} />;
  }

  return (
    <>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload-data" element={<DataUploadPage />} />
          <Route path="/upload-audio" element={<UploadAudioPage />} />
          <Route path="/transcripts/:id" element={<TranscriptAnalysisPage />} />
          <Route path="/dq/:dataset_id" element={<DataQualityPage />} />
          <Route path="/qa/:dataset_id" element={<DataQualityPage />} />
          <Route path="/compare" element={<SchoolComparisonPage />} />
          <Route path="/region-insights" element={<RegionInsightsPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
      <Toaster position="top-right" />
    </>
  );
}
