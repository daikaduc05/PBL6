export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-svh items-center justify-center bg-surface px-4 py-12">
      <div className="w-full max-w-sm">{children}</div>
    </main>
  );
}
