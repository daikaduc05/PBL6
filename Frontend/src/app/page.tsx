import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";

// Placeholder root route — the real marketing landing page (route group
// `(marketing)`) is Ninthanon's scope per frontend.md §1, not built here.
// This just sends people somewhere sensible until that exists.
export default async function RootPage() {
  const user = await getSession();
  redirect(user ? "/profile" : "/login");
}
