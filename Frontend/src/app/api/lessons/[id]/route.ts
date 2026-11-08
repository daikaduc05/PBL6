import { NextRequest, NextResponse } from "next/server";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import { getSession } from "@/lib/session";
import type { Lesson } from "@/types/content";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await getSession();
  try {
    const lesson = await contentApi.get<Lesson>(`/lessons/${id}`, { user });
    return NextResponse.json(lesson);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
