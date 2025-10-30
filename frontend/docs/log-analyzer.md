# Network Log Analyzer – How It Works

This document explains the end-to-end flow of the analyzer UI: from user input (CSV upload), through client-side parsing and summarization, to Gemini inference for both the initial report and interactive chat.

## High-level Flow

1. User opens `/analyzer`.
2. User uploads a CSV of network logs.
3. The browser parses the CSV (no server involved).
4. A compact sample is generated to fit in a prompt.
5. The browser calls Gemini’s GenerateContent REST API with a cybersecurity analysis prompt and the sampled logs.
6. The returned Markdown report is displayed.
7. User can ask follow-up questions; the app sends the report + sample + question to Gemini and renders the answer.

## Components and Files

- Page: `pages/analyzer.jsx`
- UI Atoms reused: `components/StarsBG.jsx` (background)
- CSV parsing: [`papaparse`](https://www.papaparse.com/)
- Markdown rendering: `react-markdown` with `remark-gfm`

## Input: CSV Upload (Client-only)

- The file input accepts `.csv` files. On selection, the file is parsed entirely in the browser using Papa.parse with `header: true` and `skipEmptyLines: true`.
- A lightweight preview table shows the first rows and detected column headers.

## Parsing and Sampling

- After parsing, the app keeps an in-memory array of row objects and a list of column headers.
- To respect token limits, it builds a compact sample string:
  - Picks up to ~60 rows from the start (configurable) and re-serializes them as `CSV` text.
  - Includes a header line (comma-separated column names) followed by sampled rows.

## Prompt Construction (Report Generation)

- The app constructs a structured prompt instructing Gemini to behave like a senior cybersecurity analyst and to produce a report with:
  - Executive summary
  - Key findings (ranked)
  - Evidence snippets (with fields)
  - Likely root cause and kill chain mapping
  - Recommended remediation (prioritized)
  - Residual risks and monitoring follow-ups
- The sampled CSV text is appended to the prompt.

## Direct REST Call to Gemini

- The page uses a small helper `callGeminiGenerateContent(contents)` which makes a `POST` request to the Generative Language API GenerateContent endpoint.
- Endpoint shape (v1/v1beta differ by path – ensure model, version, and key match what your account supports):
  - `POST https://generativelanguage.googleapis.com/v1/models/{MODEL_ID}:generateContent?key={API_KEY}`
  - or `POST .../v1beta/models/{MODEL_ID}:generateContent?...`
- Request body uses the `contents` format:

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "<your full prompt + logs sample>" }]
    }
  ]
}
```

- The response is parsed from `candidates[0].content.parts[].text` and concatenated as the final Markdown string.

## Rendering the Report

- The Markdown report is displayed with `ReactMarkdown` and `remark-gfm`, wrapped in a styled container (Tailwind classes are applied to the container, not the `<ReactMarkdown/>` itself).

## Chat Over the Report

- After a report is generated, the user can ask follow-up questions.
- The app builds a compact context containing:
  - A system-style instruction reminding the model to reference the existing report and logs
  - The previously generated report
  - The sampled CSV text
- It sends a new `contents` array to Gemini with the context and the user’s `Question: ...` appended.
- The answer (Markdown) is rendered the same way as the report.

## Environment and Keys

- The app is designed to read the API key from `NEXT_PUBLIC_GEMINI_API_KEY` in `.env.local` under `frontend/`.
- As this is a browser app, the key is exposed to the client. Use a scoped key and apply Google Cloud restrictions where possible.

## Error Handling

- Upload/parse errors are surfaced beneath the file input.
- Gemini call errors include the HTTP status text/body where available.
- The UI disables buttons while generation is in progress to prevent duplicate requests.

## Limits and Considerations

- Sampling is intentionally conservative (first ~60 rows) to keep prompts small. Increase cautiously; larger prompts may hit model limits or slow responses.
- Consider client-side redaction of sensitive values before sending to Gemini.
- Long-term, you can move calls server-side to protect keys and implement more advanced retrieval (e.g., chunking + embeddings).

## Extensibility Ideas

- Add schema detection and field mapping (e.g., timestamp, src_ip, dst_ip, action, user).
- Compute quick metrics client-side (top talkers, uncommon ports) and include them in the prompt.
- Add presets for different telemetry sources (firewall, proxy, EDR, auth logs).
- Add download/export of the generated report as Markdown or PDF.



