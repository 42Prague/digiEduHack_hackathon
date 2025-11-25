import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { schoolsApi, transcriptsApi } from '../api/endpoints';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { 
  TrendingUp, 
  TrendingDown,
  Minus,
  School,
  Filter,
  BarChart3
} from 'lucide-react';
import { 
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';

export function SchoolComparisonPage() {
  const [comparisonMode, setComparisonMode] = useState<'schools' | 'dimension'>('schools');
  const [school1, setSchool1] = useState<string>('');
  const [school2, setSchool2] = useState<string>('');
  const [metric, setMetric] = useState<string>('');
  
  // Dimension comparison state
  const [dimension, setDimension] = useState<'school_type' | 'intervention_type' | 'participant_role'>('school_type');
  const [filters, setFilters] = useState({
    school_type: '',
    intervention_type: '',
    participant_role: '',
    date_from: '',
    date_to: '',
  });

  // Fetch transcripts to get school list
  const { data: transcripts, isLoading: transcriptsLoading, error: transcriptsError } = useQuery({
    queryKey: ['transcripts'],
    queryFn: async () => {
      try {
        const result = await transcriptsApi.listTranscripts();
        console.log('📊 Transcripts fetched for comparison:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching transcripts:', error);
        throw error;
      }
    },
  });

  // Get unique schools from transcripts
  const transcriptsArray = Array.isArray(transcripts) ? transcripts : [];
  const schools = Array.from(
    new Set(
      transcriptsArray.map(t => t.school_id).filter((id): id is string => id !== null && id !== undefined)
    )
  ).map(schoolId => ({
    id: schoolId,
    name: schoolId,
  }));

  // Get unique values for filters
  const schoolTypes = Array.from(new Set(transcriptsArray.map(t => t.school_type).filter((t): t is string => !!t)));
  const interventionTypes = Array.from(new Set(transcriptsArray.map(t => t.intervention_type).filter((t): t is string => !!t)));
  const participantRoles = Array.from(new Set(transcriptsArray.map(t => t.participant_role).filter((t): t is string => !!t)));

  // Fetch school comparison data
  const { data: comparison, isLoading: comparisonLoading, error: comparisonError } = useQuery({
    queryKey: ['school-comparison', school1, school2, metric],
    queryFn: () => schoolsApi.compareSchools([school1, school2], metric || undefined),
    enabled: comparisonMode === 'schools' && !!school1 && !!school2 && school1 !== school2,
  });

  // Fetch dimension comparison data
  const { data: dimensionComparison, isLoading: dimensionLoading, error: dimensionError } = useQuery({
    queryKey: ['dimension-comparison', dimension, filters],
    queryFn: () => schoolsApi.compareByDimension(dimension, {
      school_type: filters.school_type || undefined,
      intervention_type: filters.intervention_type || undefined,
      participant_role: filters.participant_role || undefined,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
    }),
    enabled: comparisonMode === 'dimension',
  });

  if (transcriptsLoading) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'School Comparison' }]} />
        <LoadingSkeleton />
      </div>
    );
  }

  if (transcriptsError) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'School Comparison' }]} />
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

  if (schools.length === 0) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[{ label: 'School Comparison' }]} />
        <div>
          <h1 className="text-3xl font-bold">School Comparison</h1>
          <p className="text-slate-600 mt-1">Compare performance metrics across schools or dimensions</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-slate-600 mb-2">No schools found</p>
              <p className="text-sm text-slate-500 mb-4">
                Upload audio files or transcripts with school metadata to compare schools
              </p>
              <Button onClick={() => navigate('/upload-audio')}>
                Upload Audio/Transcript
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const selectedSchool1 = schools.find(s => s.id === school1);
  const selectedSchool2 = schools.find(s => s.id === school2);

  // Prepare radar chart data - handle both school IDs and names
  const radarData = comparison?.comparisons ? (() => {
    // Backend returns comparisons keyed by school name/ID
    // Try both school1/school2 as keys, and also try to find by matching
    const school1Name = selectedSchool1?.name || school1;
    const school2Name = selectedSchool2?.name || school2;
    
    const school1Data = comparison.comparisons[school1] || 
                        comparison.comparisons[school1Name] || 
                        Object.values(comparison.comparisons)[0] || {};
    const school2Data = comparison.comparisons[school2] || 
                        comparison.comparisons[school2Name] || 
                        Object.values(comparison.comparisons)[1] || {};
    
    const metrics = [
      { key: 'collaboration_score', label: 'Collaboration' },
      { key: 'mindset_shift_score', label: 'Mindset Shift' },
      { key: 'teacher_confidence_score', label: 'Teacher Confidence' },
      { key: 'municipality_cooperation_score', label: 'Municipality Cooperation' },
      { key: 'cooperation_municipality_score', label: 'Municipality Cooperation' }, // Alternative name
      { key: 'sentiment_score', label: 'Sentiment' },
      { key: 'sentiment', label: 'Sentiment' }, // Alternative name
    ];

    return metrics.map(({ key, label }) => {
      const school1Value = Number(school1Data[key] ?? school1Data[label] ?? 0);
      const school2Value = Number(school2Data[key] ?? school2Data[label] ?? 0);
      return {
        metric: label,
        school1: school1Value,
        school2: school2Value,
      };
    }).filter(item => item.school1 > 0 || item.school2 > 0); // Only include metrics with data
  })() : [];

  // Prepare dimension comparison chart data with proper numeric conversions
  const dimensionChartData = dimensionComparison?.groups ? Object.entries(dimensionComparison.groups).map(([key, value]: [string, any]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    collaboration: Number(value?.avg_collaboration_score ?? value?.avg_collaboration ?? 0),
    mindset: Number(value?.avg_mindset_shift_score ?? value?.avg_mindset_shift ?? 0),
    confidence: Number(value?.avg_teacher_confidence_score ?? value?.avg_confidence ?? value?.avg_teacher_confidence ?? 0),
    municipality: Number(
      value?.avg_municipality_cooperation_score ?? 
      value?.avg_cooperation_municipality_score ?? 
      value?.avg_municipality_cooperation ?? 
      0
    ),
    sentiment: Number(value?.avg_sentiment_score ?? value?.avg_sentiment ?? 50),
    count: Number(value?.count ?? 0),
  })).filter(item => item.count > 0 || item.collaboration > 0 || item.mindset > 0) : [];

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'School Comparison' }]} />
      
      <div>
        <h1 className="text-3xl font-bold">School Comparison</h1>
        <p className="text-slate-600 mt-1">Compare performance metrics across schools or dimensions</p>
      </div>

      {/* Mode Selection */}
      <Tabs value={comparisonMode} onValueChange={(v) => setComparisonMode(v as 'schools' | 'dimension')}>
        <TabsList>
          <TabsTrigger value="schools">
            <School className="w-4 h-4 mr-2" />
            Compare Schools
          </TabsTrigger>
          <TabsTrigger value="dimension">
            <BarChart3 className="w-4 h-4 mr-2" />
            Compare by Dimension
          </TabsTrigger>
        </TabsList>

        {/* School Comparison Tab */}
        <TabsContent value="schools" className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <Label className="text-sm mb-2 block">School A</Label>
                  <Select value={school1} onValueChange={setSchool1}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select school" />
                    </SelectTrigger>
                    <SelectContent>
                      {schools.map((school) => (
                        <SelectItem key={school.id} value={school.id}>
                          {school.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm mb-2 block">School B</Label>
                  <Select value={school2} onValueChange={setSchool2}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select school" />
                    </SelectTrigger>
                    <SelectContent>
                      {schools.map((school) => (
                        <SelectItem key={school.id} value={school.id}>
                          {school.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm mb-2 block">Metric (Optional)</Label>
                  <Select value={metric || "all"} onValueChange={(value) => setMetric(value === "all" ? "" : value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="All metrics" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Metrics</SelectItem>
                      <SelectItem value="collaboration_score">Collaboration</SelectItem>
                      <SelectItem value="mindset_shift_score">Mindset Shift</SelectItem>
                      <SelectItem value="teacher_confidence_score">Teacher Confidence</SelectItem>
                      <SelectItem value="municipality_cooperation_score">Municipality Cooperation</SelectItem>
                      <SelectItem value="sentiment_score">Sentiment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {comparisonError && (
            <ErrorBanner error={comparisonError} />
          )}

          {!school1 || !school2 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  Please select two schools to compare
                </div>
              </CardContent>
            </Card>
          ) : comparisonLoading ? (
            <LoadingSkeleton />
          ) : comparison && comparison.comparisons ? (
            <>
              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {Object.entries({
                  collaboration_score: 'Collaboration',
                  mindset_shift_score: 'Mindset Shift',
                  teacher_confidence_score: 'Teacher Confidence',
                  municipality_cooperation_score: 'Municipality Cooperation',
                  sentiment_score: 'Sentiment',
                }).map(([key, label]) => {
                  const school1Name = selectedSchool1?.name || school1;
                  const school2Name = selectedSchool2?.name || school2;
                  const school1Data = comparison.comparisons[school1] || comparison.comparisons[school1Name] || {};
                  const school2Data = comparison.comparisons[school2] || comparison.comparisons[school2Name] || {};
                  
                  // Handle alternative field names
                  const school1Value = Number(
                    school1Data[key] || 
                    school1Data[key.replace('_score', '')] || 
                    school1Data[key.replace('municipality_cooperation_score', 'cooperation_municipality_score')] || 
                    0
                  );
                  const school2Value = Number(
                    school2Data[key] || 
                    school2Data[key.replace('_score', '')] || 
                    school2Data[key.replace('municipality_cooperation_score', 'cooperation_municipality_score')] || 
                    0
                  );
                  const diff = school1Value - school2Value;

                  return (
                    <Card key={key}>
                      <CardContent className="pt-6">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="text-center">
                            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                              <span className="text-blue-600 text-sm">A</span>
                            </div>
                            <p className="text-xs text-slate-600 mb-1">{label}</p>
                            <p className="text-xl font-bold">{Math.round(school1Value)}</p>
                          </div>
                          <div className="text-center">
                            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                              <span className="text-purple-600 text-sm">B</span>
                            </div>
                            <p className="text-xs text-slate-600 mb-1">{label}</p>
                            <p className="text-xl font-bold">{Math.round(school2Value)}</p>
                          </div>
                        </div>
                        <div className="mt-3 pt-3 border-t border-slate-200 text-center">
                          {diff > 0 ? (
                            <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              A +{Math.round(diff)}
                            </Badge>
                          ) : diff < 0 ? (
                            <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              B +{Math.round(Math.abs(diff))}
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              <Minus className="w-3 h-3 mr-1" />
                              Equal
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              {/* Radar Chart */}
              {radarData.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Cultural Metrics Comparison</CardTitle>
                    <p className="text-sm text-slate-600">Multi-dimensional performance analysis</p>
                  </CardHeader>
                  <CardContent>
                    <div style={{ width: '100%', height: '400px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="#e2e8f0" />
                          <PolarAngleAxis dataKey="metric" />
                          <PolarRadiusAxis angle={90} domain={[0, 100]} />
                          <Radar 
                            name={selectedSchool1?.name || 'School A'}
                            dataKey="school1" 
                            stroke="#3b82f6" 
                            fill="#3b82f6" 
                            fillOpacity={0.3}
                            strokeWidth={2}
                          />
                          <Radar 
                            name={selectedSchool2?.name || 'School B'}
                            dataKey="school2" 
                            stroke="#8b5cf6" 
                            fill="#8b5cf6" 
                            fillOpacity={0.3}
                            strokeWidth={2}
                          />
                          <Legend />
                          <Tooltip />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Detailed Comparison Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Metrics Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-3 px-4">Metric</th>
                          <th className="text-center py-3 px-4">{selectedSchool1?.name || 'School A'}</th>
                          <th className="text-center py-3 px-4">{selectedSchool2?.name || 'School B'}</th>
                          <th className="text-center py-3 px-4">Difference</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries({
                          collaboration_score: 'Collaboration Score',
                          mindset_shift_score: 'Mindset Shift Score',
                          teacher_confidence_score: 'Teacher Confidence',
                          municipality_cooperation_score: 'Municipality Cooperation',
                          sentiment_score: 'Sentiment Score',
                        }).map(([key, label]) => {
                          const school1Value = comparison.comparisons[school1]?.[key] || 0;
                          const school2Value = comparison.comparisons[school2]?.[key] || 0;
                          const diff = school1Value - school2Value;

                          return (
                            <tr key={key} className="border-b border-slate-100">
                              <td className="py-3 px-4">{label}</td>
                              <td className="text-center py-3 px-4">{Math.round(school1Value)}</td>
                              <td className="text-center py-3 px-4">{Math.round(school2Value)}</td>
                              <td className="text-center py-3 px-4">
                                {diff > 0 ? (
                                  <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                                    A +{Math.round(diff)}
                                  </Badge>
                                ) : diff < 0 ? (
                                  <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                                    B +{Math.round(Math.abs(diff))}
                                  </Badge>
                                ) : (
                                  <Badge variant="outline">Equal</Badge>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  No comparison data available for the selected schools
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Dimension Comparison Tab */}
        <TabsContent value="dimension" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Dimension Comparison Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-sm mb-2 block">Compare By</Label>
                <Select value={dimension} onValueChange={(v) => setDimension(v as typeof dimension)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="school_type">School Type</SelectItem>
                    <SelectItem value="intervention_type">Intervention Type</SelectItem>
                    <SelectItem value="participant_role">Participant Role</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <Label className="text-sm mb-2 block">School Type Filter</Label>
                  <Select 
                    value={filters.school_type || "all"} 
                    onValueChange={(v) => setFilters({ ...filters, school_type: v === "all" ? "" : v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {schoolTypes.map(type => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm mb-2 block">Intervention Filter</Label>
                  <Select 
                    value={filters.intervention_type || "all"} 
                    onValueChange={(v) => setFilters({ ...filters, intervention_type: v === "all" ? "" : v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All interventions" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Interventions</SelectItem>
                      {interventionTypes.map(type => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm mb-2 block">Participant Role Filter</Label>
                  <Select 
                    value={filters.participant_role || "all"} 
                    onValueChange={(v) => setFilters({ ...filters, participant_role: v === "all" ? "" : v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All roles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Roles</SelectItem>
                      {participantRoles.map(role => (
                        <SelectItem key={role} value={role}>{role}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-sm mb-2 block">Date Range</Label>
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      type="date"
                      value={filters.date_from}
                      onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                      placeholder="From"
                    />
                    <Input
                      type="date"
                      value={filters.date_to}
                      onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                      placeholder="To"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {dimensionError && (
            <ErrorBanner error={dimensionError} />
          )}

          {dimensionLoading ? (
            <LoadingSkeleton />
          ) : dimensionChartData.length > 0 ? (
            <>
              {/* Dimension Comparison Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Comparison by {dimension.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</CardTitle>
                  <p className="text-sm text-slate-600">Average scores grouped by {dimension}</p>
                </CardHeader>
                <CardContent>
                  <div style={{ width: '100%', height: '400px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={dimensionChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="name" stroke="#64748b" />
                        <YAxis domain={[0, 100]} stroke="#64748b" />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px'
                          }}
                        />
                        <Legend />
                        <Bar dataKey="collaboration" fill="#3b82f6" name="Collaboration" />
                        <Bar dataKey="mindset" fill="#8b5cf6" name="Mindset Shift" />
                        <Bar dataKey="confidence" fill="#10b981" name="Teacher Confidence" />
                        <Bar dataKey="municipality" fill="#f59e0b" name="Municipality Cooperation" />
                        <Bar dataKey="sentiment" fill="#ef4444" name="Sentiment" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Dimension Comparison Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left py-3 px-4">{dimension.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>
                          <th className="text-center py-3 px-4">Count</th>
                          <th className="text-center py-3 px-4">Collaboration</th>
                          <th className="text-center py-3 px-4">Mindset</th>
                          <th className="text-center py-3 px-4">Confidence</th>
                          <th className="text-center py-3 px-4">Municipality</th>
                          <th className="text-center py-3 px-4">Sentiment</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dimensionChartData.map((row, idx) => (
                          <tr key={idx} className="border-b border-slate-100">
                            <td className="py-3 px-4 font-medium">{row.name}</td>
                            <td className="text-center py-3 px-4">{row.count}</td>
                            <td className="text-center py-3 px-4">{Math.round(row.collaboration)}</td>
                            <td className="text-center py-3 px-4">{Math.round(row.mindset)}</td>
                            <td className="text-center py-3 px-4">{Math.round(row.confidence)}</td>
                            <td className="text-center py-3 px-4">{Math.round(row.municipality)}</td>
                            <td className="text-center py-3 px-4">{Math.round(row.sentiment)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  No data available for the selected dimension and filters
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
