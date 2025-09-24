export default function handler(req, res) {
  const incidents = [
    {
      id: "inc-001",
      title: "Suspicious Token Use — Geo Anomaly",
      summary: "Privileged token used from a new country minutes after reset.",
      severity: "High",
      proposed_action: {
        title: "Quarantine endpoint & revoke token (30m)",
        description: "Isolate host and revoke token.",
      },
      evidence: [
        {
          time: "2025-09-20T08:14:22Z",
          source: "IdP",
          line: "Token for alice@acme.com from IP 195.12.4.8",
        },
        {
          time: "2025-09-20T08:16:05Z",
          source: "EDR",
          line: "powershell.exe spawned rclone — outbound transfer",
        },
        {
          time: "2025-09-20T08:16:40Z",
          source: "Gateway",
          line: "TLS to newly-registered domain exfil-123.online",
        },
      ],
    },
    {
      id: "inc-002",
      title: "Lateral Movement Attempt",
      summary:
        "Host attempted multiple authentications to servers after credential access.",
      severity: "Medium",
      proposed_action: {
        title: "Block lateral traffic; snapshot host",
        description: "Block traffic and take forensic snapshot.",
      },
      evidence: [
        {
          time: "2025-09-18T02:12:33Z",
          source: "EDR",
          line: "Multiple SMB connections to DB subnet",
        },
        {
          time: "2025-09-18T02:13:01Z",
          source: "Sysmon",
          line: "Privilege escalation: new service 'svcex' installed",
        },
      ],
    },
  ];
  res.status(200).json({ incidents });
}
