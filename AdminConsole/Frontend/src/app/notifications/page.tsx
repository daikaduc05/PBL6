import Sidebar from "../components/Sidebar";

export default function NotificationsPage() {
  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        {/* Header */}
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Notifications
          </h1>

          <p className="text-sm text-gray-500">
            Manage system notifications
          </p>
        </header>

        {/* Content */}
        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">

            {/* Title + Add Notification */}
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Notification Management
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Create and manage notifications for users.
                </p>
              </div>

              <button
                type="button"
                className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
              >
                + Add Notification
              </button>
            </div>

            {/* Notification Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">

                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Title
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Message
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Type
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

                  {/* Notification 1 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      New Lesson Available
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      A new programming lesson is now available.
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                        LESSON
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                        SENT
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="rounded-lg bg-red-100 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>

                  {/* Notification 2 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      Quiz Reminder
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      You have an unfinished quiz to complete.
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-700">
                        QUIZ
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-700">
                        PENDING
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="rounded-lg bg-red-100 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>

                  {/* Notification 3 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      Payment Successful
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      Your premium subscription payment was successful.
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                        PAYMENT
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                        SENT
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="mr-2 rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        className="rounded-lg bg-red-100 px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>

                </tbody>
              </table>
            </div>

          </div>
        </section>
      </div>
    </main>
  );
}