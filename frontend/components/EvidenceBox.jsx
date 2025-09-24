export default function EvidenceBox({ evidence = [] }) {
  return (
    <div className="p-3 rounded-md bg-gradient-to-b from-[#07070b] to-[#0f0f12] border border-[#1b1b1b]">
      <div className="text-xs text-[#bfbfbf] mb-2">Evidence (log lines & indicators)</div>
      <div className="space-y-2">
        {evidence.map((e, i) => (
          <div key={i} className="text-xs font-mono text-[#d9d9d9] p-2 bg-[#060606]/30 rounded">
            <div className="opacity-70">{e.time} • {e.source}</div>
            <div>{e.line}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
