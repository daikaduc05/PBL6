"use client";

import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";

export default function Home() {
  const [users, setUsers] = useState(0);
  const [lessons, setLessons] = useState(0);
  const [quizzes, setQuizzes] = useState(0);

  const API_URL = "http://localhost:5000";

  useEffect(() => {
    fetchDashboardData();
  }, []);

  async function fetchDashboardData() {
    try {
      // Get Users
      const usersResponse = await fetch(`${API_URL}/api/users`);
      const usersData = await usersResponse.json();

      if (usersData.success) {
        setUsers(usersData.users?.length || 0);
      }

      // Get Lessons
      const lessonsResponse = await fetch(`${API_URL}/api/lessons`);
      const lessonsData = await lessonsResponse.json();

      if (lessonsData.success) {
        setLessons(lessonsData.lessons?.length || 0);
      }

      // Get Quizzes
      const quizzesResponse = await fetch(`${API_URL}/api/quizzes`);
      const quizzesData = await quizzesResponse.json();

      if (quizzesData.success) {
        setQuizzes(quizzesData.quizzes?.length || 0);
      }
    } catch (error) {
      console.error("Dashboard API error:", error);
    }
  }

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      {/* Main Content */}
      <div className="ml-64">
        {/* Header */}
        <header className="border-b bg-white px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                PBL6 Admin Console
              </h1>

              <p className="text-sm text-gray-500">
                Learning Management System
              </p>
            </div>

            <div className="rounded-full bg-blue-100 px-4 py-2 text-sm font-medium text-blue-700">
              NINTHANON
            </div>
          </div>
        </header>

        {/* Dashboard */}
        <section className="p-8">
          <h2 className="mb-6 text-xl font-semibold text-gray-900">
            Dashboard
          </h2>

          <div className="grid gap-6 md:grid-cols-3">

            {/* Users */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">
                Users
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {users}
              </p>

              <p className="mt-2 text-sm text-gray-500">
                Total registered users
              </p>
            </div>

            {/* Lessons */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">
                Lessons
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {lessons}
              </p>

              <p className="mt-2 text-sm text-gray-500">
                Available lessons
              </p>
            </div>

            {/* Quizzes */}
            <div className="rounded-xl bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">
                Quizzes
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {quizzes}
              </p>

              <p className="mt-2 text-sm text-gray-500">
                Available quizzes
              </p>
            </div>

          </div>

          {/* Quick Actions */}
          <div className="mt-8 rounded-xl bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">
              Quick Actions
            </h3>

            <div className="mt-4 flex flex-wrap gap-3">

              <button
                onClick={() => {
                  window.location.href = "/users";
                }}
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                Manage Users
              </button>

              <button
                onClick={() => {
                  window.location.href = "/lessons";
                }}
                className="rounded-lg bg-gray-200 px-5 py-3 font-medium text-gray-800 hover:bg-gray-300"
              >
                Manage Lessons
              </button>

              <button
                onClick={() => {
                  window.location.href = "/quizzes";
                }}
                className="rounded-lg bg-gray-200 px-5 py-3 font-medium text-gray-800 hover:bg-gray-300"
              >
                Manage Quizzes
              </button>

            </div>
          </div>
        </section>
      </div>
    </main>
  );
}