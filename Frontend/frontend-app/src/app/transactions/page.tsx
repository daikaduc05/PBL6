import Sidebar from "../components/Sidebar";

export default function TransactionsPage() {
  return (
    <main className="min-h-screen bg-gray-100">
      <Sidebar />

      <div className="ml-64">
        {/* Header */}
        <header className="border-b bg-white px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Transactions
          </h1>

          <p className="text-sm text-gray-500">
            Manage payment transactions
          </p>
        </header>

        {/* Content */}
        <section className="p-8">
          <div className="rounded-xl bg-white p-6 shadow-sm">

            {/* Title */}
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Transaction Management
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                View and manage user payment transactions.
              </p>
            </div>

            {/* Transaction Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">

                <thead className="border-b bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-gray-700">
                      User
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Amount
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Payment
                    </th>

                    <th className="px-4 py-3 font-semibold text-gray-700">
                      Date
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

                  {/* Transaction 1 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      Ninthanon
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      $19.99
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      Premium Plan
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      2026-09-30
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
                        SUCCESS
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        View
                      </button>
                    </td>
                  </tr>

                  {/* Transaction 2 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      Somchai
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      $9.99
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      Basic Plan
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      2026-09-29
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-700">
                        PENDING
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        View
                      </button>
                    </td>
                  </tr>

                  {/* Transaction 3 */}
                  <tr className="border-b">
                    <td className="px-4 py-4 font-medium text-gray-900">
                      Anan
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      $29.99
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      Premium Plan
                    </td>

                    <td className="px-4 py-4 text-gray-600">
                      2026-09-28
                    </td>

                    <td className="px-4 py-4">
                      <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">
                        FAILED
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        className="rounded-lg bg-gray-200 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-300"
                      >
                        View
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