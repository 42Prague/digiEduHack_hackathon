import { AdminNavbar } from "./_components/AdminNavbar";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <AdminNavbar />
      <main className="ml-72 flex-1 p-8">
        {children}
      </main>
    </div>
  );
}

