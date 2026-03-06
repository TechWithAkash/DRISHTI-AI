# DRISHTI Chrome Extension — Deepfake Detector for Google Meet

> Real-time AI & deepfake detection for Google Meet participants.
> Built for Hackathon 2026 · PS3: Cybersecurity · AI-Generated Content Detection

---

## What It Does

DRISHTI (दृष्टि — Sanskrit for "Vision") detects whether participants in a Google Meet session are using deepfake video or AI-generated audio/video in real time.

### How It Works
1. The Chrome Extension **captures frames** from Google Meet participant video tiles every ~8 seconds
2. Frames are sent to the **DRISHTI FastAPI backend** running locally
3. The backend runs a **6-layer detection pipeline** (local forensics + 6 cloud APIs)
4. Results are shown as **color-coded badges** overlaid on each participant's video:
   - 🟢 **REAL** — likely authentic
   - 🟡 **UNCERTAIN** — manual review advised
   - 🔴 **DEEPFAKE** — AI manipulation detected (pulsing alert)

---

## Quick Start

### Step 1 — Install the Backend

```bash
cd /path/to/Hackive2.0/streamlit
pip install fastapi uvicorn python-multipart
python backend_server.py
```

The backend runs at `http://localhost:8000`. Check `http://localhost:8000/docs` for the API explorer.

### Step 2 — Load the Chrome Extension

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `chrome-extension/` folder
5. The **DRISHTI eye icon** appears in your toolbar

### Step 3 — Use in Google Meet

1. Join any Google Meet call
2. Click the DRISHTI icon → see the popup panel
3. Badges appear automatically on each participant's video tile
4. Click any badge for a detailed forensic breakdown

---

## Extension Architecture

```
chrome-extension/
├── manifest.json           ← MV3 manifest
│
├── background/
│   └── background.js       ← Service Worker: API calls, state, health checks
│
├── content/
│   ├── content.js          ← Injected into meet.google.com
│   │                          Observes tiles, captures frames, renders badges
│   └── overlay.css         ← Badge, panel, alert banner styles
│
├── popup/
│   ├── popup.html          ← Extension popup UI
│   ├── popup.css           ← Popup styles (dark cyberpunk theme)
│   └── popup.js            ← Popup logic, live polling, i18n, settings
│
├── _locales/               ← Multilingual support
│   ├── en/messages.json    ← English
│   ├── hi/messages.json    ← Hindi (हिन्दी)
│   ├── es/messages.json    ← Spanish (Español)
│   ├── fr/messages.json    ← French (Français)
│   ├── ar/messages.json    ← Arabic (العربية) — with RTL support
│   └── zh/messages.json    ← Chinese (中文)
│
└── icons/
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

---

## Backend Architecture

```
streamlit/backend_server.py  ← FastAPI server

POST /analyze/frame   ← Chrome extension (base64 JPEG frame)
POST /analyze/image   ← Full image multipart
POST /analyze/audio   ← Audio multipart
POST /analyze/text    ← Text JSON
GET  /health          ← Health check
GET  /kb              ← Knowledge base (for tooltip explanations)
```

The backend imports from `main.py` (DRISHTI core) and wraps the following pipeline for each frame:

```
Frame (JPEG base64)
    ↓
AI-or-Not API (40% weight)  +  Sightengine  +  Hive
    ↓
Local Forensics: DCT checkerboard, ELA, EXIF, sensor noise
    ↓
Fusion v2: weighted ensemble (60% API / 40% local)
    ↓
Groq LLaMA 3.3 RAG explanation
    ↓
{ confidence, verdict, tags, explanation }
```

---

## Multilingual Support

| Language | Code | Label Display |
|---|---|---|
| English  | `en` | REAL / UNCERTAIN / DEEPFAKE |
| Hindi    | `hi` | वास्तविक / अनिश्चित / डीपफेक |
| Spanish  | `es` | REAL / INCIERTO / FALSO |
| French   | `fr` | RÉEL / INCERTAIN / DEEPFAKE |
| Arabic   | `ar` | حقيقي / مشكوك / مزيف (RTL) |
| Chinese  | `zh` | 真实 / 不确定 / 深度伪造 |

Switch language from the extension popup → language grid.

---

## Features

| Feature | Description |
|---|---|
| Real-time frame capture | Canvas API captures video tile frames every 8s |
| Per-participant badges | Color-coded overlays injected directly on Meet tiles |
| Draggable summary panel | Shows scan count, suspicious count, backend status |
| Alert banner | Full-width red banner when a deepfake is detected |
| Voice alerts | Browser TTS announces deepfake detections |
| Local fallback | Works without backend using lightweight local heuristic |
| Tooltip on click | Shows confidence %, tags, and AI explanation |
| Threshold control | Slider to adjust fake/uncertain threshold (40–80%) |
| Settings persistence | All settings saved via `chrome.storage.local` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extension frontend | Vanilla JS, CSS3, Chrome MV3 |
| Content injection | Chrome Content Scripts |
| State management | Chrome Service Worker + `chrome.storage` |
| Backend | FastAPI + Uvicorn (Python) |
| Image forensics | OpenCV, NumPy, Pillow (local) |
| AI detection APIs | AI-or-Not, Sightengine, Hive.ai, HuggingFace |
| LLM explanation | Groq + LLaMA 3.3 70B |
| Graph intelligence | Neo4j (cross-scan correlation) |
| i18n | Chrome `_locales` + inline JS strings |

---

## Environment Variables (for backend)

Create `streamlit/.env`:
```env
AI_OR_NOT_KEY=your_key
SIGHTENGINE_USER=your_user
SIGHTENGINE_SECRET=your_secret
HIVE_KEY=your_key
GROQ_KEY=your_key
HF_KEY=your_key
NEO4J_URI=neo4j+s://...
NEO4J_PASSWORD=your_password
```

---

## Hackathon Demo Script

1. Start backend: `python backend_server.py` → green "ONLINE" in popup
2. Open Google Meet → join a call (or use a test recording)
3. Enable the extension → badges appear on each tile
4. Switch to Hindi → badges now show वास्तविक / डीपफेक
5. Simulate a deepfake → alert banner fires + voice reads the alert
6. Click the popup → show scan metrics and participant cards
7. Click a badge → tooltip shows confidence + forensic tags

Total demo time: **~3 minutes**
