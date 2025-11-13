"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";

interface Props {
  userId: number;
}

export function ViewUserButton({ userId }: Props) {
  return (
    <Button>
      <Link href={`/users/${userId}`}>Details</Link>
    </Button>
  );
}
