import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { QuizRunner } from "@/components/feature/quiz-runner";
import type { QuizStudentResponse } from "@/types/quiz";

describe("QuizRunner", () => {
  const mockQuiz: QuizStudentResponse = {
    id: "quiz-1",
    lesson_id: "lesson-1",
    title: "Present Simple Tense Quiz",
    created_at: new Date().toISOString(),
    questions: [
      {
        id: "q-1",
        content: "She ___ to school every day.",
        type: "SINGLE_CHOICE",
        options: [
          { id: "opt-1", content: "goes" },
          { id: "opt-2", content: "go" },
          { id: "opt-3", content: "going" },
        ],
      },
      {
        id: "q-2",
        content: "Which of these are vowels?",
        type: "MULTI_CHOICE",
        options: [
          { id: "opt-a", content: "Vowel A" },
          { id: "opt-b", content: "Consonant B" },
          { id: "opt-e", content: "Vowel E" },
        ],
      },
    ],
  };

  it("renders quiz title and first question", () => {
    render(<QuizRunner quiz={mockQuiz} onSubmit={vi.fn()} />);
    expect(screen.getByText("Present Simple Tense Quiz")).toBeInTheDocument();
    expect(screen.getByText("She ___ to school every day.")).toBeInTheDocument();
    expect(screen.getByText("goes")).toBeInTheDocument();
  });

  it("allows selecting an option and submitting", () => {
    const handleSubmit = vi.fn();
    render(<QuizRunner quiz={mockQuiz} onSubmit={handleSubmit} />);

    // Select option A
    fireEvent.click(screen.getByText("goes"));

    // Next question
    fireEvent.click(screen.getByRole("button", { name: /Câu tiếp theo/i }));
    expect(screen.getByText("Which of these are vowels?")).toBeInTheDocument();

    // Select options in multi choice
    fireEvent.click(screen.getByText("Vowel A"));
    fireEvent.click(screen.getByText("Vowel E"));

    // Submit
    fireEvent.click(screen.getByRole("button", { name: /Nộp bài thi/i }));

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    const [answers] = handleSubmit.mock.calls[0];
    expect(answers).toEqual([
      { question_id: "q-1", selected_option_ids: ["opt-1"] },
      { question_id: "q-2", selected_option_ids: ["opt-a", "opt-e"] },
    ]);
  });
});
