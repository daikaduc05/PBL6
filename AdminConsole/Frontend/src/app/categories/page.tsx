"use client";

import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

type Category = {
  category_id: number;
  name: string;
  description: string | null;
  created_at: string;
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  // Add form
  const [showForm, setShowForm] = useState(false);

  // Edit form
  const [editingId, setEditingId] = useState<number | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  // ========================================
  // GET CATEGORIES
  // ========================================

  const fetchCategories = async () => {
    try {
      const response = await fetch(
        "http://localhost:5000/api/categories"
      );

      const data = await response.json();

      if (data.success) {
        setCategories(data.categories);
      }
    } catch (error) {
      console.error("Failed to load categories:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  // ========================================
  // OPEN ADD FORM
  // ========================================

  const openAddForm = () => {
    setEditingId(null);
    setName("");
    setDescription("");
    setShowForm(true);
  };

  // ========================================
  // OPEN EDIT FORM
  // ========================================

  const openEditForm = (category: Category) => {
    setEditingId(category.category_id);
    setName(category.name);
    setDescription(category.description || "");
    setShowForm(true);
  };

  // ========================================
  // CANCEL FORM
  // ========================================

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setName("");
    setDescription("");
  };

  // ========================================
  // ADD CATEGORY
  // ========================================

  const handleAddCategory = async () => {
    if (!name.trim()) {
      alert("Please enter category name");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:5000/api/categories",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            description: description.trim(),
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        alert("Category added successfully!");

        handleCancel();
        fetchCategories();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Add category error:", error);
      alert("Cannot connect to backend");
    }
  };

  // ========================================
  // UPDATE CATEGORY
  // ========================================

  const handleUpdateCategory = async () => {
    if (!editingId) return;

    if (!name.trim()) {
      alert("Please enter category name");
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:5000/api/categories/${editingId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            description: description.trim(),
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        alert("Category updated successfully!");

        handleCancel();
        fetchCategories();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Update category error:", error);
      alert("Cannot connect to backend");
    }
  };

  // ========================================
  // DELETE CATEGORY
  // ========================================

  const handleDelete = async (id: number) => {
    const confirmDelete = confirm(
      "Are you sure you want to delete this category?"
    );

    if (!confirmDelete) return;

    try {
      const response = await fetch(
        `http://localhost:5000/api/categories/${id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (data.success) {
        alert("Category deleted successfully!");

        fetchCategories();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Delete category error:", error);
      alert("Cannot connect to backend");
    }
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">

        {/* HEADER */}
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Categories
          </h1>

          <p className="text-sm text-gray-500">
            Manage lesson categories
          </p>
        </header>

        {/* CONTENT */}
        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">

            {/* TITLE + ADD BUTTON */}
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Category Management
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Create and manage categories for lessons.
                </p>
              </div>

              <button
                type="button"
                onClick={openAddForm}
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add Category
              </button>
            </div>

            {/* ADD / EDIT FORM */}
            {showForm && (
              <div className="mb-6 rounded-lg border bg-gray-50 p-5">

                <h3 className="mb-4 text-lg font-semibold text-gray-900">
                  {editingId
                    ? "Edit Category"
                    : "Add New Category"}
                </h3>

                {/* NAME */}
                <div className="mb-4">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Category Name
                  </label>

                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter category name"
                    className="w-full rounded-lg border px-4 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* DESCRIPTION */}
                <div className="mb-4">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Description
                  </label>

                  <textarea
                    value={description}
                    onChange={(e) =>
                      setDescription(e.target.value)
                    }
                    placeholder="Enter description"
                    rows={3}
                    className="w-full rounded-lg border px-4 py-2 outline-none focus:border-blue-500"
                  />
                </div>

                {/* BUTTONS */}
                <div className="flex gap-2">

                  <button
                    type="button"
                    onClick={
                      editingId
                        ? handleUpdateCategory
                        : handleAddCategory
                    }
                    className="rounded-lg bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700"
                  >
                    {editingId ? "Save Changes" : "Save"}
                  </button>

                  <button
                    type="button"
                    onClick={handleCancel}
                    className="rounded-lg bg-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-400"
                  >
                    Cancel
                  </button>

                </div>
              </div>
            )}

            {/* TABLE */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">

                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Category
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Description
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

                  {loading ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-gray-500"
                      >
                        Loading categories...
                      </td>
                    </tr>
                  ) : categories.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-gray-500"
                      >
                        No categories found.
                      </td>
                    </tr>
                  ) : (
                    categories.map((category) => (
                      <tr
                        key={category.category_id}
                        className="border-b"
                      >

                        {/* CATEGORY */}
                        <td className="px-4 py-4 font-medium text-gray-900">
                          {category.name}
                        </td>

                        {/* DESCRIPTION */}
                        <td className="px-4 py-4 text-gray-600">
                          {category.description || "-"}
                        </td>

                        {/* STATUS */}
                        <td className="px-4 py-4">
                          <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                            ACTIVE
                          </span>
                        </td>

                        {/* ACTION */}
                        <td className="px-4 py-4">

                          <button
                            type="button"
                            onClick={() =>
                              openEditForm(category)
                            }
                            className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                category.category_id
                              )
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