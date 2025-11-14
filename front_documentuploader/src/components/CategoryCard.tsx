import { Card, CardContent } from "./ui/card";
import { LucideIcon } from "lucide-react";

interface CategoryCardProps {
  icon: LucideIcon;
  title: string;
  coursesCount: number;
  color: string;
}

export function CategoryCard({
  icon: Icon,
  title,
  coursesCount,
  color,
}: CategoryCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div
            className="p-3 rounded-lg"
            style={{ backgroundColor: `${color}20` }}
          >
            <Icon className="w-6 h-6" style={{ color }} />
          </div>
          <div>
            <h3 className="mb-1">{title}</h3>
            <p className="text-gray-600">{coursesCount} Courses</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
