import Navbar from "@/components/Navbar";
import { useState } from "react";
import axios from "axios";

export default function Demo() {
  const [actionResp, setActionResp] = useState(null);

  const runDryRun = async () => {
    setActionResp("Running dry-run…");
    try {
      const r = await axios.post("/api/action-bench", { test: "dry-run-123", detail: "quarantine host" });
      setActionResp(JSON.stringify(r.data, null, 2));
    } catch (e) {
      setActionResp("Error: " + (e.message || "unknown"));
    }
  };

  return (
    <div className="min-h-screen bg-[#050508] text-white">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-24">
        <h1 className="text-3xl font-bold mb-4">Demo Console</h1>
        <p className="text-sm text-[#bfbfbf] mb-6">Run a dry-run of automation (mock).</p>
        <div className="space-y-4">
          <button onClick={runDryRun} className="px-4 py-2 rounded bg-[#7e30e1]">Run Dry-Run</button>
          <pre className="p-4 rounded bg-[#08080b] border border-[#1b1b1b] text-xs">{actionResp || "No result yet."}</pre>
        </div>
      </main>
    </div>
  );
}
