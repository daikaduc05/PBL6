"use client";

import Link from "next/link";

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-gray-900 p-6 text-white">
      {/* Logo */}
      <div className="mb-8">
        <h1 className="text-xl font-bold">PBL6</h1>
        <p className="text-sm text-gray-400">Admin Console</p>
      </div>

      {/* Navigation */}
      <nav className="space-y-2">
        <Link
          href="/"
          className="block rounded-lg bg-blue-600 px-4 py-3 font-medium hover:bg-blue-700"
        >
          Dashboard
        </Link>

        <Link
          href="/users"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Users
        </Link>

        <Link
          href="/categories"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Categories
        </Link>

        <Link
          href="/lessons"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Lessons
        </Link>

        <Link
          href="/quizzes"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Quizzes
        </Link>

        {/* New menu: Questions */}
        <Link
          href="/questions"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Questions
        </Link>

        {/* New menu: Options */}
        <Link
          href="/options"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Options
        </Link>

        <Link
          href="/transactions"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Transactions
        </Link>

        <Link
          href="/notifications"
          className="block rounded-lg px-4 py-3 hover:bg-gray-800"
        >
          Notifications
        </Link>
      </nav>

      {/* Footer */}
      <div className="absolute bottom-6 left-6">
        <p className="text-xs text-gray-500">Frontend</p>
        <p className="text-sm font-medium text-gray-300">NINTHANON</p>
      </div>
    </aside>
  );
}