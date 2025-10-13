// frontend/pages/_app.jsx
import "@/styles/globals.css";
import Navbar from "../components/Navbar";

export default function App({ Component, pageProps }) {
  return (
    <>
      <Navbar />
      {/* Add top padding so page content doesn't hide behind fixed navbar */}
      <div style={{ paddingTop: 64 }}>
        <Component {...pageProps} />
      </div>
    </>
  );
}
