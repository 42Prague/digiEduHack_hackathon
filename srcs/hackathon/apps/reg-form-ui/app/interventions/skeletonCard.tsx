import React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";

function SkeletonCard() {
  return (
    <Card className="flex flex-col justify-between">
      <CardHeader className={"flex-row gap-4 items-center"}>
        <Skeleton className="h-6 flex-grow" />
        <Skeleton className="h-4 flex-grow" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 flex-grow mt-3" />
      </CardContent>
      <CardFooter className="flex justify-between">
        <Skeleton className="h-9 w-28" />
        <Skeleton className="h-9 w-28" />
      </CardFooter>
    </Card>
  );
}

export default SkeletonCard;
