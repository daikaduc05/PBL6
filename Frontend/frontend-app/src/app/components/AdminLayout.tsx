import type { ReactNode } from "react";
import Sidebar from "./Sidebar";

type AdminLayoutProps = {
  title: string;
  description?: string;
  children: ReactNode;
};

export default function AdminLayout({
  title,
  description,
  children,
}: AdminLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />

      <div className="ml-64 min-h-screen">
        <header className="border-b border-gray-200 bg-white px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {title}
          </h1>

          {description && (
            <p className="mt-1 text-sm text-gray-500">
              {description}
            </p>
          )}
        </header>

        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
}