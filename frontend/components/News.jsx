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
        const r = await axios.get("/api/fluxsim");
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
    <section id="news" className="relative py-24 px-6 bg-[#06060a] scroll-mt-24">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold mb-6">Simulated Incidents (FluxSim)</h2>
        <p className="text-sm text-[#bdbdbd] mb-8">Sample multi-stage incidents used to evaluate planning and explanation quality.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {loading ? <div className="col-span-full text-[#a9a9a9]">Loading simulations…</div> : incidents.length === 0 ? <div className="col-span-full text-[#a9a9a9]">No simulations available.</div> : incidents.map((inc, i) => <ActionCard key={i} incident={inc} />)}
        </div>
      </div>
    </section>
  );
}
