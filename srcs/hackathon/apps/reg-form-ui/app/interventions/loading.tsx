import SkeletonCard from "./skeletonCard";
import { SkeletonLoginCard } from "./skeletonLoginCard";
import React from "react";

export default function loading() {
  return (
    <main className="min-h-screen p-8 ">
      <div>
        <h1 className="text-3xl font-bold mb-8 text-center">
          Lazy form. Test our API.
        </h1>
        <div className="flex flex-col items-center justify-center mb-8">
          <SkeletonLoginCard />
        </div>
      </div>
      <div>
        <h1>Submitted users</h1>
        <div className="grid grid-cols-3 gap-8">
          {"123".split("").map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    </main>
  );
}
