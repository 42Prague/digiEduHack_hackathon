import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { analyticsApi, transcriptsApi } from '../api/endpoints';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { 
  MapPin, 
  School,
  TrendingUp,
  Award,
  Target,
  AlertTriangle,
  Calendar,
  Clock
} from 'lucide-react';
import { 
  BarChart, 
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

export function RegionInsightsPage() {
  const navigate = useNavigate();
  const [selectedRegion, setSelectedRegion] = useState<string>('');

  // Fetch transcripts to get region list
  const { data: transcripts, isLoading: transcriptsLoading, error: transcriptsError } = useQuery({
    queryKey: ['transcripts'],
    queryFn: async () => {
      try {
        const result = await transcriptsApi.listTranscripts();
        console.log('📊 Transcripts fetched for region insights:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching transcripts:', error);
        throw error;
      }
    },
  });

  // Get unique regions
  const transcriptsArray = Array.isArray(transcripts) ? transcripts : [];
  const regions = Array.from(
    new Set(
      transcriptsArray.map(t => t.region_id).filter((id): id is string => id !== null && id !== undefined)
    )
  );

  // Fetch region insights
  const { data: insights, isLoading: insightsLoading, error: insightsError } = useQuery({
    queryKey: ['region-insights', selectedRegion],
    queryFn: () => analyticsApi.getRegionInsights(selectedRegion),
    enabled: !!selectedRegion,
  });

  if (transcriptsLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton />
      </div>
    );
  }

  if (transcriptsError) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'Region Insights' }]} />
        <ErrorBanner error={transcriptsError} />
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-slate-600 mb-4">Unable to load transcripts. Please check:</p>
              <ul className="text-sm text-slate-500 space-y-2">
                <li>• Backend is running on http://localhost:8000</li>
                <li>• Database is connected</li>
                <li>• CORS is configured correctly</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Region Insights' }]} />
      
      <div>
        <h1 className="text-3xl font-bold">Region Insights</h1>
        <p className="text-slate-600 mt-1">Analyze performance and trends by region</p>
      </div>

      {/* Region Selection */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <MapPin className="w-5 h-5 text-blue-600" />
            <div className="flex-1">
              <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                <SelectTrigger>
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  {regions.map((region) => (
                    <SelectItem key={region} value={region}>
                      {region}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {insightsError && (
        <ErrorBanner error={insightsError} />
      )}

          {regions.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <p className="text-slate-600 mb-2">No regions found</p>
                  <p className="text-sm text-slate-500 mb-4">
                    Upload audio files or transcripts with region metadata to view insights
                  </p>
                  <Button onClick={() => navigate('/upload-audio')}>
                    Upload Audio/Transcript
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : !selectedRegion ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  Please select a region to view insights
                </div>
              </CardContent>
            </Card>
          ) : insightsLoading ? (
        <LoadingSkeleton />
      ) : insights ? (
        <>
          {/* Overview Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600">Total Transcripts</p>
                    <p className="text-3xl mt-2">{insights.summary.total_transcripts}</p>
                    <p className="text-xs text-slate-500 mt-2">Analyzed</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <School className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600">Avg Collaboration</p>
                    <p className="text-3xl mt-2">{Math.round(Number(insights.summary.avg_collaboration ?? insights.summary.avg_collaboration_score ?? 0))}</p>
                    <Badge className={`mt-2 ${
                      Number(insights.summary.avg_collaboration ?? insights.summary.avg_collaboration_score ?? 0) >= 70 
                        ? 'bg-green-100 text-green-700 hover:bg-green-100'
                        : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    }`}>
                      {Number(insights.summary.avg_collaboration ?? insights.summary.avg_collaboration_score ?? 0) >= 70 ? 'Good' : 'Needs Improvement'}
                    </Badge>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                    <Target className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600">Avg Mindset Shift</p>
                    <p className="text-3xl mt-2">{Math.round(Number(insights.summary.avg_mindset_shift ?? insights.summary.avg_mindset_shift_score ?? 0))}</p>
                    <Badge className={`mt-2 ${
                      Number(insights.summary.avg_mindset_shift ?? insights.summary.avg_mindset_shift_score ?? 0) >= 70 
                        ? 'bg-green-100 text-green-700 hover:bg-green-100'
                        : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    }`}>
                      {Number(insights.summary.avg_mindset_shift ?? insights.summary.avg_mindset_shift_score ?? 0) >= 70 ? 'Positive' : 'Needs Work'}
                    </Badge>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <Award className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600">Avg Sentiment</p>
                    <p className="text-3xl mt-2">{Math.round(Number(insights.summary.avg_sentiment ?? insights.summary.avg_sentiment_score ?? 50))}</p>
                    <Badge className={`mt-2 ${
                      Number(insights.summary.avg_sentiment ?? insights.summary.avg_sentiment_score ?? 50) >= 70 
                        ? 'bg-green-100 text-green-700 hover:bg-green-100'
                        : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    }`}>
                      {Number(insights.summary.avg_sentiment ?? insights.summary.avg_sentiment_score ?? 50) >= 70 ? 'Positive' : 'Needs Attention'}
                    </Badge>
                  </div>
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs for Different Views */}
          <Tabs defaultValue="performance" className="space-y-6">
            <TabsList>
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="interventions">Interventions</TabsTrigger>
              <TabsTrigger value="themes">Themes</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
            </TabsList>

            <TabsContent value="performance" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {Array.isArray(insights.top_schools) && insights.top_schools.length > 0 && (
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Top Performing Schools</CardTitle>
                      <p className="text-sm text-slate-600">Best schools in {selectedRegion}</p>
                    </CardHeader>
                  <CardContent>
                    <div style={{ width: '100%', height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={insights.top_schools.map((school: any) => {
                          const schoolId = school.school_id || school[0] || 'Unknown';
                          const scores = school.scores || school[1]?.scores || {};
                          const scoreValues = Object.values(scores).map(v => Number(v ?? 0));
                          const avgScore = scoreValues.length > 0 
                            ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length 
                            : 0;
                          return {
                            name: schoolId,
                            score: avgScore,
                          };
                        })} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis type="number" domain={[0, 100]} stroke="#64748b" />
                          <YAxis dataKey="name" type="category" width={150} stroke="#64748b" />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: 'white', 
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px'
                            }}
                          />
                          <Bar dataKey="score" fill="#3b82f6" radius={[0, 8, 8, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                  </Card>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle>Summary Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm">Collaboration</span>
                        <span className="text-sm">{Math.round(Number(insights.summary.avg_collaboration ?? insights.summary.avg_collaboration_score ?? 0))}</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${Number(insights.summary.avg_collaboration ?? insights.summary.avg_collaboration_score ?? 0)}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm">Mindset Shift</span>
                        <span className="text-sm">{Math.round(Number(insights.summary.avg_mindset_shift ?? insights.summary.avg_mindset_shift_score ?? 0))}</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-purple-600 rounded-full" style={{ width: `${Number(insights.summary.avg_mindset_shift ?? insights.summary.avg_mindset_shift_score ?? 0)}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm">Teacher Confidence</span>
                        <span className="text-sm">{Math.round(Number(insights.summary.avg_confidence ?? insights.summary.avg_teacher_confidence ?? insights.summary.avg_teacher_confidence_score ?? 0))}</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-green-600 rounded-full" style={{ width: `${Number(insights.summary.avg_confidence ?? insights.summary.avg_teacher_confidence ?? insights.summary.avg_teacher_confidence_score ?? 0)}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm">Municipality Cooperation</span>
                        <span className="text-sm">{Math.round(Number(insights.summary.avg_municipality_cooperation ?? insights.summary.avg_municipality_cooperation_score ?? insights.summary.avg_cooperation_municipality_score ?? 0))}</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-orange-600 rounded-full" style={{ width: `${Number(insights.summary.avg_municipality_cooperation ?? insights.summary.avg_municipality_cooperation_score ?? insights.summary.avg_cooperation_municipality_score ?? 0)}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm">Sentiment</span>
                        <span className="text-sm">{Math.round(Number(insights.summary.avg_sentiment ?? insights.summary.avg_sentiment_score ?? 50))}</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-pink-600 rounded-full" style={{ width: `${Number(insights.summary.avg_sentiment ?? insights.summary.avg_sentiment_score ?? 50)}%` }}></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {Array.isArray(insights.schools_needing_support) && insights.schools_needing_support.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-600" />
                      Schools Needing Support
                    </CardTitle>
                    <p className="text-sm text-slate-600">Schools below region average</p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {insights.schools_needing_support.map((school: any, idx: number) => {
                        const schoolId = school.school_id || school[0] || `School ${idx + 1}`;
                        const scores = school.scores || school[1]?.scores || {};
                        const scoreValues = Object.values(scores).map(v => Number(v ?? 0));
                        const avgScore = scoreValues.length > 0 
                          ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length 
                          : 0;
                        return (
                          <div key={idx} className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium">{schoolId}</p>
                                <p className="text-sm text-slate-600">
                                  Avg Score: {Math.round(avgScore)}
                                </p>
                              </div>
                              <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100">
                                Needs Support
                              </Badge>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="interventions" className="space-y-6">
              {insights.intervention_effectiveness && typeof insights.intervention_effectiveness === 'object' && Object.keys(insights.intervention_effectiveness).length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Intervention Effectiveness</CardTitle>
                    <p className="text-sm text-slate-600">Performance by intervention type</p>
                  </CardHeader>
                  <CardContent>
                    <div style={{ width: '100%', height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(insights.intervention_effectiveness).map(([key, value]: [string, any]) => ({
                          intervention: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                          avg_score: Number(value?.avg_score ?? value?.score ?? 0),
                          count: Number(value?.count ?? 0),
                        })).filter(item => item.avg_score > 0 || item.count > 0)}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="intervention" stroke="#64748b" />
                          <YAxis stroke="#64748b" />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: 'white', 
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px'
                            }}
                          />
                          <Bar dataKey="avg_score" fill="#3b82f6" name="Average Score" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="mt-4 space-y-2">
                      {Object.entries(insights.intervention_effectiveness).map(([key, value]: [string, any]) => {
                        const avgScore = Number(value?.avg_score ?? value?.score ?? 0);
                        const count = Number(value?.count ?? 0);
                        return (
                          <div key={key} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                            <span className="text-sm">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                            <div className="flex items-center gap-4">
                              <span className="text-sm text-slate-600">{count} transcripts</span>
                              <Badge>{Math.round(avgScore)}</Badge>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center py-8 text-slate-500">
                      No intervention effectiveness data available
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="themes" className="space-y-6">
              {Array.isArray(insights.frequent_themes) && insights.frequent_themes.length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Frequent Themes</CardTitle>
                    <p className="text-sm text-slate-600">Most mentioned themes in {selectedRegion}</p>
                  </CardHeader>
                  <CardContent>
                    <div style={{ width: '100%', height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={insights.frequent_themes.map((t: any) => {
                          const theme = typeof t === 'string' ? t : (t.theme || t.name || 'Unknown');
                          const count = typeof t === 'number' ? t : Number(t.count ?? t.value ?? 0);
                          return {
                            theme,
                            count,
                          };
                        }).filter(item => item.count > 0)} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis type="number" stroke="#64748b" />
                          <YAxis dataKey="theme" type="category" width={200} stroke="#64748b" />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: 'white', 
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px'
                            }}
                          />
                          <Bar dataKey="count" fill="#8b5cf6" radius={[0, 8, 8, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center py-8 text-slate-500">
                      No theme data available
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-500">
              {insights && insights.summary && insights.summary.total_transcripts === 0 
                ? "No transcripts found for this region. Upload audio/transcript files to generate insights."
                : "No insights available for this region"}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
