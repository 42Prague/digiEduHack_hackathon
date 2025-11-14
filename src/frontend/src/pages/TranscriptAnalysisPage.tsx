import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { transcriptsApi } from '../api/endpoints';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { CulturalScoreChart } from '../components/shared/CulturalScoreChart';
import { MetadataPanel } from '../components/shared/MetadataPanel';
import { ScoreBadge } from '../components/shared/ScoreBadge';
import { ThemeChip } from '../components/shared/ThemeChip';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { 
  ArrowLeft,
  FileText,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  MessageSquare
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export function TranscriptAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: transcript, isLoading, error } = useQuery({
    queryKey: ['transcript', id],
    queryFn: () => transcriptsApi.getTranscript(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !transcript) {
    return (
      <div className="space-y-6">
        <ErrorBanner error={error || 'Transcript not found'} />
        <Button variant="outline" onClick={() => navigate('/upload-audio')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Upload
        </Button>
      </div>
    );
  }

  const culturalAnalysis = transcript.cultural_analysis;
  const dqReport = transcript.dq_report;

  // Prepare chart data with proper numeric conversions and fallbacks
  const culturalScoresData = culturalAnalysis ? [
    { 
      metric: 'Mindset Shift', 
      score: Number(culturalAnalysis.mindset_shift_score ?? culturalAnalysis.mindset_shift ?? 0) 
    },
    { 
      metric: 'Collaboration', 
      score: Number(culturalAnalysis.collaboration_score ?? culturalAnalysis.collaboration ?? 0) 
    },
    { 
      metric: 'Teacher Confidence', 
      score: Number(culturalAnalysis.teacher_confidence_score ?? culturalAnalysis.teacher_confidence ?? 0) 
    },
    { 
      metric: 'Municipality Cooperation', 
      score: Number(
        culturalAnalysis.municipality_cooperation_score ?? 
        culturalAnalysis.cooperation_municipality_score ?? 
        culturalAnalysis.municipality_cooperation ?? 
        0
      ) 
    },
    { 
      metric: 'Sentiment', 
      score: Number(culturalAnalysis.sentiment_score ?? culturalAnalysis.sentiment ?? 50) 
    },
  ].filter(item => item.score > 0) : []; // Only include metrics with data

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[
        { label: 'Transcripts', href: '/upload-audio' },
        { label: transcript.metadata?.school_id || 'Transcript Analysis' }
      ]} />
      
      <div className="flex items-center justify-between">
        <div>
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="text-3xl font-bold mt-2">Transcript Analysis</h1>
          <p className="text-slate-600 mt-1">{transcript.metadata?.original_filename || 'Transcript'}</p>
        </div>
        {dqReport && (
          <Badge className={
            dqReport.dq_score >= 80 
              ? 'bg-green-100 text-green-700 hover:bg-green-100'
              : dqReport.dq_score >= 60
              ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
              : 'bg-red-100 text-red-700 hover:bg-red-100'
          }>
            DQ Score: {dqReport.dq_score}
          </Badge>
        )}
      </div>

      {/* Metadata Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <p className="text-xs text-slate-600 mb-1">School ID</p>
              <p className="text-sm font-medium">{transcript.metadata?.school_id || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 mb-1">Region</p>
              <p className="text-sm font-medium">{transcript.metadata?.region_id || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 mb-1">School Type</p>
              <p className="text-sm font-medium">{transcript.metadata?.school_type || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 mb-1">Intervention</p>
              <p className="text-sm font-medium">{transcript.metadata?.intervention_type || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 mb-1">Participant Role</p>
              <p className="text-sm font-medium">{transcript.metadata?.participant_role || 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-600 mb-1">Interview Date</p>
              <p className="text-sm font-medium">
                {transcript.metadata?.interview_date 
                  ? new Date(transcript.metadata.interview_date).toLocaleDateString()
                  : 'N/A'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="transcript" className="space-y-6">
        <TabsList>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="cultural">Cultural Analysis</TabsTrigger>
          <TabsTrigger value="quality">Data Quality</TabsTrigger>
        </TabsList>

        {/* Transcript Tab */}
        <TabsContent value="transcript" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Original Transcript
                </CardTitle>
                <p className="text-sm text-slate-600">Raw transcription</p>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <p className="text-sm whitespace-pre-wrap">
                    {transcript.transcript_text || 'No transcript text available'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-blue-600" />
                  Cleaned Transcript
                </CardTitle>
                <p className="text-sm text-slate-600">Processed and normalized</p>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <p className="text-sm whitespace-pre-wrap">
                    {transcript.clean_text || transcript.transcript_text || 'No cleaned text available'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Cultural Analysis Tab */}
        <TabsContent value="cultural" className="space-y-6">
          {culturalAnalysis ? (
            <>
              {/* Cultural Scores Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CulturalScoreChart scores={{
                  mindset_shift_score: culturalAnalysis.mindset_shift_score,
                  collaboration_score: culturalAnalysis.collaboration_score,
                  teacher_confidence_score: culturalAnalysis.teacher_confidence_score,
                  municipality_cooperation_score: culturalAnalysis.municipality_cooperation_score,
                  sentiment_score: culturalAnalysis.sentiment_score,
                }} />
                
                {/* Sentiment Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle>Sentiment Score</CardTitle>
                    <p className="text-sm text-slate-600">Overall sentiment analysis</p>
                  </CardHeader>
                  <CardContent>
                    {(() => {
                      const sentimentValue = Number(culturalAnalysis.sentiment_score ?? culturalAnalysis.sentiment ?? 50);
                      return sentimentValue > 0 ? (
                        <div style={{ width: '100%', height: '300px' }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={[{ name: 'Sentiment', value: sentimentValue }]}>
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
                            <Bar 
                              dataKey="value" 
                              fill={sentimentValue >= 70 ? '#10b981' : sentimentValue >= 50 ? '#f59e0b' : '#ef4444'}
                              radius={[8, 8, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div className="h-[300px] flex items-center justify-center text-slate-500">
                        No sentiment data available
                      </div>
                    );
                    })()}
                    <div className="mt-4 text-center">
                      {(() => {
                        const sentimentValue = Number(culturalAnalysis.sentiment_score ?? culturalAnalysis.sentiment ?? 50);
                        return (
                          <>
                            <p className="text-3xl font-bold">{sentimentValue}</p>
                            <Badge className={`mt-2 ${
                              sentimentValue >= 70 
                                ? 'bg-green-100 text-green-700 hover:bg-green-100'
                                : sentimentValue >= 50
                                ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                                : 'bg-red-100 text-red-700 hover:bg-red-100'
                            }`}>
                              {sentimentValue >= 70 ? 'Positive' : 
                               sentimentValue >= 50 ? 'Neutral' : 'Negative'}
                            </Badge>
                          </>
                        );
                      })()}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-slate-600 mb-2">Mindset Shift</p>
                      <p className="text-3xl font-bold">{culturalAnalysis.mindset_shift_score}</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-slate-600 mb-2">Collaboration</p>
                      <p className="text-3xl font-bold">{culturalAnalysis.collaboration_score}</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-slate-600 mb-2">Teacher Confidence</p>
                      <p className="text-3xl font-bold">{culturalAnalysis.teacher_confidence_score}</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-slate-600 mb-2">Municipality Cooperation</p>
                      <p className="text-3xl font-bold">{culturalAnalysis.municipality_cooperation_score}</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <p className="text-sm text-slate-600 mb-2">Sentiment</p>
                      <p className="text-3xl font-bold">{culturalAnalysis.sentiment_score}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Themes */}
              {culturalAnalysis.themes && culturalAnalysis.themes.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Extracted Themes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {culturalAnalysis.themes.map((theme, idx) => (
                        <ThemeChip key={idx} theme={theme} />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Insights */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5" />
                      Practical Change
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{culturalAnalysis.practical_change || 'N/A'}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      Mindset Change
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{culturalAnalysis.mindset_change || 'N/A'}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Impact Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Impact Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm whitespace-pre-wrap">
                    {culturalAnalysis.impact_summary || 'No impact summary available'}
                  </p>
                  {culturalAnalysis.culture_change_detected && (
                    <Badge className="mt-4 bg-green-100 text-green-700 hover:bg-green-100">
                      Culture Change Detected
                    </Badge>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  No cultural analysis available for this transcript.
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Data Quality Tab */}
        <TabsContent value="quality" className="space-y-6">
          {dqReport ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Data Quality Report</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-600">DQ Score</p>
                      <p className="text-3xl font-bold">{dqReport.dq_score}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Total Rows</p>
                      <p className="text-3xl font-bold">{dqReport.total_rows}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Valid Rows</p>
                      <p className="text-3xl font-bold text-green-600">{dqReport.valid_rows}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Invalid Rows</p>
                      <p className="text-3xl font-bold text-red-600">{dqReport.invalid_rows}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* PII Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>PII Detection & Masking</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-slate-600">Emails</p>
                      <p className="text-2xl font-bold">{dqReport.pii_found_and_masked.emails}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Phone Numbers</p>
                      <p className="text-2xl font-bold">{dqReport.pii_found_and_masked.phones}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Names</p>
                      <p className="text-2xl font-bold">{dqReport.pii_found_and_masked.names}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Schema Issues */}
              {dqReport.schema_issues && dqReport.schema_issues.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Schema Issues</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {dqReport.schema_issues.map((issue, idx) => (
                        <div key={idx} className="p-3 bg-yellow-50 rounded border border-yellow-200">
                          <p className="text-sm font-medium">{issue.column}</p>
                          <p className="text-sm text-slate-600">{issue.issue}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Missing Values Chart */}
              {Object.keys(dqReport.missing_values).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Missing Values</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div style={{ width: '100%', height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(dqReport.missing_values).map(([key, value]) => ({
                          field: key,
                          count: value,
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="field" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#ef4444" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  No data quality report available for this transcript.
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

