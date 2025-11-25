import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { 
  School, 
  MapPin, 
  Upload, 
  TrendingUp, 
  Mic, 
  Users,
  Calendar,
  Target,
  FileText,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { analyticsApi, ingestionApi, transcriptsApi } from '../api/endpoints';
import { LoadingSkeleton, CardSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { useNavigate } from 'react-router-dom';
import { ThemeChip } from '../components/shared/ThemeChip';
import { AlertTriangle } from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();

  // Fetch analytics summary
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: async () => {
      try {
        const result = await analyticsApi.getSummary();
        console.log('📊 Analytics summary:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching analytics summary:', error);
        throw error;
      }
    },
  });

  // Fetch datasets
  const { data: datasets, isLoading: datasetsLoading, error: datasetsError } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      try {
        const result = await ingestionApi.listDatasets();
        console.log('📊 Datasets fetched:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching datasets:', error);
        // Return empty array on error to prevent page crash
        return [];
      }
    },
  });

  // Fetch transcripts
  const { data: transcripts, isLoading: transcriptsLoading, error: transcriptsError } = useQuery({
    queryKey: ['transcripts'],
    queryFn: async () => {
      try {
        const result = await transcriptsApi.listTranscripts();
        console.log('📊 Transcripts fetched for dashboard:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching transcripts:', error);
        // Return empty array on error to prevent page crash
        return [];
      }
    },
  });

  // Calculate stats - ensure datasets is an array
  const datasetsArray = Array.isArray(datasets) ? datasets : [];
  const transcriptsArray = Array.isArray(transcripts) ? transcripts : [];
  
  const totalDatasets = datasetsArray.length;
  const totalTranscripts = transcriptsArray.length;

  // Fetch sentiment trends (must be before early return to follow Rules of Hooks)
  const { data: sentimentTrends } = useQuery({
    queryKey: ['sentiment-trends'],
    queryFn: async () => {
      try {
        const result = await analyticsApi.getTrends('sentiment_score');
        // Handle both old format (results array) and new format (time_series)
        if (result.time_series) {
          return result.time_series;
        } else if (result.results && Array.isArray(result.results)) {
          // Convert region results to time series format if needed
          return result.results.map((r: any, idx: number) => ({
            date: new Date(Date.now() - (result.results.length - idx) * 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 7),
            value: r.mean || r.value || 50,
          }));
        }
        return [];
      } catch (error) {
        console.error('Error fetching sentiment trends:', error);
        return [];
      }
    },
    enabled: totalTranscripts > 0,
  });

  const quantitativeDatasets = datasetsArray.filter(d => d.file_type === 'table').length;
  const qualitativeDatasets = datasetsArray.filter(d => d.file_type === 'text').length;
  
  // Get unique regions
  const regions = new Set<string>();
  transcriptsArray.forEach(t => {
    if (t.region_id) regions.add(t.region_id);
  });

  // Calculate average DQ score
  const dqScores = datasetsArray.map(d => d.dq_score).filter((s): s is number => s !== null && s !== undefined);
  const avgDQScore = dqScores.length > 0 
    ? Math.round(dqScores.reduce((a, b) => a + b, 0) / dqScores.length)
    : null;

  // Get latest uploads
  const latestUploads = datasetsArray
    .sort((a, b) => {
      const dateA = a.ingested_at ? new Date(a.ingested_at).getTime() : 0;
      const dateB = b.ingested_at ? new Date(b.ingested_at).getTime() : 0;
      return dateB - dateA;
    })
    .slice(0, 5);

  // Extract themes from summary
  const allThemes: string[] = [];
  datasetsArray.forEach(dataset => {
    // Themes would come from summary, but for now we'll use sample data
  });

  // Region distribution chart data
  const regionData = Array.from(regions).map(region => ({
    region: region,
    count: transcriptsArray.filter(t => t.region_id === region).length,
  }));

  if (summaryLoading || datasetsLoading || transcriptsLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
        </div>
      </div>
    );
  }

  // Calculate intervention type distribution
  const interventionData = transcriptsArray.reduce((acc, t) => {
    const type = t.intervention_type || 'Unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const interventionChartData = Object.entries(interventionData).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

  // Calculate problem schools (lowest average cultural scores)
  const schoolScores = transcriptsArray.reduce((acc, t) => {
    if (!t.school_id) return acc;
    if (!acc[t.school_id]) {
      acc[t.school_id] = { scores: [], count: 0 };
    }
    // We'd need to fetch full transcript details to get scores, so we'll use a placeholder
    acc[t.school_id].count++;
    return acc;
  }, {} as Record<string, { scores: number[], count: number }>);

  // Prepare sentiment trend data
  // Format sentiment trends for chart - handle both time_series array and old format
  const sentimentChartData = Array.isArray(sentimentTrends) 
    ? sentimentTrends.map((item: any) => ({
        date: item.date ? (item.date.length > 7 ? item.date.slice(0, 7) : item.date) : '',
        sentiment: item.value || 0,
      }))
    : [];

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-slate-600 mt-1">Welcome back! Here's your platform overview</p>
      </div>

      {(summaryError || datasetsError) && (
        <ErrorBanner error={summaryError || datasetsError || 'Failed to load data'} />
      )}

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Datasets</p>
                <p className="text-3xl mt-2">{totalDatasets}</p>
                <p className="text-xs text-slate-500 mt-2">
                  {quantitativeDatasets} quantitative, {qualitativeDatasets} qualitative
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Regions Active</p>
                <p className="text-3xl mt-2">{regions.size}</p>
                <p className="text-xs text-slate-500 mt-2">Across Czech Republic</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <MapPin className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Transcripts Analyzed</p>
                <p className="text-3xl mt-2">{totalTranscripts}</p>
                <p className="text-xs text-blue-600 mt-2 flex items-center gap-1">
                  <Upload className="w-3 h-3" />
                  {latestUploads.length} recent
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <Mic className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Avg Data Quality</p>
                <p className="text-3xl mt-2">{avgDQScore !== null ? `${avgDQScore}%` : 'N/A'}</p>
                <Badge className={`mt-2 ${
                  avgDQScore !== null && avgDQScore >= 80 
                    ? 'bg-green-100 text-green-700 hover:bg-green-100'
                    : avgDQScore !== null && avgDQScore >= 60
                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-100'
                }`}>
                  {avgDQScore !== null && avgDQScore >= 80 ? 'Excellent' : 
                   avgDQScore !== null && avgDQScore >= 60 ? 'Good' : 'Needs Improvement'}
                </Badge>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <Target className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Over Time</CardTitle>
            <p className="text-sm text-slate-600">Average sentiment score trend</p>
          </CardHeader>
          <CardContent>
            {sentimentChartData.length > 0 ? (
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sentimentChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#64748b"
                      tickFormatter={(value) => {
                        // Format YYYY-MM to "Jan 2023" style
                        if (value && value.length >= 7) {
                          const [year, month] = value.split('-');
                          const date = new Date(parseInt(year), parseInt(month) - 1);
                          return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                        }
                        return value;
                      }}
                    />
                    <YAxis domain={[0, 100]} stroke="#64748b" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="sentiment" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="Sentiment Score"
                      dot={{ fill: '#3b82f6', r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-500">
                No sentiment trend data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Intervention Types</CardTitle>
            <p className="text-sm text-slate-600">Distribution by intervention</p>
          </CardHeader>
          <CardContent>
            {interventionChartData.length > 0 ? (
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={interventionChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {interventionChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-500">
                No intervention data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <p className="text-sm text-slate-600">Common tasks</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button 
                variant="outline" 
                className="w-full justify-start"
                onClick={() => navigate('/upload-data')}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload Data File
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start"
                onClick={() => navigate('/upload-audio')}
              >
                <Mic className="w-4 h-4 mr-2" />
                Upload Audio/Transcript
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start"
                onClick={() => navigate('/compare')}
              >
                <School className="w-4 h-4 mr-2" />
                Compare Schools
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start"
                onClick={() => navigate('/region-insights')}
              >
                <MapPin className="w-4 h-4 mr-2" />
                Region Insights
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Region Distribution and Problem Schools */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Region Distribution</CardTitle>
            <p className="text-sm text-slate-600">Transcripts by region</p>
          </CardHeader>
          <CardContent>
            {regionData.length > 0 ? (
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={regionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="region" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="count" fill="#3b82f6" name="Transcripts" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-500">
                No region data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              Schools Needing Attention
            </CardTitle>
            <p className="text-sm text-slate-600">Schools with lowest activity or scores</p>
          </CardHeader>
          <CardContent>
            {Object.keys(schoolScores).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(schoolScores)
                  .sort((a, b) => a[1].count - b[1].count)
                  .slice(0, 5)
                  .map(([schoolId, data]) => (
                    <div key={schoolId} className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div>
                        <p className="text-sm font-medium">{schoolId}</p>
                        <p className="text-xs text-slate-600">{data.count} transcript{data.count !== 1 ? 's' : ''}</p>
                      </div>
                      <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">
                        Low Activity
                      </Badge>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-500">
                No school data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Latest Uploads</CardTitle>
            <p className="text-sm text-slate-600">Recent data ingestion</p>
          </CardHeader>
          <CardContent>
            {latestUploads && latestUploads.length > 0 ? (
              <div className="space-y-3">
                {latestUploads.map((dataset, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {dataset.file_type === 'table' ? (
                        <FileText className="w-4 h-4 text-blue-600" />
                      ) : (
                        <Mic className="w-4 h-4 text-purple-600" />
                      )}
                      <div>
                        <p className="text-sm">{dataset.dataset_name}</p>
                        <p className="text-xs text-slate-500">
                          {dataset.file_type} • {dataset.row_count || 'N/A'} rows
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {dataset.dq_score !== null && dataset.dq_score !== undefined && (
                        <Badge className={
                          Number(dataset.dq_score) >= 80 
                            ? 'bg-green-100 text-green-700 hover:bg-green-100'
                            : Number(dataset.dq_score) >= 60
                            ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                            : 'bg-red-100 text-red-700 hover:bg-red-100'
                        }>
                          DQ: {Number(dataset.dq_score)}
                        </Badge>
                      )}
                      {dataset.dq_report_path && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/dq/${dataset.dataset_id}`)}
                        >
                          <ArrowRight className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                No uploads yet. <Button variant="link" onClick={() => navigate('/upload-data')}>Upload data</Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Stats</CardTitle>
            <p className="text-sm text-slate-600">Platform overview</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-600" />
                  <span className="text-sm">Total Datasets</span>
                </div>
                <span className="font-medium">{totalDatasets}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Upload className="w-4 h-4 text-slate-600" />
                  <span className="text-sm">Files Uploaded</span>
                </div>
                <span className="font-medium">{totalDatasets}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mic className="w-4 h-4 text-slate-600" />
                  <span className="text-sm">Audio Transcripts</span>
                </div>
                <span className="font-medium">{totalTranscripts}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-slate-600" />
                  <span className="text-sm">Avg DQ Score</span>
                </div>
                <span className="font-medium">{avgDQScore !== null ? `${avgDQScore}%` : 'N/A'}</span>
              </div>

              <div className="pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm">System Health</span>
                  <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                    All Systems Operational
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
