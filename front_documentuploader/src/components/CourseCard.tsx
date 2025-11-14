import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Clock, Users, Star } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface CourseCardProps {
  id: string;
  title: string;
  instructor: string;
  image: string;
  category: string;
  duration: string;
  students: number;
  rating: number;
  price: string;
  progress?: number;
  enrolled?: boolean;
}

export function CourseCard({
  title,
  instructor,
  image,
  category,
  duration,
  students,
  rating,
  price,
  progress,
  enrolled = false,
}: CourseCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <CardHeader className="p-0">
        <div className="relative h-48 overflow-hidden">
          <ImageWithFallback
            src={image}
            alt={title}
            className="w-full h-full object-cover"
          />
          <Badge className="absolute top-3 left-3">{category}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-5">
        <h3 className="mb-2">{title}</h3>
        <p className="text-gray-600 mb-4">by {instructor}</p>
        
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{duration}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            <span>{students.toLocaleString()}</span>
          </div>
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            <span>{rating}</span>
          </div>
        </div>

        {enrolled && progress !== undefined && (
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Progress</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}
      </CardContent>
      <CardFooter className="p-5 pt-0 flex justify-between items-center">
        <span className="text-blue-600">{price}</span>
        <Button variant={enrolled ? "outline" : "default"}>
          {enrolled ? "Continue Learning" : "Enroll Now"}
        </Button>
      </CardFooter>
    </Card>
  );
}
