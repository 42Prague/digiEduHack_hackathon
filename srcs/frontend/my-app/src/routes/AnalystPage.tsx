import { useState, useRef, useEffect } from "react";
import { ResponseResults } from "../components/ResponseResults";

interface Msg {
  role: "analyst" | "ai";
  text: string;
}

interface AiPayload {
  generatedText: string | null;
  chartDetails: any | null;
}

export function AnalystPage() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [result, setResult] = useState<AiPayload>({
    generatedText: null,
    chartDetails: null,
  });
  const [loading, setLoading] = useState(false);

  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "auto" });
  }, [msgs]);

  async function send() {
    const content = input.trim();
    if (!content) return;

    setInput("");

    setMsgs((m) => [...m, { role: "analyst", text: content }]);

    const placeholderIndex = msgs.length + 1;
    setMsgs((m) => [...m, { role: "ai", text: "." }]);

    let dots = 1;
    const interval = setInterval(() => {
      dots = dots === 3 ? 1 : dots + 1;
      setMsgs((m) =>
        m.map((msg, idx) =>
          idx === placeholderIndex ? { ...msg, text: ".".repeat(dots) } : msg
        )
      );
    }, 300);

    setLoading(true);

    void (async () => {
      try {
        const res = await fetch("http://localhost:8000/analyst_chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content }),
        });

        const data = await res.json();

        const answer = data?.answer ?? "";
        const genText = data?.generated_text ?? null;
        const chart = data?.chart_details ?? null;

        clearInterval(interval);

        setMsgs((m) =>
          m.map((msg, idx) =>
            idx === placeholderIndex ? { ...msg, text: answer } : msg
          )
        );

        setResult({
          generatedText: genText,
          chartDetails: chart,
        });

        setLoading(false);
      } catch {
        clearInterval(interval);

        setMsgs((m) =>
          m.map((msg, idx) =>
            idx === placeholderIndex ? { ...msg, text: "error" } : msg
          )
        );

        setLoading(false);
      }
    })();
  }

  return (
    <div className="flex h-screen min-h-screen overflow-hidden">
  
      {/* LEFT CHAT PANEL */}
      <div className="w-[30%] flex flex-col border-r overflow-hidden">
  
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {msgs.length === 0 ? (
            <div className="flex items-center justify-center h-full">
                <div className="text-lg text-gray-500 dark:text-gray-400">
                Start chatting with the bot...
                </div>
            </div>
          ) : (
            msgs.map((m, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 ${
                  m.role === "analyst" ? "justify-end" : "justify-start"
                }`}
              >
                {m.role !== "analyst" && (
                  <div className="w-6 h-6 flex items-center justify-center bg-gray-300 dark:bg-gray-600 rounded-full text-xs">
                    🤖
                  </div>
                )}
  
                <div
                  className={
                    m.role === "analyst"
                      ? "bg-gray-200 p-2 rounded dark:bg-slate-800 text-black dark:text-white"
                      : "bg-gray-100 p-2 rounded dark:bg-slate-700 text-black dark:text-white"
                  }
                >
                  {m.text}
                </div>
  
                {m.role === "analyst" && (
                  <div className="w-6 h-6 flex items-center justify-center bg-gray-400 dark:bg-gray-500 rounded-full text-xs">
                    🧑
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={endRef} />
        </div>
  
        <div className="p-4 border-t flex gap-2 shrink-0">
          <input
            className="flex-1 border p-2 dark:bg-slate-800 dark:text-white dark:border-gray-700"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
          />
          <button className="border px-4" onClick={send}>
            Send
          </button>
        </div>
      </div>
  
      {/* RIGHT RESULTS PANEL */}
      <div className="w-[70%] h-full overflow-y-auto">
        {msgs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400 text-lg">
            Nothing to display
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center h-full text-gray-600 dark:text-gray-300 text-sm">
            <div className="w-8 h-8 border-4 border-gray-300 border-t-blue-500 rounded-full animate-spin dark:border-gray-700 dark:border-t-blue-400" />
          </div>
        ) : (
          <ResponseResults
            generatedText={result.generatedText}
            chartDetails={result.chartDetails}
          />
        )}
      </div>
  
    </div>
  );
}
