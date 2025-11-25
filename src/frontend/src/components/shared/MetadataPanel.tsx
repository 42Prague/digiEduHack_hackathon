import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { FileText, MapPin, School, Calendar, Users, Target } from 'lucide-react';

interface MetadataPanelProps {
  metadata: {
    school_id?: string;
    region_id?: string;
    school_type?: string;
    intervention_type?: string;
    participant_role?: string;
    interview_date?: string;
  };
}

export function MetadataPanel({ metadata }: MetadataPanelProps) {
  const items = [
    { icon: School, label: 'School ID', value: metadata.school_id },
    { icon: MapPin, label: 'Region', value: metadata.region_id },
    { icon: FileText, label: 'School Type', value: metadata.school_type },
    { icon: Target, label: 'Intervention', value: metadata.intervention_type },
    { icon: Users, label: 'Role', value: metadata.participant_role },
    { icon: Calendar, label: 'Date', value: metadata.interview_date },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Metadata</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item, index) => {
            const Icon = item.icon;
            return (
              <div key={index} className="flex items-center gap-3">
                <Icon className="w-4 h-4 text-slate-500" />
                <span className="text-sm text-slate-600 w-32">{item.label}:</span>
                <span className="text-sm font-medium">
                  {item.value || 'N/A'}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

