"use client";

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

type Question = {
  question_id: number;
  question_text: string;
  quiz_title?: string;
};

type Option = {
  option_id: number;
  question_id: number;
  question_text?: string;
  option_text: string;
  is_correct: boolean;
};

export default function OptionsPage() {
  const API_URL = "http://localhost:5000";

  const [options, setOptions] = useState<Option[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [questionId, setQuestionId] = useState("");
  const [optionText, setOptionText] = useState("");
  const [isCorrect, setIsCorrect] = useState(false);

  useEffect(() => {
    fetchOptions();
    fetchQuestions();
  }, []);

  async function fetchOptions() {
    try {
      const response = await fetch(`${API_URL}/api/options`);
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load options");
      }

      setOptions(data.options || []);
    } catch (error) {
      console.error("Fetch options error:", error);
      alert("Cannot load Options. Please check Backend.");
    }
  }

  async function fetchQuestions() {
    try {
      const response = await fetch(`${API_URL}/api/questions`);
      const data = await response.json();

      if (response.ok && data.success) {
        setQuestions(data.questions || []);
      }
    } catch (error) {
      console.error("Fetch questions error:", error);
      alert("Cannot load Questions. Please check Backend.");
    }
  }

  function resetForm() {
    setQuestionId("");
    setOptionText("");
    setIsCorrect(false);
    setEditingId(null);
    setShowForm(false);
  }

  function handleAdd() {
    resetForm();
    setShowForm(true);
  }

  function handleEdit(option: Option) {
    setEditingId(option.option_id);
    setQuestionId(String(option.question_id));
    setOptionText(option.option_text);
    setIsCorrect(option.is_correct);
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (!questionId || !optionText.trim()) {
      alert("Please select a question and enter option text.");
      return;
    }

    const body = {
      question_id: Number(questionId),
      option_text: optionText.trim(),
      is_correct: isCorrect,
    };

    try {
      const url = editingId
        ? `${API_URL}/api/options/${editingId}`
        : `${API_URL}/api/options`;

      const response = await fetch(url, {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        alert(data.message || "Operation failed.");
        return;
      }

      alert(editingId ? "Option updated successfully!" : "Option created successfully!");
      resetForm();
      await fetchOptions();
    } catch (error) {
      console.error("Save option error:", error);
      alert("Cannot connect to Backend.");
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm("Are you sure you want to delete this option?")) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/options/${id}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        alert(data.message || "Delete failed.");
        return;
      }

      alert("Option deleted successfully!");
      await fetchOptions();
    } catch (error) {
      console.error("Delete option error:", error);
      alert("Cannot connect to Backend.");
    }
  } 

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Options</h1>
          <p className="text-sm text-gray-500">
            Manage answer options for questions
          </p>
        </header>

        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Option Management
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Add, edit, or delete answer options.
                </p>
              </div>

              <button
                type="button"
                onClick={handleAdd}
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add Option
              </button>
            </div>

            {showForm && (
              <div className="mb-8 rounded-xl border bg-gray-50 p-6">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  {editingId ? "Edit Option" : "Add Option"}
                </h3>

                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Question
                    </label>

                    <select
                      value={questionId}
                      onChange={(e) => setQuestionId(e.target.value)}
                      required
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    >
                      <option value="">Select Question</option>
                      {questions.map((question) => (
                        <option
                          key={question.question_id}
                          value={question.question_id}
                        >
                          {question.question_id}. {question.question_text}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-4">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Option Text
                    </label>

                    <input
                      type="text"
                      value={optionText}
                      onChange={(e) => setOptionText(e.target.value)}
                      required
                      placeholder="Enter answer option"
                      className="w-full rounded-lg border bg-white px-4 py-3"
                    />
                  </div>

                  <div className="mb-6">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
                      <input
                        type="checkbox"
                        checked={isCorrect}
                        onChange={(e) => setIsCorrect(e.target.checked)}
                        className="h-4 w-4"
                      />
                      This is the correct answer
                    </label>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="submit"
                      className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
                    >
                      {editingId ? "Update Option" : "Create Option"}
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
                    <th className="px-4 py-3 font-semibold text-gray-700">ID</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Question</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Option</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Correct Answer</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {options.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-10 text-center text-gray-500">
                        No options found.
                      </td>
                    </tr>
                  ) : (
                    options.map((option) => (
                      <tr key={option.option_id} className="border-b">
                        <td className="px-4 py-4 text-gray-600">
                          {option.option_id}
                        </td>
                        <td className="px-4 py-4 text-gray-600">
                          {option.question_text ||
                            questions.find((q) => q.question_id === option.question_id)?.question_text ||
                            `Question ${option.question_id}`}
                        </td>
                        <td className="px-4 py-4 font-medium text-gray-900">
                          {option.option_text}
                        </td>
                        <td className="px-4 py-4">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-medium ${
                              option.is_correct
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {option.is_correct ? "YES" : "NO"}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <button
                            type="button"
                            onClick={() => handleEdit(option)}
                            className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(option.option_id)}
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
