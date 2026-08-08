# PC Slowdown Diagnoser

> A lightweight, privacy-first diagnostic tool that scans Windows system performance, identifies bottlenecks using a deterministic rules engine, and delivers plain-English fixes powered by Gemini AI.

---

## 💡 Core Principle

**The AI does NOT diagnose your computer.** 

Diagnosis is performed entirely by a 100% deterministic Python rules engine (fast, free, reproducible, and zero-hallucination). The Gemini LLM is called **only as a final step** to rephrase technical evidence into friendly, non-technical actions for everyday users.

---

## 🏗️ Architecture

```
┌────────────────────┐      JSON       ┌────────────────────┐
│ Collector Script   │───────────────> │  FastAPI Backend   │
│ (Python / psutil)  │                 │    (Port 8000)     │
└────────────────────┘                 └─────────┬──────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │ Deterministic Rules│
                                       │ Engine (15 rules)  │
                                       └─────────┬──────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │ Gemini 2.5 Flash   │
                                       │ (Plain-English)    │
                                       └─────────┬──────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │ Next.js 15 Web UI  │
                                       │ (Port 3000)        │
                                       └────────────────────┘
```

---

## ✨ Features

- **Local Telemetry Collector**: Scans CPU, RAM usage, disk space & speed, autostart programs, system uptime, and runaway background processes without sending raw telemetry over the network.
- **15 Deterministic Diagnostic Rules**: Evaluates memory pressure, thermal throttling, spinning HDDs vs SSDs, excessive startup apps, pending Windows updates, and long system uptimes.
- **AI Plain-English Rewriter**: Translates raw hardware metrics into clear, 1-2 sentence recommended fixes.
- **Doctor's Diagnostic Report UI**: A clean, scannable, near-white interface designed like an authoritative medical report — no flashy cards, glowing neon badges, or marketing clutter.
- **Graceful Degradation**: If no AI key is configured or the LLM API is unreachable, the system automatically falls back to raw rules engine outputs.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- (Optional) **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation

Clone the repository:
```bash
git clone https://github.com/H31S3NB3R4/PC-Slowdown-Diagnoser.git
cd PC-Slowdown-Diagnoser
```

Set up python dependencies & environment variables:
```bash
pip install -r backend/requirements.txt -r collector/requirements.txt
```

Create a `.env` file inside `backend/`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Generate Telemetry Report
Run the collector script on your Windows PC:
```bash
python collector/collect.py
```
This generates a local `report.json` file.

### 4. Start Backend API
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000`.

### 5. Start Frontend UI
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser. Drag and drop your `report.json` (or click one of the preset demo reports) to view your diagnostic findings.

---

## 📁 Repository Structure

```
.
├── collector/
│   ├── collect.py         # Windows hardware & OS telemetry collector
│   ├── sample_output.json # Sample JSON telemetry fixture
│   └── requirements.txt
├── rules_engine/
│   ├── engine.py          # Pure Python deterministic rules engine (15 rules)
│   └── fixtures/          # Test fixtures (healthy, low RAM, full disk)
├── backend/
│   ├── main.py            # FastAPI API server (POST /diagnose)
│   ├── llm_rewriter.py    # Gemini 2.5 Flash plain-English rewrite step
│   └── requirements.txt
├── frontend/              # Next.js 15 + Tailwind CSS minimal diagnostic UI
│   ├── app/               # App router pages & layouts
│   ├── components/        # Diagnostic report components
│   └── lib/               # Types, API helpers, & sample demo reports
└── PROJECT_SPEC.md        # Technical specification & build guidelines
```

---

## 🛡️ License

MIT License. Designed for simplicity, speed, and privacy.
