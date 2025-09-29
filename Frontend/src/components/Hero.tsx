import { useState, useEffect } from "react";
import { useAuth } from "@/quries/quries";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import { useChat } from "@/quries/useChat";
import { Link } from "react-router-dom";
import type { AxiosError } from "axios";

export default function ChatPage() {
  const { token, user, logout } = useAuth();
  const { sendMessage } = useChat(token!);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ q: string; a: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasUploadedFile, setHasUploadedFile] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const handleSend = async () => {
    if (!file) {
      toast.error("Please upload a PDF file first");
      return;
    }
    if (!question.trim()) {
      toast.error("Please enter a question");
      return;
    }
    setLoading(true);
    try {
      setMessages((prev) => [...prev, { q: question, a: "..." }]);

      const answer = await sendMessage(question, file);

      setMessages((prev) => [...prev.slice(0, -1), { q: question, a: answer }]);

      setQuestion("");
    } catch (err) {
      const error = err as AxiosError<{ detail?: string }>;
      console.error("Send message error:", error);
      const errorMessage = error.message || "Failed to send message";
      toast.error(errorMessage);

      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      if (selectedFile.type !== "application/pdf") {
        toast.error("Please upload a PDF file");
        return;
      }

      setFile(selectedFile); // <-- Just set the file, no embedding step
      toast.success("File uploaded successfully!");
      setHasUploadedFile(true);
    }
  };

  // Add scroll to bottom effect
  useEffect(() => {
    const chatContainer = document.querySelector(".overflow-y-auto");
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [messages]);

  const handleLogout = () => {
    logout();
    // navigator
    toast.success("Logged out successfully!");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Chat with PDF 💬</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">
              Welcome, {user?.userName || "User"}!
            </span>
            <Link to="/history">
              <Button variant="outline" className="ml-2">
                View History
              </Button>
            </Link>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Upload PDF</h2>
          </div>
          <div className="p-4">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Chat Messages</h2>
          </div>
          <div className="p-4 min-h-[300px] max-h-[400px] overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center">
                No messages yet. Start a conversation!
              </p>
            ) : (
              <div className="space-y-4">
                {messages.map((m, i) => (
                  <div key={i} className="space-y-2">
                    <div className="bg-blue-50 p-3 rounded-lg ml-12">
                      <p className="text-sm font-medium text-blue-900">You:</p>
                      <p className="text-gray-800">{m.q}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg mr-12">
                      <p className="text-sm font-medium text-gray-900">Bot:</p>
                      <p className="text-gray-800">{m.a}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="flex gap-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={
                hasUploadedFile
                  ? "Ask something about your PDF..."
                  : "Please upload a PDF first"
              }
              disabled={loading || !hasUploadedFile}
              onKeyPress={(e) =>
                e.key === "Enter" && !loading && hasUploadedFile && handleSend()
              }
            />
            <Button
              onClick={handleSend}
              disabled={loading || !question.trim() || !hasUploadedFile}
            >
              {loading ? "Sending..." : "Send"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
