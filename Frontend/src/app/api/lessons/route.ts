import { NextRequest, NextResponse } from "next/server";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import { getSession } from "@/lib/session";
import type { LessonListResponse } from "@/types/content";

export async function GET(req: NextRequest) {
  const user = await getSession();
  const searchParams = req.nextUrl.searchParams;

  const query = new URLSearchParams();
  const categoryId = searchParams.get("category_id");
  const level = searchParams.get("level");
  const q = searchParams.get("q");
  const page = searchParams.get("page") ?? "1";
  const size = searchParams.get("size") ?? "20";

  if (categoryId) query.set("category_id", categoryId);
  if (level && level !== "all") query.set("level", level);
  if (q) query.set("q", q);
  query.set("page", page);
  query.set("size", size);

  try {
    const data = await contentApi.get<LessonListResponse>(`/lessons?${query.toString()}`, {
      user,
    });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
