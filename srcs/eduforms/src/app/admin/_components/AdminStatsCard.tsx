"use client";

import { api } from "~/trpc/react";

/**
 * Example component demonstrating how to use adminProcedure from the client
 * This component will only work if the user is an admin
 */
export function AdminStatsCard() {
  // Use the admin tRPC endpoint - this will fail if user is not an admin
  const { data: stats, isLoading, error } = api.admin.getStats.useQuery();

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Načítání statistik...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-lg shadow p-6">
        <p className="text-red-600">Chyba: {error.message}</p>
        <p className="text-sm text-red-500 mt-2">
          Pro zobrazení těchto dat musíte být administrátor.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Systémové statistiky</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 p-4 rounded">
          <p className="text-sm text-gray-600">Celkový počet uživatelů</p>
          <p className="text-2xl font-bold text-blue-600">{stats?.totalUsers ?? 0}</p>
        </div>
        <div className="bg-green-50 p-4 rounded">
          <p className="text-sm text-gray-600">Běžní uživatelé</p>
          <p className="text-2xl font-bold text-green-600">{stats?.regularUsers ?? 0}</p>
        </div>
        <div className="bg-purple-50 p-4 rounded">
          <p className="text-sm text-gray-600">Administrátoři</p>
          <p className="text-2xl font-bold text-purple-600">{stats?.adminUsers ?? 0}</p>
        </div>
        <div className="bg-red-50 p-4 rounded">
          <p className="text-sm text-gray-600">Blokovaní uživatelé</p>
          <p className="text-2xl font-bold text-red-600">{stats?.bannedUsers ?? 0}</p>
        </div>
      </div>
    </div>
  );
}

