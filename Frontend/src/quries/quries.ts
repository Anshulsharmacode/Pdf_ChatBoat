import { useState } from "react";
import axios from "axios";
import type {
  LoginResponseDTO,
  UserLoginDTO,
  UserResponseDTO,
  UserSignupDTO,
} from "@/types/types";

const API_URL = "http://localhost:8000";

interface User {
  id: string;
  userName: string;
  email: string;
}

// interface LoginResponse {
//   access_token: string;
//   user: User;
// }

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );

  const signup = async (
    signupData: UserSignupDTO
  ): Promise<UserResponseDTO> => {
    const res = await axios.post<UserResponseDTO>(
      `${API_URL}/signup`,
      signupData
    );
    return res.data;
  };

  const login = async (loginData: UserLoginDTO): Promise<LoginResponseDTO> => {
    const res = await axios.post<LoginResponseDTO>(
      `${API_URL}/login`,
      loginData
    );
    const { token } = res.data; // Changed from access_token to token
    if (token) {
      localStorage.setItem("token", token);
      setToken(token);
    }
    return res.data;
  };

  const getMe = async (): Promise<User> => {
    if (!token) throw new Error("No token available");

    const res = await axios.get<User>(`${API_URL}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  };
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return { user, token, signup, login, getMe, logout };
};
