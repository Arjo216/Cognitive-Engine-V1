"use client";

import { useState, useRef, useEffect } from "react";
import { Send, BrainCircuit, User, BookOpen, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";

// --- CONFIGURE YOUR BACKEND HERE ---
const API_URL = "https://laughing-fishstick-694p45w96jvfxx4j-8000.app.github.dev";

type Source = { title: string; author: string; score: number; url: string };
type Message = { role: "user" | "assistant"; content: string; sources?: Source[] };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    // Add empty assistant message to stream into
    setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

    try {
      const response = await fetch(`${API_URL}/ask_stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userMessage, top_k: 5 }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;
      let isFirstLine = true;
      let buffer = "";

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // keep incomplete line in buffer

          for (const line of lines) {
            if (isFirstLine && line.startsWith("{")) {
              try {
                const metadata = JSON.parse(line);
                if (metadata.sources) {
                  setMessages((prev) => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1].sources = metadata.sources;
                    return newMsgs;
                  });
                }
              } catch (err) {
                console.error("Metadata parse error", err);
              }
              isFirstLine = false;
            } else {
              setMessages((prev) => {
                const newMsgs = [...prev];
                newMsgs[newMsgs.length - 1].content += line;
                return newMsgs;
              });
            }
          }
        }
      }
      
      if (buffer) {
        setMessages((prev) => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].content += buffer;
          return newMsgs;
        });
      }

    } catch (error) {
      console.error("Stream failed:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Engine connection failed. Ensure your FastAPI server is running and the API_URL is correct." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 font-sans">
      {/* Top Navigation Bar */}
      <header className="flex items-center p-5 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md z-10">
        <BrainCircuit className="w-8 h-8 text-indigo-500 mr-3" />
        <h1 className="text-xl font-bold tracking-tight text-white">The Founder's Oracle</h1>
        <span className="ml-4 px-2 py-1 text-xs font-semibold bg-indigo-500/20 text-indigo-400 rounded-full border border-indigo-500/30">
          ULTRA v6.0
        </span>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-8 scroll-smooth">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
            <BrainCircuit className="w-16 h-16 text-slate-700" />
            <p className="text-lg">Ask the Oracle a question about building startups.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`flex max-w-4xl w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                
                {/* Avatar */}
                <div className={`flex items-center justify-center w-10 h-10 rounded-full shrink-0 ${msg.role === "user" ? "bg-indigo-600 ml-4" : "bg-emerald-600 mr-4"}`}>
                  {msg.role === "user" ? <User size={20} className="text-white"/> : <BrainCircuit size={20} className="text-white"/>}
                </div>

                {/* Message Bubble */}
                <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`px-5 py-4 rounded-2xl shadow-sm ${msg.role === "user" ? "bg-indigo-600 text-white rounded-tr-none" : "bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700"}`}>
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                      {isLoading && msg.role === "assistant" && msg.content === "" && (
                        <span className="animate-pulse">Synthesizing...</span>
                      )}
                    </div>
                  </div>

                  {/* Render Sources if they exist */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {msg.sources.map((src, i) => (
                        <a 
                          key={i} 
                          href={src.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="group flex items-center px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700 border border-emerald-500/30 hover:border-emerald-400 rounded-lg text-xs text-slate-300 transition-all cursor-pointer shadow-sm"
                        >
                          <BookOpen size={14} className="text-emerald-400 mr-2 group-hover:text-emerald-300" />
                          <span className="font-medium mr-2">{src.title}</span>
                          <span className="text-slate-500 border-l border-slate-600 pl-2 pr-2">Score: {src.score}</span>
                          <ExternalLink size={12} className="text-slate-500 group-hover:text-emerald-400 transition-colors" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <div className="p-4 sm:p-6 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            suppressHydrationWarning
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Query the Paul Graham vector index..."
            className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-full pl-6 pr-16 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all disabled:opacity-50"
          />
          <button
            suppressHydrationWarning
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} className={isLoading ? "animate-pulse" : ""} />
          </button>
        </form>
        <div className="text-center mt-3 text-xs text-slate-500">
          Powered by Pinecone v2, Gemini 2.5 Flash, and Next.js
        </div>
      </div>
    </div>
  );
}