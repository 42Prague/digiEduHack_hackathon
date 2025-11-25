import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { FileUpload } from '../components/shared/FileUpload';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ingestionApi } from '../api/endpoints';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight,
  FileSpreadsheet,
  Eye
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';

export function DataUploadPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);

  // Fetch datasets for recent uploads
  const { data: datasets, isLoading: datasetsLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => ingestionApi.listDatasets(),
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => ingestionApi.ingestFile(file),
    onSuccess: (data) => {
      setUploadResult(data);
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      queryClient.invalidateQueries({ queryKey: ['analytics-summary'] });
      toast.success('File uploaded successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Upload failed');
    },
  });

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setUploadResult(null);
  };

  const handleUpload = () => {
    if (!selectedFile) return;
    uploadMutation.mutate(selectedFile);
  };

  const datasetsArray = Array.isArray(datasets) ? datasets : [];
  const latestUploads = datasetsArray
    .sort((a, b) => {
      const dateA = a.ingested_at ? new Date(a.ingested_at).getTime() : 0;
      const dateB = b.ingested_at ? new Date(b.ingested_at).getTime() : 0;
      return dateB - dateA;
    })
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Upload Data' }]} />
      
      <div>
        <h1 className="text-3xl font-bold">Upload Data</h1>
        <p className="text-slate-600 mt-1">Upload and manage school data files</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Area */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Upload Files</CardTitle>
            <p className="text-sm text-slate-600">Supports CSV, Excel, JSON, TXT, MD, DOCX</p>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload
              onFileSelect={handleFileSelect}
              accept={{
                'text/csv': ['.csv'],
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                'application/json': ['.json'],
                'text/plain': ['.txt'],
                'text/markdown': ['.md'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
              }}
              disabled={uploadMutation.isPending}
            />

            {selectedFile && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {selectedFile.name.endsWith('.csv') ? (
                      <FileSpreadsheet className="w-5 h-5 text-green-600" />
                    ) : selectedFile.name.endsWith('.xlsx') ? (
                      <FileSpreadsheet className="w-5 h-5 text-green-600" />
                    ) : selectedFile.name.endsWith('.json') ? (
                      <FileText className="w-5 h-5 text-blue-600" />
                    ) : selectedFile.name.endsWith('.txt') || selectedFile.name.endsWith('.md') ? (
                      <FileText className="w-5 h-5 text-purple-600" />
                    ) : selectedFile.name.endsWith('.docx') ? (
                      <FileText className="w-5 h-5 text-orange-600" />
                    ) : (
                      <FileText className="w-5 h-5 text-slate-600" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{selectedFile.name}</p>
                      <p className="text-xs text-slate-600">
                        {(selectedFile.size / 1024).toFixed(2)} KB • {
                          selectedFile.name.endsWith('.csv') ? 'CSV' :
                          selectedFile.name.endsWith('.xlsx') ? 'Excel' :
                          selectedFile.name.endsWith('.json') ? 'JSON' :
                          selectedFile.name.endsWith('.txt') ? 'Text' :
                          selectedFile.name.endsWith('.md') ? 'Markdown' :
                          selectedFile.name.endsWith('.docx') ? 'Word Document' :
                          'Unknown'
                        } format
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedFile && (
              <Button
                onClick={handleUpload}
                disabled={uploadMutation.isPending}
                className="w-full"
              >
                {uploadMutation.isPending ? (
                  <>Uploading...</>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload File
                  </>
                )}
              </Button>
            )}

            {uploadMutation.error && (
              <ErrorBanner error={uploadMutation.error} />
            )}

            {uploadResult && (
              <Card className="bg-green-50 border-green-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    Upload Successful
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-600">Dataset ID:</p>
                      <p className="font-medium">{uploadResult.dataset_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">File Type:</p>
                      <Badge>{uploadResult.file_type || uploadResult.classification}</Badge>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-600">Classification:</p>
                      <Badge variant="outline">{uploadResult.classification}</Badge>
                    </div>
                    {uploadResult.row_count !== null && (
                      <div>
                        <p className="text-sm text-slate-600">Rows:</p>
                        <p className="font-medium">{uploadResult.row_count.toLocaleString()}</p>
                      </div>
                    )}
                  </div>

                  {uploadResult.dq_score !== null && (
                    <div>
                      <p className="text-sm text-slate-600 mb-2">Data Quality Score:</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-3 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${
                              uploadResult.dq_score >= 80 ? 'bg-green-600' :
                              uploadResult.dq_score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                            }`}
                            style={{ width: `${uploadResult.dq_score}%` }}
                          />
                        </div>
                        <Badge className={
                          uploadResult.dq_score >= 80 
                            ? 'bg-green-100 text-green-700 hover:bg-green-100'
                            : uploadResult.dq_score >= 60
                            ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                            : 'bg-red-100 text-red-700 hover:bg-red-100'
                        }>
                          {uploadResult.dq_score}%
                        </Badge>
                      </div>
                    </div>
                  )}

                  {uploadResult.dq_report_path && (
                    <div>
                      <p className="text-sm text-slate-600 mb-2">Data Quality Report:</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/dq/${uploadResult.dataset_id}`)}
                        className="w-full"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        View Full DQ Report
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  )}

                  {uploadResult.auto_summary && (
                    <div>
                      <p className="text-sm text-slate-600 mb-2">Auto-Generated Summary:</p>
                      <div className="bg-white p-4 rounded-lg border border-slate-200">
                        <p className="text-sm leading-relaxed">{uploadResult.auto_summary}</p>
                      </div>
                    </div>
                  )}

                  {uploadResult.summary_path && (
                    <div>
                      <p className="text-sm text-slate-600 mb-2">Summary File:</p>
                      <p className="text-xs text-slate-500 font-mono bg-white p-2 rounded border">
                        {uploadResult.summary_path}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>

        {/* Upload Stats */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Total Uploads</span>
                <span className="font-medium">{datasetsArray.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">This Week</span>
                <span className="font-medium">
                  {datasetsArray.filter(d => {
                    if (!d.ingested_at) return false;
                    const date = new Date(d.ingested_at);
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return date >= weekAgo;
                  }).length}
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <div className="text-sm text-slate-600 mb-2">Success Rate</div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-green-600 rounded-full transition-all"
                    style={{ width: '95%' }}
                  />
                </div>
                <span className="text-sm">95%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Uploads Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Uploads</CardTitle>
          <p className="text-sm text-slate-600">Latest file processing status</p>
        </CardHeader>
        <CardContent>
          {datasetsLoading ? (
            <LoadingSkeleton />
          ) : latestUploads.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4">File Name</th>
                    <th className="text-left py-3 px-4">Type</th>
                    <th className="text-left py-3 px-4">Rows</th>
                    <th className="text-left py-3 px-4">DQ Score</th>
                    <th className="text-left py-3 px-4">Date</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {latestUploads.map((dataset, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {dataset.file_type === 'table' ? (
                            <FileSpreadsheet className="w-4 h-4 text-green-600" />
                          ) : (
                            <FileText className="w-4 h-4 text-blue-600" />
                          )}
                          <span className="text-sm">{dataset.dataset_name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline">{dataset.file_type}</Badge>
                      </td>
                      <td className="py-3 px-4 text-sm">
                        {dataset.row_count !== null ? dataset.row_count.toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        {dataset.dq_score !== null ? (
                          <Badge className={
                            dataset.dq_score >= 80 
                              ? 'bg-green-100 text-green-700 hover:bg-green-100'
                              : dataset.dq_score >= 60
                              ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                              : 'bg-red-100 text-red-700 hover:bg-red-100'
                          }>
                            {dataset.dq_score}
                          </Badge>
                        ) : (
                          <span className="text-sm text-slate-500">N/A</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-500">
                        {dataset.ingested_at 
                          ? new Date(dataset.ingested_at).toLocaleDateString()
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        {dataset.dq_report_path && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/dq/${dataset.dataset_id}`)}
                          >
                            View
                            <ArrowRight className="w-4 h-4 ml-1" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              No uploads yet. Upload your first file above.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
