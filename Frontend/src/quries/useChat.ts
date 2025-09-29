import axios from "axios";

const API_URL = "http://localhost:8000";

export const useChat = (token: string) => {
  const sendMessage = async (question: string, file: File): Promise<string> => {
    const formData = new FormData();
    formData.append("user_question", question);
    formData.append("file", file);

    const res = await axios.post(`${API_URL}/llm`, formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    });

    // If backend returns just the answer as string
    return res.data;
    // If backend returns { answer: string }
    // return res.data.answer;
  };

  return { sendMessage };
};
