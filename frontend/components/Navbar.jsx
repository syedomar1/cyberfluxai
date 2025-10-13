// frontend/components/Navbar.jsx
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";

/**
 * Navbar with:
 * - anchor links to sections on the main page (#hero, #news, #services, #contact)
 * - "Demo" button that links to /demo
 * - "Analyzer" link that goes to /analyzer
 *
 * Behavior:
 * - If user is already on "/", clicking an anchor will scroll smoothly to that section if present.
 * - If user is on any other route, clicking an anchor pushes a navigation to "/#section".
 */

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  // close mobile menu on resize to desktop
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 768) setOpen(false);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // helper to navigate to a hash on the main page
  const goToSection = (hash) => {
    setOpen(false); // close mobile if open

    // If already on the home page, attempt smooth scroll to element
    if (router.pathname === "/") {
      // use setTimeout to allow hash updates and ensure element exists
      const id = hash.replace("#", "");
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        // update URL hash without reloading
        history.replaceState(null, "", hash);
        return;
      }
      // fallback: just update location hash
      location.hash = hash;
      return;
    }

    // If not on home page, navigate to home with the hash
    router.push("/" + hash).catch((_) => {
      // On failure, do a normal navigation
      window.location.href = "/" + hash;
    });
  };

  return (
    <nav className="w-full fixed top-0 left-0 z-40 bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-gradient-to-r from-[#7e30e1] to-[#b364ff]">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path d="M2 12h20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M12 2v20" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
              <span className="font-semibold text-lg text-white">CyberFluxAI</span>
            </Link>
          </div>

          {/* desktop links */}
          <div className="hidden md:flex items-center space-x-6 text-sm text-[#bfbfbf]">
            <button onClick={() => goToSection("#hero")} className="hover:text-white">Home</button>
            <button onClick={() => goToSection("#news")} className="hover:text-white">Simulations</button>
            <button onClick={() => goToSection("#services")} className="hover:text-white">Capabilities</button>
            <button onClick={() => goToSection("#contact")} className="hover:text-white">Contact</button>

            <Link href="/analyzer" legacyBehavior>
              <a className="hover:text-white">Analyzer</a>
            </Link>

            <Link href="/demo" legacyBehavior>
              <a>
                <button className="bg-[#7e30e1] px-4 py-2 rounded-lg text-white">Demo</button>
              </a>
            </Link>
          </div>

          {/* mobile hamburger */}
          <div className="md:hidden">
            <button
              aria-label="Toggle menu"
              onClick={() => setOpen((s) => !s)}
              className="p-2 rounded-md inline-flex items-center justify-center bg-black/30 hover:bg-black/40"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-white" aria-hidden>
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
          <button onClick={() => goToSection("#hero")} className="block w-full text-left px-3 py-2 rounded-md text-base text-[#e6e6e6]">Home</button>
          <button onClick={() => goToSection("#news")} className="block w-full text-left px-3 py-2 rounded-md text-base text-[#e6e6e6]">Simulations</button>
          <button onClick={() => goToSection("#services")} className="block w-full text-left px-3 py-2 rounded-md text-base text-[#e6e6e6]">Capabilities</button>
          <button onClick={() => goToSection("#contact")} className="block w-full text-left px-3 py-2 rounded-md text-base text-[#e6e6e6]">Contact</button>

          <Link href="/analyzer" legacyBehavior>
            <a onClick={() => setOpen(false)} className="block px-3 py-2 rounded-md text-base text-[#e6e6e6]">Analyzer</a>
          </Link>

          <Link href="/demo" legacyBehavior>
            <a onClick={() => setOpen(false)}>
              <button className="w-full mt-1 bg-[#7e30e1] px-4 py-2 rounded-lg text-white">Demo</button>
            </a>
          </Link>
        </div>
      </div>
    </nav>
  );
}
