"use client";

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

type Quiz = {
  quiz_id: number;
  title: string;
};

type Question = {
  question_id: number;
  quiz_id: number;
  quiz_title?: string;
  question_text: string;
  question_type: string;
};

export default function QuestionsPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [quizId, setQuizId] = useState("");
  const [questionText, setQuestionText] = useState("");
  const [questionType, setQuestionType] = useState("MULTIPLE_CHOICE");

  const API_URL = "http://localhost:5000";

  useEffect(() => {
    fetchQuestions();
    fetchQuizzes();
  }, []);

  async function fetchQuestions() {
    try {
      const response = await fetch(`${API_URL}/api/questions`);
      const data = await response.json();

      if (data.success) {
        setQuestions(data.questions || []);
      }
    } catch (error) {
      console.error("Error fetching questions:", error);
      alert("Cannot connect to Backend.");
    }
  }

  async function fetchQuizzes() {
    try {
      const response = await fetch(`${API_URL}/api/quizzes`);
      const data = await response.json();

      if (data.success) {
        setQuizzes(data.quizzes || []);
      }
    } catch (error) {
      console.error("Error fetching quizzes:", error);
    }
  }

  function resetForm() {
    setQuizId("");
    setQuestionText("");
    setQuestionType("MULTIPLE_CHOICE");
    setEditingId(null);
    setShowForm(false);
  }

  function handleAdd() {
    resetForm();
    setShowForm(true);
  }

  function handleEdit(question: Question) {
    setEditingId(question.question_id);
    setQuizId(String(question.quiz_id));
    setQuestionText(question.question_text);
    setQuestionType(question.question_type || "MULTIPLE_CHOICE");
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!quizId || !questionText.trim()) {
      alert("Please select a quiz and enter question text.");
      return;
    }

    const body = {
      quiz_id: Number(quizId),
      question_text: questionText.trim(),
      question_type: questionType,
    };

    try {
      const url = editingId
        ? `${API_URL}/api/questions/${editingId}`
        : `${API_URL}/api/questions`;

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
          ? "Question updated successfully!"
          : "Question created successfully!"
      );

      resetForm();
      fetchQuestions();
    } catch (error) {
      console.error("Save question error:", error);
      alert("Cannot connect to Backend.");
    }
  }

  async function handleDelete(id: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this question?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/questions/${id}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Delete failed.");
        return;
      }

      alert("Question deleted successfully!");

      fetchQuestions();
    } catch (error) {
      console.error("Delete question error:", error);
      alert("Cannot connect to Backend.");
    }
  }

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Questions
          </h1>

          <p className="text-sm text-gray-500">
            Manage questions for quizzes
          </p>
        </header>

        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">

            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Question Management
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Create and manage questions for quizzes.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAdd}
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add Question
              </button>
            </div>

            {showForm && (
              <div className="mb-8 rounded-xl border bg-gray-50 p-6">

                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  {editingId ? "Edit Question" : "Add Question"}
                </h3>

                <form onSubmit={handleSubmit}>

                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Quiz
                    </label>

                    <select
                      value={quizId}
                      onChange={(e) => setQuizId(e.target.value)}
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    >
                      <option value="">Select Quiz</option>

                      {quizzes.map((quiz) => (
                        <option
                          key={quiz.quiz_id}
                          value={quiz.quiz_id}
                        >
                          {quiz.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Question
                    </label>

                    <textarea
                      value={questionText}
                      onChange={(e) =>
                        setQuestionText(e.target.value)
                      }
                      placeholder="Enter question text"
                      rows={4}
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    />
                  </div>

                  <div className="mb-6">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Question Type
                    </label>

                    <select
                      value={questionType}
                      onChange={(e) =>
                        setQuestionType(e.target.value)
                      }
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    >
                      <option value="MULTIPLE_CHOICE">
                        MULTIPLE_CHOICE
                      </option>

                      <option value="SINGLE_CHOICE">
                        SINGLE_CHOICE
                      </option>
                    </select>
                  </div>

                  <div className="flex gap-3">

                    <button
                      type="submit"
                      className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
                    >
                      {editingId
                        ? "Update Question"
                        : "Create Question"}
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
                      Question
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Type
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Action
                    </th>

                  </tr>
                </thead>

                <tbody>

                  {questions.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-10 text-center text-gray-500"
                      >
                        No questions found.
                      </td>
                    </tr>
                  ) : (
                    questions.map((question) => (
                      <tr
                        key={question.question_id}
                        className="border-b"
                      >

                        <td className="px-4 py-4 text-gray-600">
                          {question.question_id}
                        </td>

                        <td className="px-4 py-4 text-gray-600">
                          {question.quiz_title || "Unknown Quiz"}
                        </td>

                        <td className="px-4 py-4 font-medium text-gray-900">
                          {question.question_text}
                        </td>

                        <td className="px-4 py-4">
                          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                            {question.question_type}
                          </span>
                        </td>

                        <td className="px-4 py-4">

                          <button
                            type="button"
                            onClick={() => handleEdit(question)}
                            className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(question.question_id)
                            }
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