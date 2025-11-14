import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { FileUpload } from '../components/shared/FileUpload';
import { MetadataForm, MetadataFormData } from '../components/shared/MetadataForm';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { ingestionApi } from '../api/endpoints';
import { Mic, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';

export function UploadAudioPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<MetadataFormData | null>(null);

  const uploadMutation = useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata: MetadataFormData }) =>
      ingestionApi.uploadAudio(file, metadata),
    onSuccess: (data) => {
      // Invalidate all relevant queries for real-time updates
      queryClient.invalidateQueries({ queryKey: ['transcripts'] });
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-summary'] });
      queryClient.invalidateQueries({ queryKey: ['sentiment-trends'] });
      queryClient.invalidateQueries({ queryKey: ['region-insights'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
      
      toast.success('Audio/transcript uploaded successfully!');
      // Navigate to transcript analysis page if we have an ID
      if (data.dataset_id) {
        navigate(`/transcripts/${data.dataset_id}`);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Upload failed');
    },
  });

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleMetadataSubmit = (data: MetadataFormData) => {
    setMetadata(data);
    if (selectedFile) {
      uploadMutation.mutate({ file: selectedFile, metadata: data });
    }
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Upload Audio/Transcript' }]} />
      
      <div>
        <h1 className="text-3xl font-bold">Upload Audio/Transcript</h1>
        <p className="text-slate-600 mt-1">Upload audio files or transcript text files with metadata</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Upload */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="w-5 h-5" />
              File Upload
            </CardTitle>
            <p className="text-sm text-slate-600">Supports WAV, MP3, M4A, TXT, JSON</p>
          </CardHeader>
          <CardContent>
            <FileUpload
              onFileSelect={handleFileSelect}
              accept={{
                'audio/*': ['.wav', '.mp3', '.m4a'],
                'text/plain': ['.txt'],
                'application/json': ['.json'],
              }}
              disabled={uploadMutation.isPending}
            />
          </CardContent>
        </Card>

        {/* Metadata Form */}
        <MetadataForm
          onSubmit={handleMetadataSubmit}
          isLoading={uploadMutation.isPending}
        />
      </div>

      {uploadMutation.error && (
        <ErrorBanner error={uploadMutation.error} onRetry={() => {
          if (selectedFile && metadata) {
            uploadMutation.mutate({ file: selectedFile, metadata });
          }
        }} />
      )}

      {uploadMutation.isSuccess && uploadMutation.data && (
        <Card className="bg-green-50 border-green-200">
          <CardHeader>
            <CardTitle>Upload Successful</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4">
              File uploaded and processed. Redirecting to analysis page...
            </p>
            {uploadMutation.data.cultural_analysis && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Cultural Analysis:</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Mindset Shift: {uploadMutation.data.cultural_analysis.mindset_shift_score}</div>
                  <div>Collaboration: {uploadMutation.data.cultural_analysis.collaboration_score}</div>
                  <div>Teacher Confidence: {uploadMutation.data.cultural_analysis.teacher_confidence_score}</div>
                  <div>Sentiment: {uploadMutation.data.cultural_analysis.sentiment}</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

