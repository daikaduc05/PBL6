export type LessonLevel = "easy" | "medium" | "hard";
export type LessonAccess = "public" | "vip";
export type LessonStatus = "draft" | "pending" | "published" | "rejected";

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  sort_order: number;
}

export interface CategoryTreeResponse extends Category {
  children: CategoryTreeResponse[];
}

export interface Lesson {
  id: string;
  category_id: string;
  title: string;
  body: string | null;
  level: LessonLevel;
  access: LessonAccess;
  status: LessonStatus;
  created_at: string;
  updated_at: string;
}

export interface LessonListResponse {
  items: Lesson[];
  total: number;
  page: number;
  size: number;
}

export interface LessonQueryParams {
  category_id?: string;
  level?: LessonLevel | "all";
  q?: string;
  page?: number;
  size?: number;
}

export type MediaKind = "image" | "audio" | "video";

export interface MediaAsset {
  id: string;
  lesson_id: string;
  kind: MediaKind;
  s3_key: string;
  cdn_url: string;
  bytes: number;
}

