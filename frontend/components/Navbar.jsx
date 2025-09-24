// frontend/components/Navbar.jsx
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  // close mobile menu on resize to desktop
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) setOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <nav className="w-full fixed top-0 left-0 z-40 bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff]">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M2 12h20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M12 2v20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <span className="font-semibold text-lg text-white">CyberFluxAI</span>
            </Link>
          </div>

          {/* desktop links */}
          <div className="hidden md:flex items-center space-x-6 text-sm text-[#bfbfbf]">
            <a href="#hero" className="hover:text-white">Home</a>
            <a href="#news" className="hover:text-white">Simulations</a>
            <a href="#services" className="hover:text-white">Capabilities</a>
            <a href="#contact" className="hover:text-white">Contact</a>
            <Link href="/demo">
              <button className="bg-[#7e30e1] px-4 py-2 rounded-lg text-white">Demo</button>
            </Link>
          </div>

          {/* mobile hamburger */}
          <div className="md:hidden">
            <button
              aria-label="Toggle menu"
              onClick={() => setOpen((s) => !s)}
              className="p-2 rounded-md inline-flex items-center justify-center bg-black/30 hover:bg-black/40"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-white">
                {open ? (
                  <path d="M6 18L18 6M6 6l12 12" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                ) : (
                  <>
                    <path d="M3 7h18" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M3 12h18" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M3 17h18" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* mobile menu panel */}
      <div
        className={`md:hidden transition-max-h duration-300 ease-in-out overflow-hidden ${
          open ? "max-h-60" : "max-h-0"
        }`}
      >
        <div className="px-4 pb-4 pt-2 space-y-2 bg-[#06060a]/80 backdrop-blur-sm">
          <a href="#hero" onClick={() => setOpen(false)} className="block px-3 py-2 rounded-md text-base text-[#e6e6e6]">Home</a>
          <a href="#news" onClick={() => setOpen(false)} className="block px-3 py-2 rounded-md text-base text-[#e6e6e6]">Simulations</a>
          <a href="#services" onClick={() => setOpen(false)} className="block px-3 py-2 rounded-md text-base text-[#e6e6e6]">Capabilities</a>
          <a href="#contact" onClick={() => setOpen(false)} className="block px-3 py-2 rounded-md text-base text-[#e6e6e6]">Contact</a>
          <Link href="/demo">
            <button onClick={() => setOpen(false)} className="w-full mt-1 bg-[#7e30e1] px-4 py-2 rounded-lg text-white">Demo</button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
