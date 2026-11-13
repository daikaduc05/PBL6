import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LessonCard } from "@/components/feature/lesson-card";
import type { Lesson } from "@/types/content";

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("LessonCard", () => {
  const mockLesson: Lesson = {
    id: "lesson-1",
    category_id: "cat-1",
    title: "English Grammar: Present Simple",
    body: "Learn the fundamentals of present simple tense.",
    level: "easy",
    access: "public",
    status: "published",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  it("renders lesson title and level correctly", () => {
    renderWithClient(<LessonCard lesson={mockLesson} />);
    expect(screen.getByText("English Grammar: Present Simple")).toBeInTheDocument();
    expect(screen.getByText("Cơ bản")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Vào học bài/i })).toHaveAttribute(
      "href",
      "/lessons/lesson-1",
    );
  });

  it("displays VIP badge when access is vip", () => {
    const vipLesson: Lesson = {
      ...mockLesson,
      id: "lesson-vip",
      title: "Business English Masterclass",
      access: "vip",
    };
    renderWithClient(<LessonCard lesson={vipLesson} />);
    expect(screen.getByText("VIP")).toBeInTheDocument();
  });
});
