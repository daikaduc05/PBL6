import { NextResponse } from "next/server";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import { getSession } from "@/lib/session";
import type { CategoryTreeResponse } from "@/types/content";

export async function GET() {
  const user = await getSession();
  try {
    const categories = await contentApi.get<CategoryTreeResponse[]>("/categories", { user });
    return NextResponse.json(categories);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
