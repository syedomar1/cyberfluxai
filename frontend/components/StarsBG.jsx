// frontend/components/StarsBG.jsx
"use client";

import { useEffect, useRef } from "react";

/**
 * StarsBG - high-DPI safe canvas starfield with parallax and cleanup.
 * Use <StarsBG count={160} parallax={true} /> inside a client-side component.
 */

export default function StarsBG({ count = 160, parallax = true }) {
  const canvasRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;

    const setSize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    setSize();

    const stars = Array.from({ length: count }).map(() => ({
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 1.6 + 0.4,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      opacity: Math.random() * 0.85 + 0.15,
    }));

    let mouseX = width / 2;
    let mouseY = height / 2;

    const onMove = (ev) => {
      if (!parallax) return;
      mouseX = ev.clientX;
      mouseY = ev.clientY;
    };

    const onResize = () => {
      setSize();
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("resize", onResize);

    function draw() {
      ctx.clearRect(0, 0, width, height);

      // faint gradient so stars are visible on very dark backgrounds
      const g = ctx.createLinearGradient(0, 0, width, height);
      g.addColorStop(0, "rgba(126,48,225,0.02)");
      g.addColorStop(1, "rgba(43,212,255,0.02)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, width, height);

      for (const s of stars) {
        const shiftX = parallax ? (mouseX - width / 2) * (s.r / 140) : 0;
        const shiftY = parallax ? (mouseY - height / 2) * (s.r / 140) : 0;

        ctx.beginPath();
        ctx.arc(s.x + shiftX, s.y + shiftY, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${s.opacity})`;
        ctx.fill();

        s.x += s.vx;
        s.y += s.vy;

        // wrap-around
        if (s.x < -10) s.x = width + 10;
        if (s.x > width + 10) s.x = -10;
        if (s.y < -10) s.y = height + 10;
        if (s.y > height + 10) s.y = -10;
      }

      rafRef.current = requestAnimationFrame(draw);
    }

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize", onResize);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [count, parallax]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 w-full h-full z-0"
      style={{ transform: "translateZ(0)" }}
    />
  );
}
