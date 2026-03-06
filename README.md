<div align="center">

# 🔍 DRISHTI AI

### AI-Generated Content & Deepfake Detection Platform

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js)](https://nextjs.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-EfficientNet--B4-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-F55036)](https://groq.com)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-4581C3?logo=neo4j&logoColor=white)](https://neo4j.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Upload any image, audio, video, or text — DRISHTI tells you if it's real or AI-generated, with a confidence score and a plain-English explanation.**

[Live Demo](#quick-start) · [Features](#-what-can-drishti-do) · [How It Works](#-how-it-works-under-the-hood) · [Setup Guide](#-getting-started)

</div>

---

## 🤔 What Problem Does This Solve?

AI-generated content (deepfakes, AI images, cloned voices, ChatGPT text) is becoming nearly impossible for humans to spot. This leads to:

- 📰 **Misinformation** — fake news with AI-generated images
- 📞 **Scams** — voice clones used in phone fraud
- 📝 **Academic fraud** — AI-written assignments and papers
- 🎭 **Identity theft** — deepfake videos impersonating real people

**DRISHTI** is a one-stop detection platform that analyzes content across all four media types and gives you a clear, honest answer — not just "real or fake", but a **confidence percentage** with a **detailed explanation** of what it found.

---

## ✨ What Can DRISHTI Do?

| Media Type | What It Detects | How |
|:---:|---|---|
| 🖼️ **Images** | AI-generated images, GAN artifacts, deepfake faces | Custom-trained EfficientNet-B4 neural network (trained on 100k+ images) |
| 🎙️ **Audio** | Cloned voices, AI-synthesized speech, voice phishing | Pitch analysis, Zero-Crossing Rate, phase detection + Resemble AI |
| 📝 **Text** | ChatGPT/LLM-generated text, AI essays | RoBERTa + Winston AI + Sapling AI ensemble with sentence-level heatmap |
| 🎥 **Video** | Deepfake videos, face swaps, AI-generated video | Frame-by-frame extraction + temporal consistency analysis |

### Bonus Features

- 🧠 **AI Explanations** — Every scan comes with a plain-English explanation (powered by Groq LLaMA 3.3) that tells you *why* DRISHTI thinks content is real or fake
- 📊 **Confidence Scores** — No binary "yes/no" — you get a percentage (e.g., "78% likely AI-generated") so you can make your own judgment
- 🔗 **Threat Intelligence** — Neo4j graph database connects related scans to identify recurring deepfake patterns
- 🌐 **Chrome Extension** — Scan images and text directly while browsing, without leaving the page
- 📱 **PWA Support** — Install DRISHTI as an app on your phone or desktop

---

## 🏗️ How It Works (Under the Hood)

```
    You upload a file (image / audio / video / text)
                        │
                        ▼
    ┌──────────────────────────────────────┐
    │         FastAPI Backend Server       │
    │          (backend_server.py)         │
    └──────────────┬───────────────────────┘
                   │
         ┌─────────┴──────────┐
         ▼                    ▼
  ┌──────────────┐   ┌───────────────┐
  │ Custom Model │   │ Forensic      │
  │ EfficientNet │   │ Analysis      │
  │ B4 (PyTorch) │   │ (math-based)  │
  └──────┬───────┘   └───────┬───────┘
         │                   │
         └─────────┬─────────┘
                   ▼
    ┌──────────────────────────────────────┐
    │      Groq LLaMA 3.3 Explainer       │
    │  (Generates human-readable report)  │
    └──────────────┬───────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │     Neo4j Graph Database             │
    │  (Stores scan + links to threats)   │
    └──────────────┬───────────────────────┘
                   │
                   ▼
         Dashboard shows results:
         ✅ Confidence %
         ✅ Verdict (Real / Deepfake / Uncertain)
         ✅ AI Explanation
         ✅ Indicator Breakdown
```

### The Detection Pipeline (Step by Step)

1. **You upload** — Drop an image, audio clip, video, or paste text into the dashboard
2. **Custom Model runs** — Our locally-trained PyTorch EfficientNet-B4 network analyzes the content at the pixel/signal level
3. **Forensic checks** — Mathematical analysis runs (like Error Level Analysis for images, pitch variance for audio, perplexity for text)
4. **Results fuse** — All signals combine into a single confidence score
5. **AI explains** — Groq's LLaMA 3.3 reads the raw data and writes a 3-sentence forensic explanation in plain English
6. **Graph stores** — The scan is saved in Neo4j so DRISHTI can cross-reference it with past scans to spot patterns
7. **You see results** — Clean dashboard shows verdict, confidence gauge, indicator breakdown, and the AI explanation

---

## 📁 Project Structure

```
DRISHTI-AI/
│
├── 📂 drishti-frontend/          ← Next.js 16 Web Dashboard (what users see)
│   ├── app/
│   │   ├── page.js               ← Landing page (animated, cyber-themed)
│   │   ├── login/ & signup/      ← User authentication
│   │   └── dashboard/            ← Analysis modules
│   │       ├── page.js           ← Image Analysis (drag & drop)
│   │       ├── audio/page.js     ← Audio Analysis
│   │       ├── text/page.js      ← Text Analysis (with sentence heatmap)
│   │       ├── video/page.js     ← Video Analysis (with frame extraction)
│   │       └── history/page.js   ← Scan History (Neo4j graph data)
│   ├── components/               ← Reusable UI components
│   │   ├── AnalysisResult.js     ← Renders verdict, gauge, indicators, AI explanation
│   │   └── UploadZone.js         ← Drag-and-drop file upload widget
│   └── public/                   ← Icons, manifest (PWA)
│
├── 📂 drishti-backend/           ← Python FastAPI Server (the brain)
│   ├── backend_server.py         ← REST API endpoints (/analyze/image, /audio, /text, /video)
│   ├── main.py                   ← Core engine: all detection logic, models, forensics, RAG
│   └── requirements.txt          ← Python dependencies
│
├── 📂 chrome-extension/          ← Browser Extension (Chrome/Edge)
│   ├── manifest.json             ← Extension configuration
│   ├── popup/                    ← Extension popup UI
│   ├── content/                  ← In-page content scanning
│   └── background/               ← Background service worker
│
└── best_model (1).pth            ← Trained PyTorch model weights (82MB, not in Git)
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| Python | 3.12+ | Runs the backend & AI model |
| Node.js | 18+ | Runs the frontend dashboard |
| Git | any | Clone the repo |

### Step 1: Clone the Repository

```bash
git clone https://github.com/TechWithAkash/DRISHTI-AI.git
cd DRISHTI-AI
```

### Step 2: Set Up the Backend

```bash
cd drishti-backend

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# OR: .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Add Your API Keys

Create a `.env` file inside `drishti-backend/`:

```env
# Required — Powers the AI explanations
GROQ_KEY=your_groq_api_key_here

# Required — Graph intelligence (get free at neo4j.io/aura)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=your_username
NEO4J_PASSWORD=your_password

# Optional — Extra detection APIs (app works without these)
AI_OR_NOT_KEY=your_key
SIGHTENGINE_USER=your_user
SIGHTENGINE_SECRET=your_secret
HIVE_KEY=your_key
RESEMBLE_KEY=your_key
WINSTON_KEY=your_key
SAPLING_KEY=your_key
HF_KEY=your_huggingface_token
```

> 💡 **Minimum setup:** You only need `GROQ_KEY` to get started. The app will work with just the custom PyTorch model + Groq explanations. Other APIs add extra detection layers.

### Step 4: Add the Trained Model

Place your `best_model (1).pth` file in the project root directory (same level as `drishti-backend/`).

### Step 5: Start the Backend

```bash
cd drishti-backend
python backend_server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 6: Set Up & Start the Frontend

```bash
# Open a new terminal
cd drishti-frontend
npm install
npm run dev
```

You should see:
```
▲ Next.js 16.x
- Local: http://localhost:3000
✓ Ready
```

### Step 7: Open the App 🎉

Go to **[http://localhost:3000](http://localhost:3000)** in your browser. That's it!

---

## 🧪 API Endpoints

The backend exposes these REST endpoints (all on `http://localhost:8000`):

| Method | Endpoint | What It Does |
|--------|----------|-------------|
| `GET` | `/health` | Check if backend is running |
| `POST` | `/analyze/image` | Upload an image → get AI detection results |
| `POST` | `/analyze/audio` | Upload an audio file → get voice clone detection |
| `POST` | `/analyze/text` | Send text → get AI writing detection |
| `POST` | `/analyze/video` | Upload a video → get deepfake detection with frame analysis |
| `GET` | `/graph/stats` | Get Neo4j scan statistics |
| `GET` | `/graph/recent-fakes` | Get recently detected deepfakes |
| `GET` | `/graph/artifact-frequency` | Get most common AI artifacts |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16, React 19, Framer Motion | Dashboard UI, animations, PWA |
| **Backend** | FastAPI, Uvicorn | REST API server |
| **AI Model** | PyTorch, EfficientNet-B4 (custom-trained) | Image deepfake classification |
| **Audio Analysis** | Librosa, NumPy | Pitch, ZCR, phase forensics |
| **Text Analysis** | RoBERTa, Winston AI, Sapling AI | LLM-generated text detection |
| **Explanations** | Groq Cloud (LLaMA 3.3 70B) | RAG-powered forensic reports |
| **Graph DB** | Neo4j Aura | Cross-scan threat intelligence |
| **Browser** | Chrome Extension (Manifest V3) | Real-time in-browser scanning |

---

## 📸 Screenshots

> *Coming soon — run the app locally to see the full UI!*

---

## 👨‍💻 Team

**Akash Vishwakarma** — Full Stack Development, ML Engineering

---

## 📄 License

This project was built for **Hackive 2.0 Hackathon** (Cybersecurity Domain — Problem Statement 3).

---

<div align="center">
  <sub>Built with ❤️ for Hackive 2.0 · DRISHTI AI v2.0 · Deepfake Detection Platform</sub>
</div>
