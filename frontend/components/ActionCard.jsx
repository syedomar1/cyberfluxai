// frontend/components/ActionCard.jsx
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import EvidenceBox from "./EvidenceBox";
import { ChevronDown, ChevronUp } from "lucide-react";

/**
 * ActionCard - responsive, accessible, expandable simulation card
 *
 * incident shape (example):
 * {
 *   id: "SIM-001",
 *   title: "Credential abuse → lateral move",
 *   severity: "High", // or Medium/Low
 *   summary: "Attacker used stolen token then moved laterally.",
 *   proposed_action: { title: "Quarantine endpoint & revoke token (30m)", description: "Isolate host and revoke token." },
 *   evidence: [
 *     { id: "l1", time: "2025-09-20T08:14:22Z", source: "EDR", line: "Process spawn: cmd.exe -> evil.exe" },
 *     ...
 *   ]
 * }
 *
 * Props:
 *  - incident (object)
 *  - onDryRun(incidentId) optional
 *  - onRequestApproval(incidentId) optional
 */

export default function ActionCard({
  incident = {},
  onDryRun,
  onRequestApproval,
}) {
  const {
    id = "SIM-0001",
    title = "Credential abuse → lateral movement",
    severity = "High",
    summary = "Simulated attacker used a stolen token and performed lateral movement across hosts.",
    proposed_action = {
      title: "Quarantine endpoint & revoke token (30m)",
      description: "Isolate host and revoke token.",
    },
    evidence = [],
  } = incident;

  const [expanded, setExpanded] = useState(false);

  const severityColor =
    severity === "High"
      ? "bg-red-600"
      : severity === "Medium"
      ? "bg-yellow-600"
      : "bg-green-600";

  const handleDryRun = (e) => {
    e.stopPropagation();
    if (typeof onDryRun === "function") return onDryRun(id);
    // local fallback
    alert(`Dry-run requested for ${id}`);
  };

  const handleRequestApproval = (e) => {
    e.stopPropagation();
    if (typeof onRequestApproval === "function") return onRequestApproval(id);
    alert(`Approval requested for ${id}`);
  };

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01, boxShadow: "0 8px 30px rgba(0,0,0,0.45)" }}
      transition={{ type: "spring", stiffness: 160, damping: 20 }}
      className="w-full bg-gradient-to-tr from-[#070708] to-[#0b0b0b] border border-[#19191b] rounded-2xl p-4 sm:p-5"
      role="article"
      aria-labelledby={`incident-${id}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs text-[#9fb0ff]">Simulation</div>
              <h3
                id={`incident-${id}`}
                className="font-semibold text-lg mt-1 leading-snug text-white"
              >
                {title}
              </h3>
            </div>

            <div className="flex-shrink-0 text-right">
              <div
                className={`inline-flex items-center px-3 py-1 rounded-md text-xs font-medium text-white ${severityColor}`}
                aria-label={`Severity: ${severity}`}
                title={`Severity: ${severity}`}
              >
                {severity}
              </div>
              <div className="text-xs text-[#8f8f8f] mt-2">ID: {id}</div>
            </div>
          </div>

          <p className="text-sm text-[#cfcfcf] mt-3 line-clamp-4">{summary}</p>

          <div className="mt-3">
            <div className="text-sm text-[#cfcfcf]">Proposed action</div>
            <div className="mt-2 p-3 rounded-lg bg-[#060607] border border-[#151517]">
              <div className="font-medium text-sm text-white">{proposed_action.title}</div>
              <div className="text-xs text-[#bfbfbf] mt-1">{proposed_action.description}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer actions */}
      <div className="mt-4 flex items-center gap-2 justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded((s) => !s)}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md text-sm bg-transparent border border-[#232326] text-[#9fb6ff] hover:bg-white/2"
            aria-expanded={expanded}
            aria-controls={`evidence-${id}`}
          >
            {expanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Hide details
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Show evidence
              </>
            )}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleDryRun}
            className="px-3 py-1 rounded-md text-sm border border-[#2a2a2a] hover:bg-white/2"
            title="Run a safe dry-run"
          >
            Dry-run
          </button>

          <button
            onClick={handleRequestApproval}
            className="px-3 py-1 rounded-md text-sm bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white"
            title="Request approval from approvers"
          >
            Request Approval
          </button>
        </div>
      </div>

      {/* Expandable evidence */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id={`evidence-${id}`}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.18 }}
            className="mt-4"
          >
            <EvidenceBox evidence={evidence} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}
