"use client";

import { useState, useRef, useEffect } from "react";
import { Send, BrainCircuit, User, BookOpen, ExternalLink, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

// --- ⚙️ CONFIGURATION ---
const API_URL = "https://laughing-fishstick-694p45w96jvfxx4j-8000.app.github.dev";

// 🔒 Securely pull the token from the environment.
//const SECURE_JWT_TOKEN = process.env.NEXT_PUBLIC_SECURE_JWT_TOKEN || "";
const SECURE_JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuZXh0anNfZnJvbnRlbmQiLCJyb2xlIjoiYWRtaW4ifQ.j9pwvaDW5KZs6GvpKkDG593LVGZwHItUUNCq-1-U0Dg"; // 🚨 Ensure your token is here!
type Source = { title: string; author: string; score: number; url: string };
type Message = { role: "user" | "assistant"; content: string; sources?: Source[] };

export default function Home() {
  // 1. The Anti-Hydration Lock
  const [isMounted, setIsMounted] = useState(false);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsMounted(true); // Unlocks the UI only after the browser is ready
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const clearChat = () => {
    setMessages([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

    try {
      const response = await fetch(`${API_URL}/ask_stream`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${SECURE_JWT_TOKEN}` 
        },
        body: JSON.stringify({ text: userMessage, top_k: 5 }),
      });

      if (response.status === 401) {
        throw new Error("401 Unauthorized. Invalid or missing Security Token.");
      }
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
          buffer = lines.pop() || ""; 

          for (const line of lines) {
            if (isFirstLine && line.startsWith("{")) {
              try {
                const metadata = JSON.parse(line);
                if (metadata.sources) {
                  setMessages((prev) => {
                    const newMsgs = [...prev];
                    const lastIndex = newMsgs.length - 1;
                    newMsgs[lastIndex] = { ...newMsgs[lastIndex], sources: metadata.sources };
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
                const lastIndex = newMsgs.length - 1;
                newMsgs[lastIndex] = { 
                  ...newMsgs[lastIndex], 
                  content: newMsgs[lastIndex].content + line + "\n" 
                };
                return newMsgs;
              });
            }
          }
        }
      }
      
      if (buffer) {
        setMessages((prev) => {
          const newMsgs = [...prev];
          const lastIndex = newMsgs.length - 1;
          newMsgs[lastIndex] = { 
            ...newMsgs[lastIndex], 
            content: newMsgs[lastIndex].content + buffer 
          };
          return newMsgs;
        });
      }

    } catch (error: any) {
      console.error("Stream failed:", error);
      setMessages((prev) => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { 
          role: "assistant", 
          content: `⚠️ **Connection Failed:** ${error.message || "Ensure your FastAPI server is running."}` 
        };
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Prevent rendering until the client is fully mounted (Bypasses Extension Hydration Errors)
  if (!isMounted) {
    return <div className="h-screen bg-slate-950 text-slate-200"></div>;
  }

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200 font-sans">
      <header className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md z-10">
        <div className="flex items-center">
          <BrainCircuit className="w-8 h-8 text-indigo-500 mr-3" />
          <h1 className="text-xl font-bold tracking-tight text-white">The Founder's Oracle</h1>
          <span className="ml-4 px-2 py-1 text-xs font-semibold bg-indigo-500/20 text-indigo-400 rounded-full border border-indigo-500/30">
            ULTRA v8.0 🔒
          </span>
        </div>
        <button 
          onClick={clearChat}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
        >
          <Trash2 size={16} />
          <span className="hidden sm:inline">Clear Memory</span>
        </button>
      </header>

      <main className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-8 scroll-smooth">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4">
            <BrainCircuit className="w-16 h-16 text-slate-700" />
            <p className="text-lg">Ask the Oracle a question about building startups, science, or finance.</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`flex max-w-4xl w-full ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                
                <div className={`flex items-center justify-center w-10 h-10 rounded-full shrink-0 ${msg.role === "user" ? "bg-indigo-600 ml-4" : "bg-emerald-600 mr-4"}`}>
                  {msg.role === "user" ? <User size={20} className="text-white"/> : <BrainCircuit size={20} className="text-white"/>}
                </div>

                <div className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"} max-w-[85%]`}>
                  <div className={`px-6 py-4 rounded-2xl shadow-sm ${msg.role === "user" ? "bg-indigo-600 text-white rounded-tr-none" : "bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700"}`}>
                    <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-900">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                      {isLoading && msg.role === "assistant" && msg.content === "" && (
                        <span className="animate-pulse flex items-center gap-2 text-emerald-400">
                          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                        </span>
                      )}
                    </div>
                  </div>

                  {/* --- FILTERED SOURCE CHIPS --- */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {msg.sources
                        .filter((src, index, self) => 
                          index === self.findIndex((t) => t.title === src.title)
                        )
                        .map((src, i) => (
                        <a 
                          key={i} 
                          href={src.url !== "#" ? src.url : undefined} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="group flex items-center px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700 border border-emerald-500/30 hover:border-emerald-400 rounded-lg text-xs text-slate-300 transition-all cursor-pointer shadow-sm"
                        >
                          <BookOpen size={14} className="text-emerald-400 mr-2 group-hover:text-emerald-300" />
                          <span className="font-medium mr-2">{src.title}</span>
                          
                          {/* NOTE: Score is commented out for cleaner UI. Uncomment the line below to show it again! */}
                          {/* <span className="text-slate-500 border-l border-slate-600 pl-2 pr-2">Score: {src.score}</span> */}
                          
                          <ExternalLink size={12} className="text-slate-500 ml-2 group-hover:text-emerald-400 transition-colors" />
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

      <div className="p-4 sm:p-6 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Query the Multi-Tenant Knowledge Graph..."
            className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-full pl-6 pr-16 py-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={20} className={isLoading ? "animate-pulse" : ""} />
          </button>
        </form>
        <div className="text-center mt-3 text-xs text-slate-500">
          Powered by Pinecone v2, Gemini 2.5 Flash, Upstash Redis, and Next.js
        </div>
      </div>
    </div>
  );
}