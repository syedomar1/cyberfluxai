// frontend/pages/index.jsx
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import News from "@/components/News";
import Services from "@/components/Services";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#050508] text-white">
      <Navbar />
      <Hero />
      <News />
      <Services />
      <Footer />
    </div>
  );
}
