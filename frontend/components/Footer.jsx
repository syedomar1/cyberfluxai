export default function Footer() {
  return (
    <footer id="contact" className="py-8 border-t border-[#121212] mt-16">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-sm text-[#bfbfbf]">© {new Date().getFullYear()} CyberFluxAI</div>
        <div className="text-sm text-[#bfbfbf]">Built for SOCs — evidence-first automation</div>
      </div>
    </footer>
  );
}
