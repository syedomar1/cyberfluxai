// frontend/components/Footer.jsx
"use client";

export default function Footer() {
  return (
    <footer id="contact" className="py-8 px-4 bg-[#050507] text-[#bfbfbf] mt-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="font-semibold text-white">CyberFluxAI</div>
          <div className="text-xs mt-1">Explainable, auditable incident response.</div>
        </div>

        <div className="text-sm text-[#9fbfbf]">
          © {new Date().getFullYear()} CyberFluxAI — Built for research & demo use
        </div>
      </div>
    </footer>
  );
}
