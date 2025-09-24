// frontend/components/EvidenceBox.jsx
"use client";

export default function EvidenceBox({ evidence = [] }) {
  // evidence: [{ time, source, line }, ...]
  if (!evidence || evidence.length === 0) {
    return (
      <div className="p-3 rounded-md bg-gradient-to-b from-[#07070b] to-[#0f0f12] border border-[#1b1b1b]">
        <div className="text-xs text-[#bfbfbf] mb-2">Evidence (log lines & indicators)</div>
        <div className="text-sm text-[#cfcfcf]">No evidence available.</div>
      </div>
    );
  }

  return (
    <div className="p-3 rounded-md bg-gradient-to-b from-[#07070b] to-[#0f0f12] border border-[#1b1b1b]">
      <div className="text-xs text-[#bfbfbf] mb-2">Evidence (log lines & indicators)</div>

      <div className="space-y-2">
        {evidence.map((e, i) => (
          <div
            key={e.id ?? i}
            className="text-xs font-mono text-[#d9d9d9] p-2 bg-[#060606]/30 rounded break-words"
          >
            <div className="opacity-70 text-[11px] mb-1">
              {e.time ?? "—"} &nbsp;•&nbsp; {e.source ?? "unknown"}
            </div>
            <div className="leading-tight text-sm">{e.line ?? "(no line provided)"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
