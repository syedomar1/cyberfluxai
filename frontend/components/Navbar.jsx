"use client";
import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="w-full fixed top-0 left-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3">
          <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff]">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="text-white">
              <path d="M2 12h20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M12 2v20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <span className="font-semibold text-lg">CyberFluxAI</span>
        </Link>

        <div className="hidden md:flex items-center space-x-6 text-sm text-[#bfbfbf]">
          <a href="#hero" className="hover:text-white">Home</a>
          <a href="#news" className="hover:text-white">Simulations</a>
          <a href="#services" className="hover:text-white">Capabilities</a>
          <a href="#contact" className="hover:text-white">Contact</a>
          <Link href="/demo">
            <button className="bg-[#7e30e1] px-4 py-2 rounded-lg text-white">Demo</button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
