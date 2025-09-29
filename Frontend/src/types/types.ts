import type { Session } from "react-router-dom";

export interface UserSignupDTO {
  userName: string;
  email: string;
  password: string;
}

export interface UserLoginDTO {
  email: string;
  password: string;
}

export interface UserResponseDTO {
  id: string;
  userName: string;
  email: string;
  message: string;
}

export interface LoginResponseDTO {
  token: string;
}

export interface ChatRequest {
  user_question: string;
}

export interface ApiResponse {
  sessions: Session[];
}

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}
