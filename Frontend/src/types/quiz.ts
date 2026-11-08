export type QuestionType = "SINGLE_CHOICE" | "MULTI_CHOICE";

export interface OptionStudentResponse {
  id: string;
  content: string;
}

export interface QuestionStudentResponse {
  id: string;
  content: string;
  type: QuestionType;
  options: OptionStudentResponse[];
}

export interface QuizStudentResponse {
  id: string;
  lesson_id: string;
  title: string;
  created_at: string;
  questions: QuestionStudentResponse[];
}

export interface AnswerSubmit {
  question_id: string;
  selected_option_ids: string[];
}

export interface QuizSubmitRequest {
  answers: AnswerSubmit[];
  duration_seconds?: number;
}

export interface QuestionResult {
  question_id: string;
  is_correct: boolean;
  selected_option_ids: string[];
  correct_option_ids: string[];
}

export interface QuizSubmitResponse {
  quiz_id: string;
  lesson_id: string;
  score: number;
  highest_score: number;
  total_questions: number;
  correct_answers_count: number;
  passed: boolean;
  completed_at: string;
  results: QuestionResult[];
}
