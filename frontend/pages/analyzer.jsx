// pages/analyzer.jsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import StarsBG from "../components/StarsBG";
import Papa from "papaparse";
// Direct REST calls to Gemini API (no SDK)
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function AnalyzerPage() {
  const [fileName, setFileName] = useState("");
  const [logsRows, setLogsRows] = useState([]); // array of objects
  const [columns, setColumns] = useState([]);
  const [parseError, setParseError] = useState("");

  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState("");
  const [reportError, setReportError] = useState("");

  // NEW: download state + toast
  const [isDownloading, setIsDownloading] = useState(false);
  const [toast, setToast] = useState({ show: false, msg: "", type: "info" });

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]); // {role: 'user'|'model', text}
  const [isChatting, setIsChatting] = useState(false);

  const API_KEY = "AIzaSyD54VXt73o8G8QQE38W7hn8pBdzuGEd87g";
  const MODEL_ID = "gemini-2.5-flash"; // v1 stable model id
  async function listModels() {
    const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(API_KEY)}`;
  
    const response = await fetch(url);
    const data = await response.json();
  
    console.log("Available models:");
    data.models?.forEach((model) => {
      console.log(model.name);
    });
  
    console.log("\nFull response:");
    console.log(JSON.stringify(data, null, 2));
  }
  

  const callGeminiGenerateContent = async (contents) => {
    listModels();
    if (!API_KEY) throw new Error("Missing NEXT_PUBLIC_GEMINI_API_KEY");
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${encodeURIComponent(API_KEY)}`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents }),
    });
    if (!resp.ok) {
      const errText = await resp.text().catch(() => "");
      throw new Error(`Gemini error ${resp.status}: ${errText || resp.statusText}`);
    }
    const data = await resp.json();
    const text = data?.candidates?.[0]?.content?.parts?.map((p) => p?.text || "").join("") || "";
    return text;
  };

  const logsSampleText = useMemo(() => {
    if (!logsRows || logsRows.length === 0) return "";
    const maxRows = Math.min(60, logsRows.length);
    const sample = logsRows.slice(0, maxRows);
    const headers = columns.length > 0 ? columns : Object.keys(sample[0] || {});
    const lines = [headers.join(",")].concat(
      sample.map((row) => headers.map((h) => `${row?.[h] ?? ""}`).join(","))
    );
    return lines.join("\n");
  }, [logsRows, columns]);

  const onFile = (file) => {
    setParseError("");
    setReport("");
    setReportError("");
    setChatMessages([]);
    if (!file) return;
    setFileName(file.name);
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: false,
      complete: (res) => {
        const data = res?.data || [];
        const fields = res?.meta?.fields || (data[0] ? Object.keys(data[0]) : []);
        setColumns(fields);
        setLogsRows(Array.isArray(data) ? data.filter(Boolean) : []);
      },
      error: (err) => {
        setParseError(err?.message || "Failed to parse CSV");
      },
    });
  };

  const generateReport = async () => {
    if (!API_KEY) { setReportError("Missing NEXT_PUBLIC_GEMINI_API_KEY"); return; }
    if (!logsSampleText) {
      setReportError("Please upload a CSV of network logs first.");
      return;
    }
    setIsGenerating(true);
    setReportError("");
    try {
      const prompt = `You are a senior cybersecurity analyst. Analyze the following network logs and identify suspicious activity, indicators of compromise, lateral movement, C2, exfiltration, auth anomalies, and policy violations. Provide:
\n- Executive summary
- Key findings (ranked)
- Evidence snippets (with fields)
- Likely root cause and kill chain mapping
- Recommended remediation actions (prioritized)
- Residual risks and monitoring follow-ups
\nNetwork Logs (CSV sample):\n\n${logsSampleText}`;

      const text = await callGeminiGenerateContent([
        { role: "user", parts: [{ text: prompt }] },
      ]);
      setReport(text);
      setChatMessages([
        { role: "model", text: text || "Report generated." },
      ]);
    } catch (e) {
      setReportError(e?.message || "Failed to generate report");
    } finally {
      setIsGenerating(false);
    }
  };

  const askChat = async () => {
    if (!API_KEY) { setReportError("Missing NEXT_PUBLIC_GEMINI_API_KEY"); return; }
    const question = chatInput.trim();
    if (!question) return;
    setIsChatting(true);
    setChatInput("");
    setChatMessages((msgs) => msgs.concat({ role: "user", text: question }));
    try {
      const systemContext = `You are assisting with incident response over network telemetry. Use the prior report as authoritative context when answering. If uncertain, state assumptions and ask for clarification. Be concise but precise.`;
      const context = [
        systemContext,
        report ? `Report:\n${report}` : "",
        logsSampleText ? `Logs sample (CSV):\n${logsSampleText}` : "",
      ]
        .filter(Boolean)
        .join("\n\n");

      const answer = await callGeminiGenerateContent([
        { role: "user", parts: [{ text: `${context}\n\nQuestion: ${question}` }] },
      ]);
      setChatMessages((msgs) => msgs.concat({ role: "model", text: answer }));
    } catch (e) {
      setChatMessages((msgs) =>
        msgs.concat({ role: "model", text: e?.message || "Failed to get answer" })
      );
    } finally {
      setIsChatting(false);
    }
  };

  // NEW: Download summary function.
  // This calls a Next.js API proxy at /api/report/direct.
  const downloadSummary = async ({ csv = "logs.csv", include_ai = true } = {}) => {
    setToast({ show: false, msg: "", type: "info" });
    setIsDownloading(true);
    try {
      const apiUrl = `/api/report/direct?csv=${encodeURIComponent(csv)}&include_ai=${include_ai ? "true" : "false"}`;
      const resp = await fetch(apiUrl, {
        method: "GET",
      });

      if (!resp.ok) {
        const txt = await resp.text().catch(() => "");
        throw new Error(`Failed to download report: ${resp.status} ${txt}`);
      }

      const blob = await resp.blob();
      let filename = "cyberflux_report.pdf";
      const contentDisp = resp.headers.get("content-disposition") || "";
      const m = /filename="?([^"]+)"?/.exec(contentDisp);
      if (m && m[1]) filename = m[1];

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setToast({ show: true, msg: "Summary downloaded.", type: "success" });
    } catch (err) {
      console.error("downloadSummary error:", err);
      setToast({ show: true, msg: String(err?.message || err || "Download failed"), type: "error" });
    } finally {
      setIsDownloading(false);
      setTimeout(() => setToast((t) => ({ ...t, show: false })), 4500);
    }
  };

  // Build UI - preserve all existing markup & add button below the Generate button
  return (
    <section
      id="analyzer"
      className="relative min-h-screen flex items-start justify-center overflow-hidden px-6 pt-24 pb-16 bg-[#050508]"
    >
      <StarsBG count={120} parallax={true} />
      <div className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-b from-transparent via-black/20 to-black/60" />

      {/* Spinner overlay when generating report or downloading */}
      {(isGenerating || isDownloading) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
          <div className="pointer-events-auto bg-black/60 rounded-lg p-6 flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-t-transparent border-white rounded-full animate-spin" />
            <div className="text-white text-sm">{isGenerating ? "Generating report..." : "Downloading summary..."}</div>
          </div>
        </div>
      )}

      {/* Simple toast */}
      {toast.show && (
        <div className={`fixed z-60 bottom-6 right-6 px-4 py-2 rounded-lg text-sm ${toast.type === "error" ? "bg-red-600 text-white" : toast.type === "success" ? "bg-green-600 text-white" : "bg-gray-800 text-white"}`}>
          {toast.msg}
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-6xl"
      >
        <h1 className="text-3xl md:text-4xl font-extrabold leading-tight text-center">
          Network Log Analyzer
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-[#7e30e1] to-[#2bd4ff] mt-2 text-lg md:text-2xl">
            Upload, Analyze, and Chat with your Telemetry
          </span>
        </h1>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload + Preview */}
          <div className="lg:col-span-1 glass p-4 rounded-xl border border-[#222] bg-black/40">
            <div className="text-[#cfcfcf] text-sm">Upload network logs (CSV)</div>
            <label className="mt-3 block">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => onFile(e.target.files?.[0])}
                className="block w-full text-sm text-[#bfbfbf] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gradient-to-r file:from-[#7e30e1] file:to-[#b364ff] file:text-white hover:file:opacity-95"
              />
            </label>
            {fileName ? (
              <div className="mt-3 text-xs text-[#9fb0ff]">Selected: {fileName}</div>
            ) : null}
            {parseError ? (
              <div className="mt-3 text-xs text-red-400">{parseError}</div>
            ) : null}

            {logsRows.length > 0 ? (
              <div className="mt-4 text-xs text-[#bfbfbf] max-h-64 overflow-auto rounded border border-[#222]">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-black/60">
                    <tr>
                      {columns.map((c) => (
                        <th key={c} className="px-2 py-2 font-semibold text-[#cfcfcf] border-b border-[#222]">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {logsRows.slice(0, 12).map((row, idx) => (
                      <tr key={idx} className="odd:bg-white/0 even:bg-white/[0.02]">
                        {columns.map((c) => (
                          <td key={c} className="px-2 py-2 border-b border-[#111] text-[#9aa0a6]">
                            {`${row?.[c] ?? ""}`}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="mt-4 text-xs text-[#8b8b8b]">No data loaded yet.</div>
            )}

            <div className="mt-4">
              <button
                type="button"
                onClick={generateReport}
                disabled={isGenerating || !logsRows.length}
                className="w-full px-4 py-2 rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white shadow disabled:opacity-50"
              >
                {isGenerating ? "Generating Report..." : "Generate Report"}
              </button>
              {reportError ? (
                <div className="mt-2 text-xs text-red-400">{reportError}</div>
              ) : null}

              {/* NEW: Download Summary button */}
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => downloadSummary({ csv: "logs.csv", include_ai: true })}
                  disabled={isDownloading}
                  className="w-full mt-2 px-4 py-2 rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white shadow disabled:opacity-50"
                >
                  {isDownloading ? "Downloading..." : "Download Summary"}
                </button>
              </div>
            </div>
          </div>

          {/* Report + Chat */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="glass p-4 rounded-xl border border-[#222] bg-black/40 min-h-[260px]">
              <div className="text-[#cfcfcf] text-sm font-semibold">Analysis Report</div>
              {report ? (
                <div className="prose prose-invert mt-3 text-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {report}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="mt-3 text-xs text-[#8b8b8b]">Generate a report to see findings here.</div>
              )}
            </div>

            <div className="glass p-4 rounded-xl border border-[#222] bg-black/40">
              <div className="text-[#cfcfcf] text-sm font-semibold">Chat about these logs</div>
              <div className="mt-3 flex flex-col gap-3 max-h-[320px] overflow-auto pr-1">
                {chatMessages.length === 0 ? (
                  <div className="text-xs text-[#8b8b8b]">Ask follow-up questions after generating a report.</div>
                ) : (
                  chatMessages.map((m, i) => (
                    <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                      <div
                        className={
                          "inline-block rounded-lg px-3 py-2 text-sm " +
                          (m.role === "user"
                            ? "bg-[#1a1a1a] text-[#cfcfcf] border border-[#333]"
                            : "bg-gradient-to-r from-[#0b0b10] to-[#0f0f18] text-[#d7e0ff] border border-[#222]")
                        }
                      >
                        {m.role === "model" ? (
                          <div className="prose prose-invert text-sm max-w-none">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {m.text}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          m.text
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="mt-3 flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask about anomalies, IOCs, remediation…"
                  className="flex-1 px-3 py-2 rounded-lg bg-black/40 border border-[#333] text-[#cfcfcf] placeholder:text-[#777]"
                />
                <button
                  type="button"
                  onClick={askChat}
                  disabled={isChatting || !report}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white disabled:opacity-50"
                >
                  {isChatting ? "Thinking…" : "Send"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
