// frontend/components/Services.jsx
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Database,
  Zap,
  ShieldCheck,
  FileText,
  ClipboardCheck,
  BarChart3,
  Hash,
  Layers,
} from "lucide-react";

const CAPABILITIES = [
  {
    id: "ingest",
    short: "Log Ingestion",
    title: "Telemetry Ingestion",
    group: "Pipeline",
    icon: Database,
    blurb: "Collect endpoint, IdP, cloud logs; normalize and enrich with threat intel.",
    details:
      "Agents, syslog, cloud-native streams and EDR feeds are normalized into a unified schema. Enrichment adds geolocation, IOC matches, and asset context so downstream models have clean, consistent inputs.",
  },
  {
    id: "preproc",
    short: "Preprocessing",
    title: "Preprocessing Module",
    group: "Pipeline",
    icon: Layers,
    blurb: "Sessionization, deduplication, and feature extraction at ingest time.",
    details:
      "Preprocesser does sessionization (user/host timeline), deduplcation of noisy alerts, and feature extraction (behavioral vectors, statistical baselines) so the GenAI Threat Analyzer can reason efficiently.",
  },
  {
    id: "planner",
    short: "GenAI Planner",
    title: "GenAI Threat Analyzer / Planner",
    group: "Reasoning",
    icon: Zap,
    blurb: "LLM-guided planner that proposes containment steps and rollback plans.",
    details:
      "A retrieval-augmented planner consults playbooks, MITRE mappings and past incident dossiers to propose prioritized, safety-checked actions (e.g., quarantine host, revoke token, block destination). Each plan includes a rollback recipe.",
  },
  {
    id: "action",
    short: "Action Engine",
    title: "Action Engine",
    group: "Reasoning",
    icon: Hash,
    blurb: "Execute guard-railed actions through idempotent playbooks and automation connectors.",
    details:
      "Actions are executed by auditable playbooks (SOAR / infrastructure automation). High-impact steps are approval-gated and every step is logged with precomputed rollback steps and canary tests.",
  },
  {
    id: "explain",
    short: "Explanations",
    title: "Explanation Engine (ELAE)",
    group: "Governance",
    icon: ShieldCheck,
    blurb: "Evidence-linked explanations: each claim cites exact log lines and a faithfulness score.",
    details:
      "ELAE ties human-readable rationales to exact evidence (log line IDs, timestamps, and IOCs). Explanations carry a faithfulness score that measures how well the narrative aligns with the underlying model attributions.",
  },
  {
    id: "policy",
    short: "Policy-as-Code",
    title: "Policy-as-Code",
    group: "Governance",
    icon: ClipboardCheck,
    blurb: "Machine-checkable policies and approval tiers prevent unsafe automation.",
    details:
      "Policies are encoded as machine-checkable rules (impact tiers, asset sensitivity, SLA windows). The policy engine validates every proposed action and determines auto-exec vs. approval paths.",
  },
  {
    id: "dossier",
    short: "Auditable Dossiers",
    title: "Auditable Dossiers",
    group: "Governance",
    icon: FileText,
    blurb: "Tamper-evident incident records for compliance and post-incident review.",
    details:
      "Incident dossiers bundle raw events, model artifacts, explanations, and approvals into tamper-evident records suitable for internal or regulatory review.",
  },
  {
    id: "bench",
    short: "ACTION-Bench",
    title: "ACTION-Bench",
    group: "Measurement",
    icon: BarChart3,
    blurb: "Measure MTTD/MTTC, rollback rates and exposure reduction.",
    details:
      "ACTION-Bench simulates attacks and measures action quality: time to contain, false-mitigation rates, rollback reliability, analyst workload, and compute token costs.",
  },
];

const groups = ["All", "Pipeline", "Reasoning", "Governance", "Measurement"];

export default function Services() {
  const [activeGroup, setActiveGroup] = useState("All");
  const [selected, setSelected] = useState(null);

  const visible = CAPABILITIES.filter(
    (c) => activeGroup === "All" || c.group === activeGroup
  );

  return (
    <section id="services" className="py-20 px-6 bg-gradient-to-tr from-[#06060a] to-[#08080d]">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-4xl font-bold">Core Capabilities</h2>
            <p className="text-sm text-[#bdbdbd] mt-1 max-w-xl">
              CyberFluxAI blends telemetry, generative reasoning, policy-as-code, and auditable automation to close the loop from detection to defensible action.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {groups.map((g) => (
              <button
                key={g}
                onClick={() => {
                  setActiveGroup(g);
                  setSelected(null);
                }}
                className={`px-3 py-1 rounded-md text-sm font-medium transition ${
                  activeGroup === g
                    ? "bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-black shadow-md"
                    : "text-[#bfbfbf] bg-transparent hover:bg-white/5"
                }`}
                aria-pressed={activeGroup === g}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {visible.map((cap) => {
            const Icon = cap.icon;
            const isOpen = selected === cap.id;
            return (
              <motion.article
                key={cap.id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ translateY: -6, boxShadow: "0 12px 30px rgba(99,52,255,0.12)" }}
                onClick={() => setSelected(isOpen ? null : cap.id)}
                className="cursor-pointer p-5 rounded-2xl glass border border-[#1e1e1f]"
                role="button"
                aria-expanded={isOpen}
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-gradient-to-tr from-[#7e30e1]/12 to-[#b364ff]/8">
                    <Icon className="w-6 h-6 text-[#b364ff]" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-lg">{cap.title}</h3>
                      <span className="text-xs px-2 py-1 rounded-md bg-[#111115] text-[#cfcfcf]">
                        {cap.short}
                      </span>
                    </div>
                    <p className="text-sm text-[#bfbfbf] mt-2">{cap.blurb}</p>

                    <div className="mt-4 flex items-center justify-between">
                      <div className="text-xs text-[#9fb0ff]">Learn more →</div>
                      <div className="text-xs text-[#9fbfbf]">Group: {cap.group}</div>
                    </div>
                  </div>
                </div>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25 }}
                      className="mt-4 pt-4 border-t border-[#151515] text-sm text-[#cfcfcf]"
                    >
                      <div className="mb-3">{cap.details}</div>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            alert(`Dry-run for: ${cap.title}`);
                          }}
                          className="px-3 py-2 rounded-md bg-[#7e30e1] text-white text-sm"
                        >
                          Dry-run
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            alert(`Request approval for: ${cap.title}`);
                          }}
                          className="px-3 py-2 text-sm rounded-md border border-[#2a2a2a] hover:bg-white/5"
                        >
                          Request Approval
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            alert(`Open evidence viewer (stub) for: ${cap.title}`);
                          }}
                          className="ml-auto text-xs text-[#bfbfbf] underline"
                        >
                          Open evidence
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.article>
            );
          })}
        </div>

        <div className="mt-8 text-sm text-[#9fbfbf]">
          Tip: click any capability to expand details and run a dry-run or request approval.
        </div>
      </div>
    </section>
  );
}
