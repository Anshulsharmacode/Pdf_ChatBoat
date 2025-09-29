import axios from "axios";

const API_URL = "http://localhost:8000";

interface FileUploadResponse {
  success: boolean;
  message: string;
  fileId?: string;
}

export const useFileUpload = (token: string) => {
  const uploadFile = async (file: File): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post<FileUploadResponse>(
      `${API_URL}/upload`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return res.data;
  };

  return { uploadFile };
};
