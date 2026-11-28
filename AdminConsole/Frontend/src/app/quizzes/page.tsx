"use client";

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

type Lesson = {
  lesson_id: number;
  title: string;
};

type Quiz = {
  quiz_id: number;
  lesson_id: number;
  lesson_title?: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
};

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [lessonId, setLessonId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("DRAFT");

  const API_URL = "http://localhost:5000";

  useEffect(() => {
    fetchQuizzes();
    fetchLessons();
  }, []);

  // Get quizzes
  async function fetchQuizzes() {
    try {
      const response = await fetch(`${API_URL}/api/quizzes`);
      const data = await response.json();

      if (data.success) {
        setQuizzes(data.quizzes || []);
      }
    } catch (error) {
      console.error("Error fetching quizzes:", error);
      alert("Cannot connect to Backend.");
    }
  }

  // Get lessons
  async function fetchLessons() {
    try {
      const response = await fetch(`${API_URL}/api/lessons`);
      const data = await response.json();

      if (data.success) {
        setLessons(data.lessons || []);
      }
    } catch (error) {
      console.error("Error fetching lessons:", error);
    }
  }

  // Reset form
  function resetForm() {
    setLessonId("");
    setTitle("");
    setDescription("");
    setStatus("DRAFT");
    setEditingId(null);
    setShowForm(false);
  }

  // Open Add form
  function handleAdd() {
    resetForm();
    setShowForm(true);
  }

  // Open Edit form
  function handleEdit(quiz: Quiz) {
    setEditingId(quiz.quiz_id);
    setLessonId(String(quiz.lesson_id));
    setTitle(quiz.title);
    setDescription(quiz.description || "");
    setStatus(quiz.status || "DRAFT");
    setShowForm(true);
  }

  // Add / Update
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!lessonId || !title.trim()) {
      alert("Please select a lesson and enter quiz title.");
      return;
    }

    const body = {
      lesson_id: Number(lessonId),
      title: title.trim(),
      description: description.trim(),
      status,
    };

    try {
      const url = editingId
        ? `${API_URL}/api/quizzes/${editingId}`
        : `${API_URL}/api/quizzes`;

      const method = editingId ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Operation failed.");
        return;
      }

      alert(
        editingId
          ? "Quiz updated successfully!"
          : "Quiz created successfully!"
      );

      resetForm();
      fetchQuizzes();
    } catch (error) {
      console.error("Save quiz error:", error);
      alert("Cannot connect to Backend.");
    }
  }

  // Delete
  async function handleDelete(id: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this quiz?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/quizzes/${id}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Delete failed.");
        return;
      }

      alert("Quiz deleted successfully!");

      fetchQuizzes();
    } catch (error) {
      console.error("Delete quiz error:", error);
      alert("Cannot connect to Backend.");
    }
  }

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        {/* Header */}
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Quizzes
          </h1>

          <p className="text-sm text-gray-500">
            Manage quizzes and questions
          </p>
        </header>

        {/* Content */}
        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">

            {/* Title + Add Quiz */}
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Quiz Management
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Create and manage quizzes for lessons.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAdd}
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add Quiz
              </button>
            </div>

            {/* Add / Edit Form */}
            {showForm && (
              <div className="mb-8 rounded-xl border bg-gray-50 p-6">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  {editingId ? "Edit Quiz" : "Add Quiz"}
                </h3>

                <form onSubmit={handleSubmit}>

                  {/* Lesson */}
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Lesson
                    </label>

                    <select
                      value={lessonId}
                      onChange={(e) => setLessonId(e.target.value)}
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    >
                      <option value="">Select Lesson</option>

                      {lessons.map((lesson) => (
                        <option
                          key={lesson.lesson_id}
                          value={lesson.lesson_id}
                        >
                          {lesson.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Title */}
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Quiz Title
                    </label>

                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Enter quiz title"
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    />
                  </div>

                  {/* Description */}
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Description
                    </label>

                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Enter quiz description"
                      rows={3}
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    />
                  </div>

                  {/* Status */}
                  <div className="mb-6">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Status
                    </label>

                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    >
                      <option value="DRAFT">DRAFT</option>
                      <option value="PUBLISHED">PUBLISHED</option>
                    </select>
                  </div>

                  {/* Buttons */}
                  <div className="flex gap-3">
                    <button
                      type="submit"
                      className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
                    >
                      {editingId ? "Update Quiz" : "Create Quiz"}
                    </button>

                    <button
                      type="button"
                      onClick={resetForm}
                      className="rounded-lg bg-gray-200 px-5 py-3 font-medium text-gray-700 hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Quiz Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">

                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-700">
                      ID
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Quiz
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Lesson
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Status
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {quizzes.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-10 text-center text-gray-500"
                      >
                        No quizzes found.
                      </td>
                    </tr>
                  ) : (
                    quizzes.map((quiz) => (
                      <tr
                        key={quiz.quiz_id}
                        className="border-b"
                      >
                        <td className="px-4 py-4 text-gray-600">
                          {quiz.quiz_id}
                        </td>

                        <td className="px-4 py-4 font-medium text-gray-900">
                          {quiz.title}
                        </td>

                        <td className="px-4 py-4 text-gray-600">
                          {quiz.lesson_title || "Unknown Lesson"}
                        </td>

                        <td className="px-4 py-4">
                          <span
                            className={
                              quiz.status === "PUBLISHED"
                                ? "rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700"
                                : "rounded-full bg-gray-200 px-3 py-1 text-xs font-medium text-gray-700"
                            }
                          >
                            {quiz.status}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          <button
                            type="button"
                            onClick={() => handleEdit(quiz)}
                            className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() => handleDelete(quiz.quiz_id)}
                            className="rounded-lg bg-red-100 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-200"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>

              </table>
            </div>

          </div>
        </section>
      </div>
    </main>
  );
}