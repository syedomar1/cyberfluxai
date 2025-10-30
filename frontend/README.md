# CyberFluxAI – Frontend Report & LLM Integration Dashboard

A production-ready **frontend dashboard** for **automated cybersecurity reporting**, **explainable AI (XAI) insights**, and **interactive Q&A analysis** on log and threat datasets.  
Built with **Next.js, TypeScript, TailwindCSS, and shadcn/ui**, this frontend demonstrates real-time explainability, large language model (LLM) integration, and faithfulness-driven analysis visualization.

---

## Live Deployment

- **Frontend App:** [https://cyberfluxai.vercel.app/](https://cyberfluxai.vercel.app/)

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [Workflow](#workflow)  
4. [Usage Guide](#usage-guide)  
5. [Explainability Dashboard](#explainability-dashboard)  
6. [Architecture & Project Structure](#architecture--project-structure)  
7. [Technology Stack](#technology-stack)  
8. [Local Quickstart](#local-quickstart)  
9. [Production Build](#production-build)  
10. [Notes](#notes)

---

## Project Overview

**CyberFluxAI Frontend** is an advanced dashboard built to visualize and interact with AI-driven cybersecurity analytics.  
It bridges **backend LLM agents**, **XAI explainers**, and **automated reporting engines** into a unified, human-centric interface.

The system provides analysts with:
- Auto-generated **incident reports** via LLM reasoning.  
- **Explainable charts** and SHAP/LIME plots for feature interpretation.  
- **Interactive chatbot** capable of contextual Q&A over the analyzed dataset.  
- Real-time **faithfulness verification** and **risk scoring overlays**.

---

## Features

| Feature | Description |
| :------- | :----------- |
| **Automated Report Generation** | Converts AI detection logs into human-readable summaries using Gemini LLM APIs. |
| **Explainability Dashboard** | Interactive SHAP/LIME visualization to interpret model reasoning. |
| **Faithfulness Verification** | Ensures that generated explanations are logically aligned with actual model behavior. |
| **Chatbot (Q&A on Dataset)** | Conversational agent powered by retrieval-augmented LLM (RAG) for dataset-level insights. |
| **Real-Time Risk Visualization** | Graph-based representation of anomaly patterns and blocked IPs. |
| **Dark/Light Mode UI** | Clean, adaptive interface with persistent theme memory. |
| **Secure API Connectivity** | Seamless integration with FastAPI backend for report and audit retrieval. |

---

## Workflow

The application frontend serves as the **analyst’s workspace** for CyberFluxAI’s pipeline.  
1. Logs are processed and scored in the backend (FastAPI).  
2. Detected anomalies are summarized by LLMs (Gemini / OpenAI).  
3. Explainability metrics are computed (SHAP, LIME).  
4. Frontend visualizes:  
   - Incident report cards  
   - Feature contribution plots  
   - Chatbot for dataset Q&A  
   - Faithfulness metrics table  

---

## Usage Guide

### Home (`/`)
- Overview of system functionality and current AI insights.

### Chatbot (`/analyzer`)
- Query any dataset entry, model behavior, or AI-generated report section.
- View generated incident summaries and their explainability metrics.

---

## Explainability Dashboard

The **Explainability Dashboard** integrates SHAP and LIME visual plots, overlaid with **faithfulness validation markers**.  
Each feature’s contribution is interactively displayed, allowing users to:  
- Hover for value contribution  
- Compare model vs. explanation alignment  
- Export explanations as `.png` or `.json`  

Faithfulness metrics (cosine similarity, KL-divergence, fidelity scores) are rendered dynamically with adjustable thresholds.

---

## Architecture & Project Structure

```
├── public
│   ├── favicon.ico
│   └── logo.svg
├── src
│   ├── components
│   │   ├── ReportCard.tsx
│   │   ├── XAIVisualizer.tsx
│   │   ├── FaithfulnessMeter.tsx
│   │   ├── ChatAgent.tsx
│   │   └── ui/ [...shadcn components]
│   ├── pages
│   │   ├── index.tsx
│   │   ├── reports.tsx
│   │   ├── xai.tsx
│   │   ├── chat.tsx
│   │   └── audit.tsx
│   ├── hooks/ [...custom data fetchers]
│   ├── lib/ [api.ts, constants.ts]
│   └── styles/
│       └── globals.css
├── tailwind.config.ts
├── next.config.js
├── package.json
├── tsconfig.json
└── README.md
```

---

## Technology Stack

| Layer | Technology |
| :----- | :---------- |
| **Framework** | Next.js 14 |
| **Language** | TypeScript |
| **Styling** | TailwindCSS + shadcn/ui |
| **Charts & Visualization** | Recharts + Framer Motion |
| **Explainability Libraries** | SHAP.js, LIME.js (custom visualizations) |
| **LLM Interface** | OpenAI API / Gemini API |
| **Data Source** | REST (FastAPI backend) |

---

## Local Quickstart

### Prerequisites
- Node.js v18+  
- npm v9+ or yarn v1.22+

### Run Locally
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```
Then visit [http://localhost:3000](http://localhost:3000)

---

## Production Build

```bash
npm run build
npm run start
```

Optimized output will be served from `.next/` directory.

---

## Notes

- The dashboard is modular — each section (XAI, LLM, Chatbot) can be independently deployed.  
- Faithfulness computation visualized on frontend but processed server-side.  
- Default dark mode is designed for SOC and low-light analyst environments.  
- All visual analytics are client-side rendered for maximum responsiveness.

---

© 2025 CyberFluxAI. All rights reserved.
