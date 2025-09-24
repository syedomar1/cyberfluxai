// frontend/components/Hero.jsx
"use client";

import { useRouter } from "next/navigation"; // Next 13 app/router; if pages-router use 'next/router'
import { motion } from "framer-motion";
import StarsBG from "./StarsBG";

export default function Hero() {
  const router = useRouter();

  const goToDemo = (e) => {
    e.preventDefault();
    // programmatic navigation
    router.push("/demo");
  };

  const scrollToServices = () => {
    const el = document.getElementById("services");
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section
      id="hero"
      className="relative min-h-[75vh] md:min-h-screen flex items-center justify-center overflow-hidden px-6 pt-20 md:pt-28 bg-[#050508] scroll-mt-20"
    >
      {/* Stars background (z-0) */}
      <StarsBG count={120} parallax={true} />

      {/* subtle overlay so stars don't steal contrast */}
      <div className="pointer-events-none absolute inset-0 z-0 bg-gradient-to-b from-transparent via-black/20 to-black/60" />

      {/* main content (z-10 ensures it sits above canvas & overlay) */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9 }}
        className="relative z-10 max-w-4xl text-center"
      >
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight">
          CyberFluxAI
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-[#7e30e1] to-[#2bd4ff] mt-2 sm:mt-3 text-lg sm:text-2xl md:text-3xl">
            GenAI for Explainable Incident Response
          </span>
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12 }}
          className="text-[#cfcfcf] mt-5 md:mt-6 text-sm sm:text-base md:text-lg mx-auto max-w-3xl"
        >
          Turn alerts into defensible actions. Ingest telemetry, reason with GenAI over
          policy and playbooks, execute guard-railed automation, and produce auditable
          evidence-backed reports — all while keeping humans in the loop.
        </motion.p>

        <div className="mt-6 md:mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
          {/* motion.button (no nested anchors) */}
          <motion.button
            type="button"
            onClick={goToDemo}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full sm:w-auto text-center px-5 py-3 rounded-xl bg-gradient-to-r from-[#7e30e1] to-[#b364ff] text-white shadow-lg"
            aria-label="Open demo"
          >
            Try the Demo
          </motion.button>

          <motion.button
            type="button"
            onClick={scrollToServices}
            whileHover={{ scale: 1.02 }}
            className="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#333] text-[#bfbfbf] bg-black/40"
            aria-label="Explore capabilities"
          >
            Explore Capabilities
          </motion.button>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-6 md:mt-10 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm text-[#cfcfcf]"
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
