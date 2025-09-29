import type { ChatRequest } from "@/types/types";
import axios from "axios";

const API_URL = "http://localhost:8000";

interface ChatResponse {
  answer: string;
  success: boolean;
}

interface EmbeddingResponse {
  status: string;
}

export const useChat = (token: string) => {
  const sendMessage = async (question: string): Promise<ChatResponse> => {
    const chatRequest: ChatRequest = {
      user_question: question,
    };

    const res = await axios.post<ChatResponse>(`${API_URL}/llm`, chatRequest, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return res.data;
  };

  const generateEmbeddings = async (): Promise<EmbeddingResponse> => {
    const res = await axios.post<EmbeddingResponse>(
      `${API_URL}/inset`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return res.data;
  };

  return { sendMessage, generateEmbeddings };
};
