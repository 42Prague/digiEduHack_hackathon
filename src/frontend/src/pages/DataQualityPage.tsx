import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ingestionApi } from '../api/endpoints';
import { LoadingSkeleton } from '../components/shared/LoadingSkeleton';
import { ErrorBanner } from '../components/shared/ErrorBanner';
import { Breadcrumbs } from '../components/shared/Breadcrumbs';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Shield,
  FileCheck,
  Database,
  Eye,
  Download
} from 'lucide-react';
import { 
  BarChart, 
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
} from 'recharts';

export function DataQualityPage() {
  const { dataset_id } = useParams<{ dataset_id: string }>();

  // Always show the page, even if dataset_id is missing (for debugging)
  if (!dataset_id) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[
          { label: 'Data Quality', href: '/upload-data' },
          { label: 'Report' }
        ]} />
        <div>
          <h1 className="text-3xl font-bold">Data Quality Report</h1>
          <p className="text-slate-600 mt-1">No dataset ID provided</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-500">
              <p className="mb-4">No dataset ID provided in the URL.</p>
              <p className="text-sm mb-4">Please navigate from a dataset upload or use a valid dataset ID.</p>
              <Button onClick={() => window.history.back()}>
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { data: dqReport, isLoading, error } = useQuery({
    queryKey: ['dq-report', dataset_id],
    queryFn: () => ingestionApi.getDQReport(dataset_id),
    enabled: !!dataset_id,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[
          { label: 'Data Quality', href: '/upload-data' },
          { label: dataset_id }
        ]} />
        <div>
          <h1 className="text-3xl font-bold">Data Quality Report</h1>
          <p className="text-slate-600 mt-1">Dataset: {dataset_id}</p>
        </div>
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !dqReport) {
    return (
      <div className="space-y-6">
        <Breadcrumbs items={[
          { label: 'Data Quality', href: '/upload-data' },
          { label: dataset_id }
        ]} />
        <div>
          <h1 className="text-3xl font-bold">Data Quality Report</h1>
          <p className="text-slate-600 mt-1">Dataset: {dataset_id}</p>
        </div>
        <ErrorBanner error={error || new Error('DQ report not found')} />
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <p className="text-slate-600 mb-4">Unable to load DQ report for dataset: {dataset_id}</p>
              <p className="text-sm text-slate-500 mb-4">
                The report may not exist yet, or there may be a backend issue.
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline" onClick={() => window.history.back()}>
                  Go Back
                </Button>
                <Button onClick={() => window.location.reload()}>
                  Retry
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare chart data with proper numeric conversions
  const missingValuesData = Object.entries(dqReport.missing_values || {}).map(([field, count]) => ({
    field,
    count: Number(count ?? 0),
  })).filter(item => item.count > 0); // Only show fields with missing values

  const schemaIssuesArray = Array.isArray(dqReport.schema_issues) ? dqReport.schema_issues : [];
  const missingValuesObj = dqReport.missing_values || {};
  const piiData = dqReport.pii_found_and_masked || {};
  
  const errorDistribution = [
    { name: 'Schema Issues', value: schemaIssuesArray.length, color: '#ef4444' },
    { name: 'Missing Values', value: Object.values(missingValuesObj).reduce((a, b) => a + b, 0), color: '#f59e0b' },
    { name: 'PII Found', value: (piiData.emails || 0) + (piiData.phones || 0) + (piiData.names || 0), color: '#eab308' },
  ].filter(item => item.value > 0);

  const totalPII = (dqReport.pii_found_and_masked?.emails || 0) + 
                   (dqReport.pii_found_and_masked?.phones || 0) + 
                   (dqReport.pii_found_and_masked?.names || 0);

  // Calculate completeness percentage with proper numeric conversions
  const totalRows = Number(dqReport.total_rows ?? 0);
  const totalMissing = Object.values(missingValuesObj).reduce((a, b) => Number(a) + Number(b ?? 0), 0);
  const completenessPercent = totalRows > 0 
    ? Math.round(((totalRows - totalMissing) / totalRows) * 100)
    : 100;

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[
        { label: 'Data Quality', href: '/upload-data' },
        { label: dataset_id || 'Report' }
      ]} />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Quality Report</h1>
          <p className="text-slate-600 mt-1">Dataset: {dataset_id}</p>
        </div>
        {dqReport.quarantined_rows_path && (
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Download Quarantined Data
          </Button>
        )}
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">DQ Score</p>
                <p className="text-3xl mt-2">{Number(dqReport.dq_score ?? 0)}</p>
                <Badge className={`mt-2 ${
                  Number(dqReport.dq_score ?? 0) >= 80 
                    ? 'bg-green-100 text-green-700 hover:bg-green-100'
                    : Number(dqReport.dq_score ?? 0) >= 60
                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    : 'bg-red-100 text-red-700 hover:bg-red-100'
                }`}>
                  {Number(dqReport.dq_score ?? 0) >= 80 ? 'Excellent' : 
                   Number(dqReport.dq_score ?? 0) >= 60 ? 'Good' : 'Needs Improvement'}
                </Badge>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <FileCheck className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Rows</p>
                <p className="text-3xl mt-2">{Number(dqReport.total_rows ?? 0).toLocaleString()}</p>
                <p className="text-xs text-green-600 mt-2">
                  {Number(dqReport.valid_rows ?? 0)} valid ({Number(dqReport.total_rows ?? 0) > 0 ? Math.round((Number(dqReport.valid_rows ?? 0) / Number(dqReport.total_rows ?? 0)) * 100) : 0}%)
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <Database className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Invalid Rows</p>
                <p className="text-3xl mt-2">{Number(dqReport.invalid_rows ?? 0)}</p>
                <p className="text-xs text-orange-600 mt-2">
                  {Number(dqReport.invalid_rows ?? 0) > 0 ? 'Requires review' : 'All valid'}
                </p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">PII Detected</p>
                <p className="text-3xl mt-2">{totalPII}</p>
                <p className="text-xs text-red-600 mt-2">All redacted</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {missingValuesData.length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Missing Values by Field</CardTitle>
              <p className="text-sm text-slate-600">Fields with missing data</p>
            </CardHeader>
            <CardContent>
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={missingValuesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="field" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="count" fill="#ef4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {errorDistribution.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Issue Distribution</CardTitle>
              <p className="text-sm text-slate-600">By type</p>
            </CardHeader>
            <CardContent>
              <div style={{ width: '100%', height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={errorDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {errorDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* PII Stats */}
      {totalPII > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>PII Detection & Masking</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-slate-600">Emails</p>
                <p className="text-2xl font-bold">{dqReport.pii_found_and_masked?.emails || 0}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Phone Numbers</p>
                <p className="text-2xl font-bold">{dqReport.pii_found_and_masked?.phones || 0}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Names</p>
                <p className="text-2xl font-bold">{dqReport.pii_found_and_masked?.names || 0}</p>
              </div>
            </div>
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <p className="text-sm text-green-700">
                  All PII has been automatically masked and redacted.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schema Issues */}
      {schemaIssuesArray.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Schema Issues</CardTitle>
            <p className="text-sm text-slate-600">Data structure problems detected</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {schemaIssuesArray.map((issue: any, idx: number) => (
                <div key={idx} className="p-3 bg-yellow-50 rounded border border-yellow-200">
                  <p className="text-sm font-medium">{issue.column || issue.field || `Issue ${idx + 1}`}</p>
                  <p className="text-sm text-slate-600">{issue.issue || issue.message || String(issue)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Normalization Fixes */}
      {Array.isArray(dqReport.normalization_fixes) && dqReport.normalization_fixes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Auto-Corrections Applied</CardTitle>
            <p className="text-sm text-slate-600">Automatic fixes during normalization</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dqReport.normalization_fixes.map((fix: any, idx: number) => (
                <div key={idx} className="p-3 bg-green-50 rounded border border-green-200">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <p className="text-sm">{typeof fix === 'string' ? fix : (fix.message || fix.description || String(fix))}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schema Issues with Column Highlighting */}
      {schemaIssuesArray.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Problematic Columns</CardTitle>
            <p className="text-sm text-slate-600">Columns with schema issues (highlighted)</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {schemaIssuesArray.map((issue: any, idx: number) => (
                <div key={idx} className="p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-yellow-900">{issue.column || issue.field || `Issue ${idx + 1}`}</p>
                    <Badge className="bg-yellow-200 text-yellow-900 hover:bg-yellow-200">
                      Issue Detected
                    </Badge>
                  </div>
                  <p className="text-sm text-yellow-800">{issue.issue || issue.message || String(issue)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quarantined Rows Viewer */}
      {dqReport.quarantined_rows_path && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              Quarantined Rows
            </CardTitle>
            <p className="text-sm text-slate-600">Rows that failed validation and were quarantined</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div>
                  <p className="text-sm font-medium">Quarantined File Available</p>
                  <p className="text-xs text-slate-600 mt-1">
                    {Number(dqReport.invalid_rows ?? 0)} row(s) have been quarantined for review
                  </p>
                </div>
                <Button variant="outline" onClick={() => {
                  // In a real app, this would download the file
                  window.open(dqReport.quarantined_rows_path, '_blank');
                }}>
                  <Download className="w-4 h-4 mr-2" />
                  View Quarantined Data
                </Button>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <p className="text-xs text-slate-600">
                  <strong>Note:</strong> Quarantined rows contain data that failed validation checks. 
                  Review and fix these rows before re-importing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Preview */}
      {dqReport.total_rows > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Data Preview</CardTitle>
            <p className="text-sm text-slate-600">Sample of processed data</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-600">Total Rows</p>
                  <p className="text-2xl font-bold">{Number(dqReport.total_rows ?? 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-700">Valid Rows</p>
                  <p className="text-2xl font-bold text-green-700">{Number(dqReport.valid_rows ?? 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg">
                  <p className="text-xs text-red-700">Invalid Rows</p>
                  <p className="text-2xl font-bold text-red-700">{Number(dqReport.invalid_rows ?? 0).toLocaleString()}</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700">Completeness</p>
                  <p className="text-2xl font-bold text-blue-700">
                    {completenessPercent}%
                  </p>
                </div>
              </div>
              
              {/* Highlight problematic columns */}
              {Object.keys(missingValuesObj).length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium mb-2">Columns with Missing Values:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(missingValuesObj)
                      .sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0))
                      .slice(0, 10)
                      .map(([field, count]) => {
                        const countNum = Number(count ?? 0);
                        const totalRowsNum = Number(dqReport.total_rows ?? 0);
                        return (
                          <Badge 
                            key={field}
                            className={`${
                              totalRowsNum > 0 && countNum > totalRowsNum * 0.1
                                ? 'bg-red-100 text-red-700 hover:bg-red-100'
                                : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                            }`}
                          >
                            {field}: {countNum} missing
                          </Badge>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">Data Completeness</span>
                <span className="font-medium">
                  {completenessPercent}%
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">Valid Rows</span>
                <span className="font-medium text-green-600">{Number(dqReport.valid_rows ?? 0)}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">Invalid Rows</span>
                <span className="font-medium text-red-600">{Number(dqReport.invalid_rows ?? 0)}</span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">Overall Quality</span>
                <Badge className={
                  Number(dqReport.dq_score ?? 0) >= 80 
                    ? 'bg-green-100 text-green-700 hover:bg-green-100'
                    : Number(dqReport.dq_score ?? 0) >= 60
                    ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                    : 'bg-red-100 text-red-700 hover:bg-red-100'
                }>
                  {Number(dqReport.dq_score ?? 0) >= 80 ? 'Excellent' : 
                   Number(dqReport.dq_score ?? 0) >= 60 ? 'Good' : 'Needs Improvement'}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">PII Safety</span>
                <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                  {totalPII > 0 ? 'Masked' : 'No PII Found'}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-sm">Schema Compliance</span>
                <Badge className={
                  schemaIssuesArray.length === 0
                    ? 'bg-green-100 text-green-700 hover:bg-green-100'
                    : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100'
                }>
                  {schemaIssuesArray.length === 0 ? 'Compliant' : 'Issues Found'}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
