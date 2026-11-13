import { NextResponse } from "next/server";
import { getSession } from "@/lib/session";
import { backendErrorResponse, learningApi } from "@/lib/backend-client";

interface StatusResponse {
  lesson_id: string;
  is_favorite: boolean;
}

export async function GET(_req: Request, { params }: { params: Promise<{ lessonId: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json({ is_favorite: false });
  }

  const { lessonId } = await params;
  try {
    const data = await learningApi.get<StatusResponse>(`/lessons/${lessonId}/favorite`, { user });
    return NextResponse.json(data);
  } catch (err) {
    return backendErrorResponse(err);
  }
}

export async function POST(_req: Request, { params }: { params: Promise<{ lessonId: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  const { lessonId } = await params;
  try {
    const data = await learningApi.post(`/lessons/${lessonId}/favorite`, undefined, { user });
    return NextResponse.json(data, { status: 201 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}

export async function DELETE(_req: Request, { params }: { params: Promise<{ lessonId: string }> }) {
  const user = await getSession();
  if (!user) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Yêu cầu đăng nhập." } },
      { status: 401 },
    );
  }

  const { lessonId } = await params;
  try {
    await learningApi.delete(`/lessons/${lessonId}/favorite`, { user });
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    return backendErrorResponse(err);
  }
}
