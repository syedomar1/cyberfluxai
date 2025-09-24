// frontend/components/News.jsx
"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import ActionCard from "./ActionCard";

export default function News() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        // if you don't have backend yet, this will return 404 — handle gracefully
        const r = await axios.get("/api/fluxsim").catch(() => ({ data: { incidents: [] } }));
        setIncidents(r.data.incidents || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  return (
    <section id="news" className="relative py-12 md:py-20 px-4 md:px-6 bg-[#06060a] scroll-mt-24">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold mb-3">Simulated Incidents (FluxSim)</h2>
        <p className="text-sm md:text-base text-[#bdbdbd] mb-6">Sample multi-stage incidents used to evaluate planning and explanation quality.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {loading ? (
            <div className="col-span-full text-[#a9a9a9]">Loading simulations…</div>
          ) : incidents.length === 0 ? (
            <div className="col-span-full text-[#a9a9a9]">No simulations available.</div>
          ) : (
            incidents.map((inc, i) => <ActionCard key={i} incident={inc} />)
          )}
        </div>
      </div>
    </section>
  );
}
