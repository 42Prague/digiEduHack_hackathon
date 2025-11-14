import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface CulturalScoreChartProps {
  scores: {
    mindset_shift_score: number | null;
    collaboration_score: number | null;
    teacher_confidence_score: number | null;
    municipality_cooperation_score: number | null;
    sentiment_score: number | null;
  };
}

export function CulturalScoreChart({ scores }: CulturalScoreChartProps) {
  const data = [
    {
      metric: 'Mindset Shift',
      score: scores.mindset_shift_score ?? 0,
      fullMark: 100,
    },
    {
      metric: 'Collaboration',
      score: scores.collaboration_score ?? 0,
      fullMark: 100,
    },
    {
      metric: 'Teacher Confidence',
      score: scores.teacher_confidence_score ?? 0,
      fullMark: 100,
    },
    {
      metric: 'Municipality Cooperation',
      score: scores.municipality_cooperation_score ?? 0,
      fullMark: 100,
    },
    {
      metric: 'Sentiment',
      score: scores.sentiment_score ?? 0,
      fullMark: 100,
    },
  ];

  // Check if all scores are null/zero
  const hasData = data.some(d => d.score > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cultural Analysis Scores</CardTitle>
      </CardHeader>
      <CardContent>
        {hasData ? (
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={data}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Scores"
                  dataKey="score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-slate-500">
            No cultural analysis data available
          </div>
        )}
      </CardContent>
    </Card>
  );
}

