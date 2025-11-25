import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { analyticsApi, transcriptsApi } from '../api/endpoints';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { 
  Lightbulb, 
  TrendingUp,
  Users,
  BookOpen,
  Target,
  Zap,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Award,
  School
} from 'lucide-react';

export function RecommendationsPage() {
  const navigate = useNavigate();
  const [schoolId, setSchoolId] = useState<string>('');
  const [regionId, setRegionId] = useState<string>('');

  // Fetch transcripts to get school/region lists
  const { data: transcripts, isLoading: transcriptsLoading, error: transcriptsError } = useQuery({
    queryKey: ['transcripts'],
    queryFn: async () => {
      try {
        const result = await transcriptsApi.listTranscripts();
        console.log('📊 Transcripts fetched:', result);
        return result;
      } catch (error) {
        console.error('❌ Error fetching transcripts:', error);
        throw error;
      }
    },
  });

  // Get unique schools and regions
  const transcriptsArray = Array.isArray(transcripts) ? transcripts : [];
  const schools = Array.from(
    new Set(
      transcriptsArray.map(t => t.school_id).filter((id): id is string => id !== null && id !== undefined)
    )
  );

  const regions = Array.from(
    new Set(
      transcriptsArray.map(t => t.region_id).filter((id): id is string => id !== null && id !== undefined)
    )
  );

  console.log('🏫 Schools:', schools);
  console.log('📍 Regions:', regions);

  // Fetch recommendations - only when school or region is selected
  const { data: recommendations, isLoading: recommendationsLoading, error: recommendationsError } = useQuery({
    queryKey: ['recommendations', schoolId, regionId],
    queryFn: () => analyticsApi.getRecommendations({
      school_id: schoolId || undefined,
      region_id: regionId || undefined,
    }),
    enabled: !!(schoolId || regionId), // Only fetch when at least one filter is selected
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
        <Breadcrumbs items={[{ label: 'Recommendations' }]} />
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

  const schoolRecs = Array.isArray(recommendations?.school_recommendations) ? recommendations.school_recommendations : [];
  const regionRecs = Array.isArray(recommendations?.region_recommendations) ? recommendations.region_recommendations : [];
  const interventionRecs = Array.isArray(recommendations?.intervention_recommendations) ? recommendations.intervention_recommendations : [];
  const warnings = Array.isArray(recommendations?.culture_warnings) ? recommendations.culture_warnings : [];
  const strengths = Array.isArray(recommendations?.strengths) ? recommendations.strengths : [];

  const totalRecommendations = schoolRecs.length + regionRecs.length + interventionRecs.length;
  const highImpactCount = schoolRecs.filter(r => {
    if (typeof r === 'string') {
      return r.toLowerCase().includes('high') || r.toLowerCase().includes('critical');
    }
    return r.priority === 'high' || r.priority === 'critical';
  }).length;

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Recommendations' }]} />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Recommendations</h1>
          <p className="text-slate-600 mt-1">Data-driven insights and actionable strategies</p>
        </div>
        <div className="flex items-center gap-2">
          {recommendations && (
            <>
              <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                {highImpactCount} High Priority
              </Badge>
              <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                {totalRecommendations} Total
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-sm mb-2 block">School (Optional)</label>
              <Select value={schoolId || "all"} onValueChange={(value) => setSchoolId(value === "all" ? "" : value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All schools" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Schools</SelectItem>
                  {schools.map((school) => (
                    <SelectItem key={school} value={school}>
                      {school}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm mb-2 block">Region (Optional)</label>
              <Select value={regionId || "all"} onValueChange={(value) => setRegionId(value === "all" ? "" : value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All regions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Regions</SelectItem>
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

      {recommendationsError && (
        <ErrorBanner error={recommendationsError} />
      )}

      {schools.length === 0 && regions.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-slate-600 mb-2">No transcripts found</p>
              <p className="text-sm text-slate-500 mb-4">
                Upload audio files or transcripts to generate recommendations
              </p>
              <Button onClick={() => navigate('/upload-audio')}>
                Upload Audio/Transcript
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : !schoolId && !regionId ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-500">
              Please select a school or region to view recommendations
            </div>
          </CardContent>
        </Card>
      ) : recommendationsLoading ? (
        <LoadingSkeleton />
      ) : recommendations ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <Lightbulb className="w-6 h-6 text-blue-600" />
                  </div>
                  <p className="text-sm text-slate-600">Total Recommendations</p>
                  <p className="text-2xl mt-1">{totalRecommendations}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                  <p className="text-sm text-slate-600">School Recommendations</p>
                  <p className="text-2xl mt-1">{schoolRecs.length}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <Target className="w-6 h-6 text-purple-600" />
                  </div>
                  <p className="text-sm text-slate-600">Intervention Recommendations</p>
                  <p className="text-2xl mt-1">{interventionRecs.length}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                    <AlertTriangle className="w-6 h-6 text-orange-600" />
                  </div>
                  <p className="text-sm text-slate-600">Culture Warnings</p>
                  <p className="text-2xl mt-1">{warnings.length}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* School Recommendations */}
          {schoolRecs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <School className="w-5 h-5" />
                  School Recommendations
                </CardTitle>
                <p className="text-sm text-slate-600">Actionable insights for {schoolId || 'selected schools'}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {schoolRecs.map((rec, idx) => {
                    // Handle both string and object formats
                    const recText = typeof rec === 'string' ? rec : (rec.description || rec.title || String(rec));
                    const recTitle = typeof rec === 'object' && rec.title ? rec.title : null;
                    const recPriority = typeof rec === 'object' && rec.priority ? rec.priority : null;
                    return (
                      <div key={idx} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center flex-shrink-0">
                            <Lightbulb className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            {recTitle && <p className="text-sm font-semibold mb-1">{recTitle}</p>}
                            <p className="text-sm">{recText}</p>
                            {recPriority && (
                              <Badge className={`mt-2 ${
                                recPriority === 'high' ? 'bg-red-100 text-red-700' :
                                recPriority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {recPriority}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Region Recommendations */}
          {regionRecs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Region Recommendations
                </CardTitle>
                <p className="text-sm text-slate-600">Strategic recommendations for {regionId || 'selected regions'}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {regionRecs.map((rec, idx) => {
                    // Handle both string and object formats
                    const recText = typeof rec === 'string' ? rec : (rec.description || rec.title || String(rec));
                    const recTitle = typeof rec === 'object' && rec.title ? rec.title : null;
                    const recPriority = typeof rec === 'object' && rec.priority ? rec.priority : null;
                    return (
                      <div key={idx} className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-purple-600 text-white rounded-lg flex items-center justify-center flex-shrink-0">
                            <Target className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            {recTitle && <p className="text-sm font-semibold mb-1">{recTitle}</p>}
                            <p className="text-sm">{recText}</p>
                            {recPriority && (
                              <Badge className={`mt-2 ${
                                recPriority === 'high' ? 'bg-red-100 text-red-700' :
                                recPriority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-purple-100 text-purple-700'
                              }`}>
                                {recPriority}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Intervention Recommendations */}
          {interventionRecs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Intervention Recommendations
                </CardTitle>
                <p className="text-sm text-slate-600">Recommended interventions and programs</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {interventionRecs.map((rec, idx) => {
                    // Handle both string and object formats
                    const recText = typeof rec === 'string' ? rec : (rec.description || rec.title || String(rec));
                    const recTitle = typeof rec === 'object' && rec.title ? rec.title : null;
                    const recPriority = typeof rec === 'object' && rec.priority ? rec.priority : null;
                    return (
                      <div key={idx} className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-green-600 text-white rounded-lg flex items-center justify-center flex-shrink-0">
                            <Zap className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            {recTitle && <p className="text-sm font-semibold mb-1">{recTitle}</p>}
                            <p className="text-sm">{recText}</p>
                            {recPriority && (
                              <Badge className={`mt-2 ${
                                recPriority === 'high' ? 'bg-red-100 text-red-700' :
                                recPriority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-green-100 text-green-700'
                              }`}>
                                {recPriority}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Culture Warnings */}
          {warnings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  Culture Warnings
                </CardTitle>
                <p className="text-sm text-slate-600">Areas requiring immediate attention</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {warnings.map((warning, idx) => {
                    // Handle both string and object formats
                    const warningText = typeof warning === 'string' ? warning : (warning.description || warning.title || String(warning));
                    return (
                      <div key={idx} className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-orange-600 text-white rounded-lg flex items-center justify-center flex-shrink-0">
                            <AlertTriangle className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm">{warningText}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Strengths */}
          {strengths.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-green-600" />
                  Strengths
                </CardTitle>
                <p className="text-sm text-slate-600">Areas of excellence</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {strengths.map((strength, idx) => {
                    // Handle both string and object formats
                    const strengthText = typeof strength === 'string' ? strength : (strength.description || strength.title || String(strength));
                    return (
                      <div key={idx} className="p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-green-600 text-white rounded-lg flex items-center justify-center flex-shrink-0">
                            <CheckCircle2 className="w-5 h-5" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm">{strengthText}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {totalRecommendations === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-500">
                  No recommendations available for the selected criteria
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}
