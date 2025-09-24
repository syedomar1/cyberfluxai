"use client";
import { useState } from "react";
import EvidenceBox from "./EvidenceBox";
import { motion } from "framer-motion";

export default function ActionCard({ incident }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div whileHover={{ scale: 1.01 }} className="glass p-4 rounded-xl border border-[#2b2b2b]">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold">{incident.title}</h3>
          <p className="text-sm text-[#bdbdbd] mt-1">{incident.summary}</p>
        </div>
        <div className="text-sm text-[#9ee6b8]">{incident.severity}</div>
      </div>

      <div className="mt-4">
        <div className="text-sm text-[#cfcfcf]">Proposed action:</div>
        <div className="p-3 rounded-md bg-[#0b0b0b] border border-[#1f1f1f] mt-2">
          <strong>{incident.proposed_action.title}</strong>
          <div className="text-xs text-[#bfbfbf] mt-1">{incident.proposed_action.description}</div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <button onClick={() => setExpanded(!expanded)} className="text-sm text-[#9fb6ff]">
            {expanded ? "Hide details" : "Show evidence"}
          </button>
          <div className="flex space-x-2">
            <button className="px-3 py-1 text-sm border rounded-md">Dry-run</button>
            <button className="px-3 py-1 text-sm bg-[#7e30e1] rounded-md">Request Approval</button>
          </div>
        </div>

        {expanded && <div className="mt-3"><EvidenceBox evidence={incident.evidence} /></div>}
      </div>
    </motion.div>
  );
}
