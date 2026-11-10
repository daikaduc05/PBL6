"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";

type User = {
  user_id: number;
  username: string;
  email: string;
  role: "CUSTOMER" | "EDITOR" | "ADMIN" | string;
  status: "ACTIVE" | "INACTIVE" | "LOCKED" | string;
  is_vip: boolean;
  created_at: string;
};

type UsersResponse = {
  success: boolean;
  users?: User[];
  message?: string;
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editUsername, setEditUsername] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editRole, setEditRole] = useState("CUSTOMER");
  const [editStatus, setEditStatus] = useState("ACTIVE");
  const [editVip, setEditVip] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:5000/api/users", {
        cache: "no-store",
      });

      const data: UsersResponse = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to load users.");
      }

      setUsers(Array.isArray(data.users) ? data.users : []);
    } catch (err) {
      console.error("Load users error:", err);
      setError(
        err instanceof Error
          ? `Cannot load users: ${err.message}`
          : "Cannot connect to Backend Server."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const openEdit = (user: User) => {
    console.log("Selected user:", user);
console.log("Username:", user.username, "Email:", user.email);
    setEditingId(user.user_id);
    setEditUsername(user.username ?? "");
    setEditEmail(user.email ?? "");
    setEditRole(user.role ?? "CUSTOMER");
    setEditStatus(user.status ?? "ACTIVE");
    setEditVip(Boolean(user.is_vip));
    setError("");

    window.setTimeout(() => {
      document.getElementById("edit-user-form")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 0);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditUsername("");
    setEditEmail("");
    setEditRole("CUSTOMER");
    setEditStatus("ACTIVE");
    setEditVip(false);
  };

  const updateUser = async () => {
    if (editingId === null) {
      setError("Please select a user to edit.");
      return;
    }

    if (!editUsername.trim() || !editEmail.trim()) {
      setError("Username and email are required.");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:5000/api/users/${editingId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: editUsername.trim(),
            email: editEmail.trim(),
            role: editRole,
            status: editStatus,
            is_vip: editVip,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to update user.");
      }

      await loadUsers();
      cancelEdit();
      window.alert("User updated successfully!");
    } catch (err) {
      console.error("Update user error:", err);
      setError(
        err instanceof Error ? err.message : "Failed to update user."
      );
    } finally {
      setSaving(false);
    }
  };

  const deleteUser = async (userId: number) => {
    const user = users.find((item) => item.user_id === userId);
    const confirmed = window.confirm(
      `Are you sure you want to delete ${user?.username ?? "this user"}?`
    );

    if (!confirmed) return;

    setError("");

    try {
      const response = await fetch(
        `http://localhost:5000/api/users/${userId}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Failed to delete user.");
      }

      if (editingId === userId) cancelEdit();

      await loadUsers();
      window.alert("User deleted successfully!");
    } catch (err) {
      console.error("Delete user error:", err);
      setError(
        err instanceof Error ? err.message : "Failed to delete user."
      );
    }
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <p className="text-sm text-gray-500">Manage system users</p>
        </header>

        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  User Management
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  Manage CUSTOMER, EDITOR and ADMIN accounts.
                </p>
              </div>

              <a
                href="/users/new"
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add User
              </a>
            </div>

            {error && (
              <div
                role="alert"
                className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            {editingId !== null && (
              <section
                id="edit-user-form"
                className="mb-6 scroll-mt-6 rounded-xl border border-blue-200 bg-blue-50 p-6"
              >
                <h3 className="mb-1 text-lg font-semibold text-gray-900">
                  Edit User
                </h3>
                <p className="mb-5 text-sm text-gray-600">
                  Editing user ID: {editingId}
                </p>

                <div className="mb-4">
                  <label
                    htmlFor="edit-username"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    Username
                  </label>
                  <input
                    id="edit-username"
                    type="text"
                    autoComplete="off"
                    value={editUsername}
                    onChange={(event) => setEditUsername(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />
                </div>

                <div className="mb-4">
                  <label
                    htmlFor="edit-email"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    Email
                  </label>
                  <input
                    id="edit-email"
                    type="email"
                    autoComplete="off"
                    value={editEmail}
                    onChange={(event) => setEditEmail(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />
                </div>

                <div className="mb-4">
                  <label
                    htmlFor="edit-role"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    Role
                  </label>
                  <select
                    id="edit-role"
                    value={editRole}
                    onChange={(event) => setEditRole(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 outline-none focus:border-blue-500"
                  >
                    <option value="CUSTOMER">CUSTOMER</option>
                    <option value="EDITOR">EDITOR</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>

                <div className="mb-5">
                  <label
                    htmlFor="edit-status"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    Status
                  </label>
                  <select
                    id="edit-status"
                    value={editStatus}
                    onChange={(event) => setEditStatus(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 outline-none focus:border-blue-500"
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="INACTIVE">INACTIVE</option>
                    <option value="LOCKED">LOCKED</option>
                  </select>
                </div>

                <label className="mb-5 flex items-center gap-2 text-sm font-medium text-gray-700">
                  <input
                    type="checkbox"
                    checked={editVip}
                    onChange={(event) => setEditVip(event.target.checked)}
                    className="h-4 w-4"
                  />
                  VIP User
                </label>

                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => void updateUser()}
                    disabled={saving}
                    className="rounded-lg bg-green-600 px-5 py-2 font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    disabled={saving}
                    className="rounded-lg bg-gray-200 px-5 py-2 font-medium text-gray-700 hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </section>
            )}

            {loading ? (
              <div className="py-10 text-center text-gray-500">
                Loading users...
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        Name
                      </th>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        Email
                      </th>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        Role
                      </th>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        Status
                      </th>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        VIP
                      </th>
                      <th className="px-4 py-3 font-semibold text-gray-700">
                        Action
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {users.length === 0 ? (
                      <tr>
                        <td
                          colSpan={6}
                          className="px-4 py-10 text-center text-gray-500"
                        >
                          No users found.
                        </td>
                      </tr>
                    ) : (
                      users.map((user) => (
                        <tr key={user.user_id} className="border-b">
                          <td className="px-4 py-4 font-medium text-gray-900">
                            {user.username}
                          </td>
                          <td className="px-4 py-4 text-gray-600">
                            {user.email}
                          </td>
                          <td className="px-4 py-4">
                            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                              {user.role}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                              {user.status}
                            </span>
                          </td>
                          <td className="px-4 py-4">
                            {user.is_vip ? "YES" : "NO"}
                          </td>
                          <td className="whitespace-nowrap px-4 py-4">
                            <button
                              type="button"
                              onClick={() => openEdit(user)}
                              className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                            >
                              Edit
                            </button>

                            <button
                              type="button"
                              onClick={() => void deleteUser(user.user_id)}
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
            )}
          </div>
        </section>
      </div>
    </main>
  );
}