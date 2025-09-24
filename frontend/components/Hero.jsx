// frontend/components/Hero.jsx
"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import StarsBG from "./StarsBG";

export default function Hero() {
  const scrollToServices = () => {
    const el = document.getElementById("services");
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 pt-28 bg-[#050508]"
    >
      {/* Stars background (z-0) */}
      <StarsBG count={160} parallax={true} />

      {/* subtle overlay between stars and content */}
      <div className="pointer-events-none absolute inset-0 z-5 bg-gradient-to-b from-transparent via-black/30 to-black/60" />

      {/* main content (z-10 ensures it sits above canvas & overlay) */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9 }}
        className="relative z-10 max-w-5xl text-center"
      >
        <h1 className="text-4xl sm:text-6xl font-extrabold leading-tight">
          CyberFluxAI{" "}
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-[#7e30e1] to-[#2bd4ff]">
            GenAI for Explainable Incident Response
          </span>
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="text-[#cfcfcf] mt-6 max-w-3xl mx-auto"
        >
          Turn alerts into defensible actions. Ingest telemetry, reason with GenAI over
          policy and playbooks, execute guard-railed automation, and produce auditable
          evidence-backed reports — all while keeping humans in the loop.
        </motion.p>

        <div className="mt-8 flex items-center justify-center gap-4">
          <Link href="/demo">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white shadow-lg"
            >
              Try the Demo
            </motion.button>
          </Link>

          <motion.button
            onClick={scrollToServices}
            whileHover={{ scale: 1.02 }}
            className="px-6 py-3 rounded-xl border border-[#333] text-[#bfbfbf] bg-black/40"
          >
            Explore Capabilities
          </motion.button>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mt-10 inline-grid grid-cols-3 gap-3 text-sm text-[#cfcfcf]"
        >
          <div className="glass p-3 rounded-lg shadow-sm">
            <div className="text-xs text-[#9fb0ff]">Ingest</div>
            <div className="font-semibold">Telemetry</div>
            <div className="text-xs mt-1 text-[#bfbfbf]">Endpoints · IdP · Cloud</div>
          </div>
          <div className="glass p-3 rounded-lg shadow-sm">
            <div className="text-xs text-[#9fb0ff]">Reason</div>
            <div className="font-semibold">GenAI Planner</div>
            <div className="text-xs mt-1 text-[#bfbfbf]">Action proposals · rollback</div>
          </div>
          <div className="glass p-3 rounded-lg shadow-sm">
            <div className="text-xs text-[#9fb0ff]">Govern</div>
            <div className="font-semibold">Policy-as-Code</div>
            <div className="text-xs mt-1 text-[#bfbfbf]">Approval tiers · auditable logs</div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}
