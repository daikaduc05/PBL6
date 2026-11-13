import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { QuizStudentResponse, QuizSubmitRequest, QuizSubmitResponse } from "@/types/quiz";

export function useQuiz(quizId: string) {
  return useQuery({
    queryKey: ["quiz", quizId],
    queryFn: () => api.get<QuizStudentResponse>(`/api/quizzes/${quizId}`),
    enabled: Boolean(quizId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLessonQuiz(lessonId: string) {
  return useQuery({
    queryKey: ["quiz-by-lesson", lessonId],
    queryFn: async () => {
      // First try to fetch by lesson_id
      try {
        return await api.get<QuizStudentResponse>(`/api/quizzes/lesson/${lessonId}`);
      } catch {
        // If not found as lesson_id, try fallback as direct quiz_id
        return await api.get<QuizStudentResponse>(`/api/quizzes/${lessonId}`);
      }
    },
    enabled: Boolean(lessonId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSubmitQuiz(quizId: string) {
  return useMutation({
    mutationFn: (body: QuizSubmitRequest) =>
      api.post<QuizSubmitResponse>(`/api/quizzes/${quizId}/submit`, body),
  });
}
