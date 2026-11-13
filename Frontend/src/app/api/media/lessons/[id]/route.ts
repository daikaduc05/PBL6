import { NextRequest, NextResponse } from "next/server";
import { backendErrorResponse, contentApi } from "@/lib/backend-client";
import { getSession } from "@/lib/session";
import type { MediaAsset } from "@/types/content";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await getSession();
  try {
    const mediaList = await contentApi.get<MediaAsset[]>(`/media/lessons/${id}`, {
      user,
    });
    return NextResponse.json(mediaList);
  } catch (err) {
    return backendErrorResponse(err);
  }
}
