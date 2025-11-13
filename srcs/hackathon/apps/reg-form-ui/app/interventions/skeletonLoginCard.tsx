import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import React from "react";

export function SkeletonLoginCard() {
  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>
          <Skeleton className="h-5 w-36" />
        </CardTitle>
        <CardDescription>
          <Skeleton className="h-4 w-40" />
        </CardDescription>
        <CardAction></CardAction>
      </CardHeader>
      <CardContent>
        <form>
          <div className="flex flex-col gap-4">
            <div className="grid gap-1">
              <Skeleton className="h-4.5 w-10" />
              <Skeleton className="h-8 flex-grow" />
            </div>
            <div className="grid gap-1">
              <Skeleton className="h-4.5 w-15" />
              <Skeleton className="h-8 flex-grow" />
            </div>
            <div className="grid gap-1">
              <Skeleton className="h-5 w-15" />
              <Skeleton className="h-8 flex-grow" />
            </div>
            <div className="grid gap-1">
              <div className="flex items-center">
                <Skeleton className="h-5 w-15" />
              </div>
              <Skeleton className="h-8 flex-grow" />
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter>
        <Skeleton className="h-8 flex-grow" />
      </CardFooter>
    </Card>
  );
}
