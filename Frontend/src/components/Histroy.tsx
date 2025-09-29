import { useState, useEffect } from "react";
import { useAuth } from "@/quries/quries";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import axios, { AxiosError } from "axios";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

interface Message {
  question: string;
  answer: string;
  created_at: string;
}

interface Session {
  _id: string;
  filename: string;
  messages: Message[];
  last_message: string;
}

export default function ChatHistory() {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, navigate]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      if (!token) {
        throw new Error("No authentication token");
      }

      const response = await axios.get("http://localhost:8000/chat-history", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.data.sessions) {
        setSessions(response.data.sessions);
      }
    } catch (err) {
      const error = err as AxiosError<{ detail?: string }>;
      console.error("Error fetching history:", error);

      if (error instanceof AxiosError && error.response?.status === 401) {
        toast.error("Session expired. Please login again");
        logout();
        navigate("/login");
      } else {
        toast.error(
          error.response?.data?.detail || "Failed to fetch chat history"
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Chat History</h1>
          <Button variant="outline" onClick={() => navigate("/chat")}>
            Back to Chat
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <p>Loading chat history...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-10 bg-white rounded-lg shadow-sm border">
            <p className="text-gray-500">No chat history found</p>
          </div>
        ) : (
          <div className="grid gap-6">
            {sessions.map((session) => (
              <Card key={session._id}>
                <CardHeader>
                  <CardTitle className="flex justify-between items-center">
                    <span>{session.filename}</span>
                    <span className="text-sm text-gray-500">
                      Last message: {formatDate(session.last_message)}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    variant="outline"
                    onClick={() =>
                      setSelectedSession(
                        selectedSession === session._id ? null : session._id
                      )
                    }
                  >
                    {selectedSession === session._id ? "Hide" : "Show"} Messages
                  </Button>

                  {selectedSession === session._id && (
                    <div className="mt-4 space-y-4">
                      {session.messages.map((msg, idx) => (
                        <div key={idx} className="border rounded-lg p-4">
                          <div className="mb-2">
                            <p className="font-medium">Q: {msg.question}</p>
                            <span className="text-sm text-gray-500">
                              {formatDate(msg.created_at)}
                            </span>
                          </div>
                          <p className="text-gray-700">A: {msg.answer}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
