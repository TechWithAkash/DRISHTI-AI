<div align="center">

# 🔍 DRISHTI AI

### Terminal-Grade Multimodal Deepfake Defense System

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-EfficientNet--B4-red?logo=pytorch)](https://pytorch.org)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange)](https://groq.com)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_Intelligence-green?logo=neo4j)](https://neo4j.com)

*A high-performance neural architecture designed to instantly tear through synthetic media signatures across Images, Audio, Video, and Text.*

</div>

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│                    DRISHTI v2                       │
├──────────┬──────────┬──────────┬──────────────────┤
│  IMAGE   │  AUDIO   │   TEXT   │     VIDEO        │
│ Analysis │ Analysis │ Analysis │   Analysis       │
├──────────┴──────────┴──────────┴──────────────────┤
│      Custom PyTorch EfficientNet-B4 Engine        │
├───────────────────────────────────────────────────┤
│           Groq LLaMA 3.3 RAG Explainer            │
├───────────────────────────────────────────────────┤
│           Neo4j Graph Intelligence                 │
├───────────────────────────────────────────────────┤
│      Chrome Extension · Next.js Dashboard          │
└───────────────────────────────────────────────────┘
```

## 🚀 Features

| Module | Description |
|--------|-------------|
| **Image Forensics** | Custom-trained EfficientNet-B4 classifier (100k+ dataset) for AI-generated image detection |
| **Audio Analysis** | Voice clone detection via Resemble AI, pitch/ZCR forensics |
| **Text Detection** | RoBERTa + Winston + Sapling ensemble with sentence-level heatmap |
| **Video Deepfake** | Frame-by-frame spatio-temporal analysis with temporal variance metrics |
| **Graph Intelligence** | Neo4j-powered adversarial threat mapping across all scans |
| **Chrome Extension** | Real-time browser-integrated deepfake scanner |
| **PWA Support** | Install as a standalone app on any device |
| **Groq RAG** | LLaMA 3.3 powered plain-English forensic explanations |

## 📁 Project Structure

```
DRISHTI-AI/
├── drishti-web/              # Next.js 16 Frontend (PWA)
│   ├── app/                  # App router pages
│   │   ├── dashboard/        # Analysis modules (image/audio/text/video)
│   │   ├── login/            # Authentication
│   │   └── signup/           # Registration
│   ├── components/           # Reusable React components
│   └── public/               # Static assets & PWA manifest
│
├── drishti-backend/          # FastAPI Backend
│   ├── main.py               # Core detection engine (all layers)
│   ├── backend_server.py     # REST API server
│   └── requirements.txt      # Python dependencies
│
├── chrome-extension/         # Chrome Extension
│   ├── manifest.json         # Extension config
│   ├── popup.html/js         # Extension popup UI
│   └── content.js            # Page content scanner
│
└── PS3.md                    # Problem statement
```

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Neo4j (optional, for graph intelligence)

### 1. Backend Setup
```bash
cd drishti-backend
pip install -r requirements.txt
# Add your API keys to .env
python backend_server.py
```

### 2. Frontend Setup
```bash
cd drishti-web
npm install
npm run dev
```

### 3. Model Setup
Place your trained `best_model.pth` (EfficientNet-B4) in the `drishti-backend/` directory.

## 🔑 Environment Variables

Create a `.env` file in `drishti-backend/`:

```env
GROQ_KEY=your_groq_api_key
NEO4J_URI=your_neo4j_uri
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## 🛡️ Detection Pipeline

1. **Input** → Image/Audio/Video/Text uploaded via Dashboard or Chrome Extension
2. **Custom Model** → EfficientNet-B4 inference (380×380 resolution)
3. **Forensic Analysis** → Modality-specific artifact detection
4. **Groq RAG** → LLaMA 3.3 generates human-readable forensic explanation
5. **Neo4j** → Result stored in graph database for threat intelligence
6. **Output** → Verdict + Confidence + Visual indicators + AI explanation

## 👨‍💻 Author

**Akash Vishwakarma**

---

<div align="center">
  <sub>Built for Hackive 2.0 Hackathon · DRISHTI v2.0</sub>
</div>
