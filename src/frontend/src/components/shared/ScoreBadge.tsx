import { Badge } from '../ui/badge';

interface ScoreBadgeProps {
  label: string;
  score: number | null;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function ScoreBadge({ label, score, variant = 'default' }: ScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-600">{label}:</span>
        <Badge variant="outline">N/A</Badge>
      </div>
    );
  }

  const getVariant = () => {
    if (variant !== 'default') return variant;
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'danger';
  };

  const colorMap = {
    success: 'bg-green-100 text-green-700 hover:bg-green-100',
    warning: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-100',
    danger: 'bg-red-100 text-red-700 hover:bg-red-100',
    default: 'bg-blue-100 text-blue-700 hover:bg-blue-100',
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-600">{label}:</span>
      <Badge className={colorMap[getVariant()]}>{score}</Badge>
    </div>
  );
}

