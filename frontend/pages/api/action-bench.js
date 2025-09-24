export default function handler(req, res) {
  if (req.method === "POST") {
    const payload = req.body || {};
    return res.status(200).json({ status: "ok", saved: true, result: payload });
  }
  return res.status(200).json({ status: "ready" });
}
