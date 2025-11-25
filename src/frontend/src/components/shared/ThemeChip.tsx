import { Badge } from '../ui/badge';

interface ThemeChipProps {
  theme: string;
  count?: number;
}

export function ThemeChip({ theme, count }: ThemeChipProps) {
  return (
    <Badge variant="outline" className="mr-2 mb-2">
      {theme}
      {count !== undefined && (
        <span className="ml-1 text-slate-500">({count})</span>
      )}
    </Badge>
  );
}

