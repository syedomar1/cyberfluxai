// pages/api/report/direct.js
import { Buffer } from "buffer";

export default async function handler(req, res) {
  const { csv = "logs.csv", include_ai = "true", nrows } = req.query;

  // Backend base URL. Override in Vercel with NEXT_PUBLIC_BACKEND_URL env var
  const BACKEND_BASE =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8001";

  const params = new URLSearchParams();
  params.set("csv", csv);
  params.set("include_ai", include_ai);
  if (nrows) params.set("nrows", String(nrows));

  const backendUrl = `${BACKEND_BASE}/report/direct?${params.toString()}`;

  try {
    const backendResp = await fetch(backendUrl, {
      method: "GET",
    });

    if (!backendResp.ok) {
      const txt = await backendResp.text().catch(() => "");
      console.error("[proxy] backend non-ok:", backendResp.status, txt);
      return res
        .status(502)
        .json({
          error: "Backend responded with error",
          status: backendResp.status,
          body: txt,
        });
    }

    const arrayBuffer = await backendResp.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // try to detect filename
    const contentDisp = backendResp.headers.get("content-disposition") || "";
    let filename = "cyberflux_report.pdf";
    const m = /filename="?([^"]+)"?/.exec(contentDisp);
    if (m && m[1]) filename = m[1];

    res.setHeader("Content-Type", "application/pdf");
    res.setHeader("Content-Length", String(buffer.length));
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);

    return res.status(200).send(buffer);
  } catch (err) {
    console.error("[proxy] error calling backend:", err);
    return res.status(500).json({ error: "Proxy error", detail: String(err) });
  }
}
