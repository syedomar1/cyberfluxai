// pages/api/report/direct.js
import { Buffer } from "buffer";

/**
 * Proxy endpoint that forwards a request to the backend /report/direct
 * - frontend calls this at /api/report/direct?csv=logs.csv&include_ai=true
 * - the server-side code forwards to BACKEND_URL/report/direct?...
 *
 * Environment variables:
 * - BACKEND_URL (server-side, recommended for Vercel)
 * - NEXT_PUBLIC_BACKEND_URL (optional, fallback for local dev)
 *
 * NOTE: On Vercel set BACKEND_URL to your ngrok https://... or your deployed backend URL.
 */

export default async function handler(req, res) {
  // Read query params
  const { csv = "logs.csv", include_ai = "true", nrows } = req.query;

  // Prefer server-side env var BACKEND_URL (set in Vercel).
  // If not present, allow NEXT_PUBLIC_BACKEND_URL (useful for local dev without adding server env),
  // else fallback to localhost (use while running backend locally).
  const BACKEND_BASE =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://127.0.0.1:8001";

  // Build backend URL
  const params = new URLSearchParams();
  params.set("csv", csv);
  params.set("include_ai", include_ai);
  if (nrows) params.set("nrows", String(nrows));

  const backendUrl = `${BACKEND_BASE.replace(
    /\/$/,
    ""
  )}/report/direct?${params.toString()}`;

  try {
    console.log("[proxy] forwarding to backend:", backendUrl);

    const backendResp = await fetch(backendUrl, {
      method: "GET",
      headers: {
        Accept: "application/pdf, application/json, */*",
      },
    });

    if (!backendResp.ok) {
      const txt = await backendResp.text().catch(() => "");
      console.error(
        "[proxy] backend non-ok:",
        backendResp.status,
        txt.slice(0, 800)
      );
      return res.status(502).json({
        error: "Backend responded with error",
        status: backendResp.status,
        body: txt,
      });
    }

    const arrayBuffer = await backendResp.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // Try to extract filename from backend response
    const contentDisp = backendResp.headers.get("content-disposition") || "";
    let filename = "cyberflux_report.pdf";
    const m = /filename="?([^"]+)"?/.exec(contentDisp);
    if (m && m[1]) filename = m[1];

    // Forward headers/content back to client
    res.setHeader(
      "Content-Type",
      backendResp.headers.get("content-type") || "application/pdf"
    );
    res.setHeader("Content-Length", String(buffer.length));
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);

    return res.status(200).send(buffer);
  } catch (err) {
    console.error("[proxy] error calling backend:", String(err));
    return res.status(500).json({ error: "Proxy error", detail: String(err) });
  }
}
