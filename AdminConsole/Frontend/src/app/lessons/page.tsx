"use client";

import { useEffect, useState } from "react";

const API_URL = "http://localhost:5000";

type Category = {
  category_id: number;
  name: string;
};

type Lesson = {
  lesson_id: number;
  category_id: number;
  category_name?: string;
  title: string;
  description: string | null;
  content: string | null;
  level: string;
  is_free: boolean;
  status: string;
  created_at: string;
  updated_at: string;
};

export default function LessonsPage() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    category_id: "",
    title: "",
    description: "",
    content: "",
    level: "EASY",
    is_free: true,
    status: "DRAFT",
  });

  // ========================================
  // GET LESSONS
  // ========================================

  const fetchLessons = async () => {
    try {
      const response = await fetch(`${API_URL}/api/lessons`);
      const data = await response.json();

      if (data.success) {
        setLessons(data.lessons);
      }
    } catch (error) {
      console.error("Error fetching lessons:", error);
    }
  };

  // ========================================
  // GET CATEGORIES
  // ========================================

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_URL}/api/categories`);
      const data = await response.json();

      if (data.success) {
        setCategories(data.categories);
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  // ========================================
  // LOAD DATA
  // ========================================

  useEffect(() => {
    fetchLessons();
    fetchCategories();
  }, []);

  // ========================================
  // INPUT CHANGE
  // ========================================

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? (e.target as HTMLInputElement).checked
          : value,
    }));
  };

  // ========================================
  // RESET FORM
  // ========================================

  const resetForm = () => {
    setForm({
      category_id: "",
      title: "",
      description: "",
      content: "",
      level: "EASY",
      is_free: true,
      status: "DRAFT",
    });

    setEditingId(null);
    setShowForm(false);
  };

  // ========================================
  // ADD / UPDATE LESSON
  // ========================================

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.category_id || !form.title.trim()) {
      alert("Please select category and enter lesson title.");
      return;
    }

    try {
      const url = editingId
        ? `${API_URL}/api/lessons/${editingId}`
        : `${API_URL}/api/lessons`;

      const method = editingId ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          category_id: Number(form.category_id),
          title: form.title,
          description: form.description,
          content: form.content,
          level: form.level,
          is_free: form.is_free,
          status: form.status,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Something went wrong.");
        return;
      }

      alert(
        editingId
          ? "Lesson updated successfully!"
          : "Lesson created successfully!"
      );

      resetForm();
      fetchLessons();
    } catch (error) {
      console.error("Save lesson error:", error);
      alert("Cannot connect to backend.");
    }
  };

  // ========================================
  // EDIT
  // ========================================

  const handleEdit = (lesson: Lesson) => {
    setForm({
      category_id: String(lesson.category_id),
      title: lesson.title,
      description: lesson.description || "",
      content: lesson.content || "",
      level: lesson.level,
      is_free: lesson.is_free,
      status: lesson.status,
    });

    setEditingId(lesson.lesson_id);
    setShowForm(true);
  };

  // ========================================
  // DELETE
  // ========================================

  const handleDelete = async (id: number) => {
    const confirmed = confirm(
      "Are you sure you want to delete this lesson?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/lessons/${id}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Delete failed.");
        return;
      }

      alert("Lesson deleted successfully!");

      fetchLessons();
    } catch (error) {
      console.error("Delete lesson error:", error);
      alert("Cannot connect to backend.");
    }
  };

  // ========================================
  // UI
  // ========================================

  return (
    <div className="p-8">

      {/* HEADER */}

      <div className="flex items-center justify-between mb-6">

        <div>
          <h1 className="text-3xl font-bold">
            Lessons
          </h1>

          <p className="text-gray-500 mt-1">
            Manage learning lessons
          </p>
        </div>

        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700"
        >
          + Add Lesson
        </button>

      </div>


      {/* FORM */}

      {showForm && (
        <div className="bg-white border rounded-xl p-6 mb-8 shadow-sm">

          <h2 className="text-xl font-semibold mb-5">
            {editingId ? "Edit Lesson" : "Add Lesson"}
          </h2>

          <form onSubmit={handleSubmit}>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

              {/* CATEGORY */}

              <div>
                <label className="block font-medium mb-2">
                  Category
                </label>

                <select
                  name="category_id"
                  value={form.category_id}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">
                    Select category
                  </option>

                  {categories.map((category) => (
                    <option
                      key={category.category_id}
                      value={category.category_id}
                    >
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>


              {/* TITLE */}

              <div>
                <label className="block font-medium mb-2">
                  Title
                </label>

                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="Enter lesson title"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>


              {/* LEVEL */}

              <div>
                <label className="block font-medium mb-2">
                  Level
                </label>

                <select
                  name="level"
                  value={form.level}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="EASY">EASY</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HARD">HARD</option>
                </select>
              </div>


              {/* STATUS */}

              <div>
                <label className="block font-medium mb-2">
                  Status
                </label>

                <select
                  name="status"
                  value={form.status}
                  onChange={handleChange}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="DRAFT">DRAFT</option>
                  <option value="PUBLISHED">PUBLISHED</option>
                </select>
              </div>

            </div>


            {/* DESCRIPTION */}

            <div className="mt-5">

              <label className="block font-medium mb-2">
                Description
              </label>

              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                rows={3}
                placeholder="Enter lesson description"
                className="w-full border rounded-lg px-3 py-2"
              />

            </div>


            {/* CONTENT */}

            <div className="mt-5">

              <label className="block font-medium mb-2">
                Content
              </label>

              <textarea
                name="content"
                value={form.content}
                onChange={handleChange}
                rows={6}
                placeholder="Enter lesson content"
                className="w-full border rounded-lg px-3 py-2"
              />

            </div>


            {/* FREE */}

            <div className="mt-5 flex items-center gap-3">

              <input
                type="checkbox"
                name="is_free"
                checked={form.is_free}
                onChange={handleChange}
                className="w-4 h-4"
              />

              <label className="font-medium">
                Free Lesson
              </label>

            </div>


            {/* BUTTONS */}

            <div className="flex gap-3 mt-6">

              <button
                type="submit"
                className="bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700"
              >
                {editingId ? "Update Lesson" : "Save Lesson"}
              </button>

              <button
                type="button"
                onClick={resetForm}
                className="bg-gray-500 text-white px-5 py-2 rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>

            </div>

          </form>

        </div>
      )}


      {/* LESSON TABLE */}

      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">

        <table className="w-full">

          <thead className="bg-gray-100">

            <tr>

              <th className="text-left px-4 py-3">
                ID
              </th>

              <th className="text-left px-4 py-3">
                Title
              </th>

              <th className="text-left px-4 py-3">
                Category
              </th>

              <th className="text-left px-4 py-3">
                Level
              </th>

              <th className="text-left px-4 py-3">
                Free
              </th>

              <th className="text-left px-4 py-3">
                Status
              </th>

              <th className="text-left px-4 py-3">
                Action
              </th>

            </tr>

          </thead>

          <tbody>

            {lessons.map((lesson) => (

              <tr
                key={lesson.lesson_id}
                className="border-t"
              >

                <td className="px-4 py-3">
                  {lesson.lesson_id}
                </td>

                <td className="px-4 py-3 font-medium">
                  {lesson.title}
                </td>

                <td className="px-4 py-3">
                  {lesson.category_name || "-"}
                </td>

                <td className="px-4 py-3">
                  {lesson.level}
                </td>

                <td className="px-4 py-3">
                  {lesson.is_free ? "YES" : "NO"}
                </td>

                <td className="px-4 py-3">
                  {lesson.status}
                </td>

                <td className="px-4 py-3">

                  <div className="flex gap-2">

                    <button
                      onClick={() => handleEdit(lesson)}
                      className="bg-yellow-500 text-white px-3 py-1 rounded hover:bg-yellow-600"
                    >
                      Edit
                    </button>

                    <button
                      onClick={() =>
                        handleDelete(lesson.lesson_id)
                      }
                      className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                    >
                      Delete
                    </button>

                  </div>

                </td>

              </tr>

            ))}

            {lessons.length === 0 && (

              <tr>

                <td
                  colSpan={7}
                  className="text-center py-8 text-gray-500"
                >
                  No lessons found.
                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>

    </div>
  );
}