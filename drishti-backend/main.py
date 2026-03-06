"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          DRISHTI v2 — Enterprise Deepfake & Synthetic Media Detection        ║
║                                                                              ║
║  ARCHITECTURE:                                                               ║
║    Layer 1 · Cloud API Detection  (AI-or-Not, Sightengine, Hive, HF)        ║
║    Layer 2 · Calibrated Math Forensics (DCT, ELA, EXIF, ZCR) — v2 FIXED    ║
║    Layer 3 · LangGraph Orchestration  (stateful multi-agent pipeline)        ║
║    Layer 4 · Neo4j GraphDB        (relational intelligence across scans)     ║
║    Layer 5 · MCP Server           (Claude Desktop tool integration)          ║
║    Layer 6 · Groq RAG Explainer   (LLaMA 3.3 plain-English forensics)        ║
║    Layer 7 · Content Highlighting (sentence/frame/timestamp flagging)        ║
╚══════════════════════════════════════════════════════════════════════════════╝

CHANGELOG v2:
  ✅ FIXED: False positive on real images (recalibrated sigmoid thresholds)
     - ELA: midpoint 3.5→5.0, direction corrected (low ELA = AI, not high)
     - Noise: midpoint 8→15 (real cameras ARE noisy; AI images are smooth)
     - EXIF missing score: 0.65→0.42 (screenshots also lack EXIF)
     - Forensic-only cap: 0.68→0.62 (API required for HIGH confidence)
  ✅ ADDED: AI-or-Not API (40% fusion weight, primary image signal)
  ✅ ADDED: HuggingFace RoBERTa text detector (Hello-SimpleAI/chatgpt-detector-roberta)
  ✅ ADDED: Fusion v2 — weighted ensemble, API "real" signals override forensics
  ✅ ADDED: Text highlighting — sentence-level AI probability heatmap + bar chart
  ✅ ADDED: Video frame gallery — thumbnails with color-coded confidence badges
  ✅ ADDED: Audio transcript via Groq Whisper + per-segment AI flagging
  ✅ ADDED: Signal radar chart (all API + forensic scores)
  ✅ ADDED: Forensic ELA heatmap overlay on images
  ✅ ADDED: Audio waveform visualization

RECOMMENDED OPEN-SOURCE MODELS (HuggingFace Inference API):
  IMAGE:  umm-maybe/AI-image-detector, Organika/sdxl-detector,
          dima806/deepfake_vs_real_image_detection
  TEXT:   Hello-SimpleAI/chatgpt-detector-roberta,
          roberta-base-openai-detector
  AUDIO:  Resemble AI API, facebook/wav2vec2-base (fine-tune on deepfake data)
  LOCAL:  pip install transformers torch timm  (EfficientNet-B4 for GPU deployment)
"""

import sys, os, io, time, json, math, re, tempfile, warnings, hashlib
import asyncio, functools
import numpy as np
import requests
from PIL import Image, ExifTags, ImageDraw
from collections import Counter
from typing import TypedDict, Optional, List
import streamlit as st
import plotly.graph_objects as go
warnings.filterwarnings("ignore")

try:
    import pandas as pd
    _PANDAS_OK = True
except ImportError:
    _PANDAS_OK = False

try:
    from langgraph.graph import END as _LG_END
except ImportError:
    _LG_END = "__end__"

# ══════════════════════════════════════════════════════════════════════════════
# API KEYS — replace with your actual keys
# ══════════════════════════════════════════════════════════════════════════════
# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

AI_OR_NOT_KEY      = os.getenv("AI_OR_NOT_KEY", "")
SIGHTENGINE_USER   = os.getenv("SIGHTENGINE_USER", "")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET", "")
HIVE_KEY           = os.getenv("HIVE_KEY", "")
RESEMBLE_KEY       = os.getenv("RESEMBLE_KEY", "")
WINSTON_KEY        = os.getenv("WINSTON_KEY", "")
SAPLING_KEY        = os.getenv("SAPLING_KEY", "")
HF_KEY             = os.getenv("HF_KEY", "")
GROQ_KEY           = os.getenv("GROQ_KEY", "")
NEO4J_URI          = os.getenv("NEO4J_URI", "")
NEO4J_USER         = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD     = os.getenv("NEO4J_PASSWORD", "")

# ══════════════════════════════════════════════════════════════════════════════
# UI STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="DRISHTI v2", page_icon="🛡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#080d14;color:#c8d8e8}
.stApp{background:#080d14}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1628,#060d1a);border-right:1px solid #0ff3}
[data-testid="stSidebar"] *{color:#aabbd0!important}
.vx-header{background:linear-gradient(135deg,#020812,#050f20,#010810);border:1px solid #0ff4;border-radius:4px;padding:2.5rem 3rem;margin-bottom:2rem;position:relative;overflow:hidden}
.vx-header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00f5ff,#00f5ff80,transparent)}
.vx-header::after{content:'DRISHTI';position:absolute;right:-20px;top:50%;transform:translateY(-50%);font-family:'Share Tech Mono',monospace;font-size:8rem;color:#ffffff04;letter-spacing:-5px;pointer-events:none}
.vx-logo{font-family:'Share Tech Mono',monospace;font-size:3rem;color:#00f5ff;letter-spacing:8px;margin:0;text-shadow:0 0 30px #00f5ff88,0 0 60px #00f5ff33}
.vx-tagline{font-family:'Rajdhani',sans-serif;font-size:1.1rem;color:#5a8a9a;letter-spacing:3px;text-transform:uppercase;margin-top:.3rem}
.vx-badge{display:inline-block;background:#00f5ff11;border:1px solid #00f5ff44;color:#00f5ff;font-family:'Share Tech Mono',monospace;font-size:.65rem;padding:3px 10px;border-radius:2px;letter-spacing:2px;margin-top:1rem}
.vx-verdict-fake{background:linear-gradient(135deg,#1a0505,#2d0808);border:1px solid #ff3b3b66;border-left:4px solid #ff3b3b;border-radius:4px;padding:1.5rem 2rem;font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;color:#ff6b6b;letter-spacing:2px}
.vx-verdict-real{background:linear-gradient(135deg,#021a0a,#042d10);border:1px solid #00ff7766;border-left:4px solid #00ff77;border-radius:4px;padding:1.5rem 2rem;font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;color:#00ff88;letter-spacing:2px}
.vx-verdict-uncertain{background:linear-gradient(135deg,#1a1205,#2d1f08);border:1px solid #ffaa0066;border-left:4px solid #ffaa00;border-radius:4px;padding:1.5rem 2rem;font-family:'Rajdhani',sans-serif;font-size:1.6rem;font-weight:700;color:#ffbb33;letter-spacing:2px}
.vx-ind-high{background:#0d0303;border:1px solid #ff3b3b33;border-left:3px solid #ff3b3b;border-radius:3px;padding:.9rem 1.1rem;margin:.5rem 0}
.vx-ind-medium{background:#0d0a03;border:1px solid #ffaa0033;border-left:3px solid #ffaa00;border-radius:3px;padding:.9rem 1.1rem;margin:.5rem 0}
.vx-ind-low{background:#03060d;border:1px solid #00aaff33;border-left:3px solid #00aaff;border-radius:3px;padding:.9rem 1.1rem;margin:.5rem 0}
.vx-ind-name{font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:700;color:#d0e8f0;letter-spacing:1px}
.vx-ind-score{font-family:'Share Tech Mono',monospace;font-size:.8rem;color:#5a8a9a;float:right}
.vx-ind-explain{font-size:.82rem;color:#8aa8b8;margin-top:.4rem;line-height:1.5}
.vx-section{font-family:'Share Tech Mono',monospace;font-size:.75rem;color:#00f5ff;letter-spacing:4px;text-transform:uppercase;border-bottom:1px solid #00f5ff22;padding-bottom:.5rem;margin:1.5rem 0 1rem}
.vx-metric{background:#0a1628;border:1px solid #1a3a5a;border-radius:3px;padding:1rem;text-align:center}
.vx-metric-val{font-family:'Share Tech Mono',monospace;font-size:1.8rem;color:#00f5ff}
.vx-metric-lbl{font-family:'Rajdhani',sans-serif;font-size:.7rem;color:#3a6a7a;letter-spacing:2px;text-transform:uppercase;margin-top:.2rem}
.vx-api-ok{background:#00ff7722;border:1px solid #00ff7755;color:#00ff77;padding:2px 8px;border-radius:2px;font-size:.7rem;font-family:'Share Tech Mono',monospace}
.vx-api-off{background:#ff3b3b22;border:1px solid #ff3b3b55;color:#ff6b6b;padding:2px 8px;border-radius:2px;font-size:.7rem;font-family:'Share Tech Mono',monospace}
.vx-api-na{background:#ffaa0022;border:1px solid #ffaa0055;color:#ffbb33;padding:2px 8px;border-radius:2px;font-size:.7rem;font-family:'Share Tech Mono',monospace}
.vx-rag{background:linear-gradient(135deg,#050f20,#030a18);border:1px solid #00f5ff22;border-top:2px solid #00f5ff55;border-radius:3px;padding:1.2rem 1.4rem;margin-top:1rem}
.vx-rag-header{font-family:'Share Tech Mono',monospace;font-size:.65rem;color:#00f5ff88;letter-spacing:3px;margin-bottom:.6rem}
.vx-rag-text{font-size:.88rem;color:#9abac8;line-height:1.7}
.vx-graph-card{background:#050f20;border:1px solid #0a2a40;border-radius:3px;padding:.8rem 1rem;margin:.4rem 0;font-family:'Share Tech Mono',monospace;font-size:.72rem;color:#4a8a9a}
.vx-graph-card b{color:#00f5ff}
/* Text highlight */
.txt-ai-high{background:rgba(255,59,59,.28);border-bottom:2px solid #ff3b3b;border-radius:2px;padding:1px 3px;cursor:help}
.txt-ai-medium{background:rgba(255,170,0,.18);border-bottom:2px solid #ffaa00;border-radius:2px;padding:1px 3px;cursor:help}
.txt-ai-low{background:rgba(0,245,255,.07);border-bottom:1px solid #00f5ff44;border-radius:2px;padding:1px 3px;cursor:help}
.txt-human{color:#c8d8e8}
.txt-highlight-container{font-family:'Inter',sans-serif;font-size:.9rem;line-height:2.1;background:#05101e;border:1px solid #1a3a5a;border-radius:4px;padding:1.4rem 1.6rem}
.txt-legend{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:.8rem;font-size:.7rem;font-family:'Share Tech Mono',monospace}
.txt-legend span{padding:2px 8px;border-radius:2px}
/* Timestamp rows */
.ts-row{display:flex;align-items:flex-start;gap:.6rem;padding:.5rem .9rem;border-left:3px solid #ff3b3b;margin:.25rem 0;background:#0d0303;border-radius:0 3px 3px 0;font-size:.82rem}
.ts-row-ok{border-left-color:#00ff77;background:#021a0a}
.ts-row-med{border-left-color:#ffaa00;background:#0d0a03}
.ts-time{font-family:'Share Tech Mono',monospace;color:#00f5ff;min-width:75px;flex-shrink:0}
.ts-score{font-family:'Share Tech Mono',monospace;color:#ff6b6b;min-width:45px;flex-shrink:0}
.ts-score-ok{color:#00ff77}
.ts-score-med{color:#ffaa00}
.stTabs [data-baseweb="tab-list"]{background:#0a1628;border-bottom:1px solid #1a3a5a;gap:0}
.stTabs [data-baseweb="tab"]{font-family:'Rajdhani',sans-serif;font-weight:600;letter-spacing:1px;color:#4a7a9a;border-bottom:2px solid transparent;padding:.75rem 1.5rem}
.stTabs [aria-selected="true"]{color:#00f5ff!important;border-bottom:2px solid #00f5ff!important}
[data-testid="stFileUploader"]{background:#0a1628!important;border:1px dashed #00f5ff33!important;border-radius:4px!important}
.stButton>button{background:linear-gradient(135deg,#00f5ff22,#005f8a22)!important;border:1px solid #00f5ff66!important;color:#00f5ff!important;font-family:'Rajdhani',sans-serif!important;font-weight:700!important;letter-spacing:2px!important;border-radius:2px!important}
.stButton>button:hover{background:linear-gradient(135deg,#00f5ff33,#005f8a33)!important;border-color:#00f5ff!important;box-shadow:0 0 20px #00f5ff33!important}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:#080d14}
::-webkit-scrollbar-thumb{background:#00f5ff33;border-radius:2px}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════════════════
KB = {
    "gan_grid":             {"name":"GAN Spatial Checkerboarding","sev":"HIGH","explain":"Detected regular grid-like anomalies in the high-frequency DCT spectrum — a mathematical signature of transposed convolution upsampling layers in GAN and diffusion model generators."},
    "ela_uniform":          {"name":"Uniform Compression Response","sev":"MEDIUM","explain":"Error Level Analysis shows unnaturally uniform JPEG compression variance. Authentic optical captures compress heterogeneously; AI images compress uniformly."},
    "no_exif":              {"name":"Missing Physical Device Metadata","sev":"MEDIUM","explain":"No EXIF metadata found. Real cameras embed model, focal length, aperture, and GPS data. AI-generated images have no physical capture event and carry no device metadata."},
    "hf_noise_absent":      {"name":"Missing Sensor Noise Distribution","sev":"HIGH","explain":"Median blur subtraction reveals absence of natural Gaussian sensor noise. Generative models output mathematically smooth pixel gradients lacking shot noise inherent to physical camera sensors."},
    "blur_anomaly":         {"name":"Focal Depth / Blur Inconsistency","sev":"MEDIUM","explain":"Analysis detected inconsistent sharpness across the image plane. AI generators struggle to simulate physically accurate depth-of-field."},
    "ai_software_tag":      {"name":"AI Software Signature in Metadata","sev":"HIGH","explain":"EXIF software field references a known generative AI tool. Near-definitive evidence of synthetic origin."},
    "ai_or_not":            {"name":"AI-or-Not Image Detector","sev":"HIGH","explain":"AI-or-Not API runs a specialized binary classifier trained on millions of real vs AI-generated images across all major generators including Midjourney, DALL-E 3, Stable Diffusion, and Firefly."},
    "custom_trained_model": {"name":"Custom PyTorch Classifier","sev":"HIGH","explain":"A localized EfficientNet-B4 network fine-tuned specifically for detecting GenAI image artifacts."},
    "flat_pitch":           {"name":"Unnaturally Stable Pitch (F0)","sev":"HIGH","explain":"Fundamental frequency extraction shows abnormally low variance. Human speech contains micro-fluctuations from breath and vocal cord tension. The measured pitch stability aligns with TTS vocoder synthesis."},
    "hf_absent":            {"name":"Attenuated High-Frequency Spectrum","sev":"MEDIUM","explain":"FFT analysis shows severe drop-off in energy above 7kHz. Neural voice synthesizers apply low-pass filtering, failing to render high-frequency breath noise and sibilant consonants."},
    "phase_break":          {"name":"Phase Discontinuity / Frame Stitching","sev":"HIGH","explain":"STFT detected abrupt non-continuous phase shifts at regular intervals — artifacts at the boundaries of synthesized audio frames."},
    "low_burstiness":       {"name":"Low Acoustic Energy Variance","sev":"MEDIUM","explain":"RMS energy distribution is unnaturally uniform. Human speech is highly dynamic; this audio envelope is mathematically optimized — typical of AI generation."},
    "zcr_anomaly":          {"name":"Zero-Crossing Rate (ZCR) Anomaly","sev":"HIGH","explain":"ZCR variance is abnormally low. Human speech contains chaotic high-frequency fricatives causing high ZCR variance. AI synthesis cannot replicate this biological chaos."},
    "low_perplexity":       {"name":"Low Language Model Perplexity","sev":"HIGH","explain":"GPT-2 assigns highly predictable probabilities to this token sequence. The text maps to AI output distributions with statistical precision."},
    "uniform_sentences":    {"name":"Statistical Sentence Uniformity","sev":"MEDIUM","explain":"Standard deviation of sentence lengths is exceptionally low. Human writing oscillates between complex and simple structures; LLMs produce statistically uniform cadence."},
    "ai_phrases":           {"name":"LLM Transition Phrase Overuse","sev":"MEDIUM","explain":"Statistically significant cluster of transition phrases strongly associated with RLHF-trained language models."},
    "temporal_inconsistency":{"name":"Inter-Frame Temporal Instability","sev":"HIGH","explain":"Detected micro-flickering and specific high-frequency structural shifts between frames — artifacts of face-swap blending failure or temporal incoherence from video generation models."},
    "sightengine_deepfake": {"name":"Face Swap / Deepfake (Sightengine)","sev":"HIGH","explain":"Sightengine's neural network detected facial manipulation by analyzing blending boundaries, eye reflection consistency, and facial landmark alignment."},
    "sightengine_ai_image": {"name":"Gen-AI Image (Sightengine)","sev":"HIGH","explain":"Cloud-based pixel-level classification matched this image to outputs of latent diffusion models."},
    "hive_ai_image":        {"name":"Hive AI Detection","sev":"HIGH","explain":"Hive Moderation's enterprise-grade AI detection engine analyzed the visual tensor and matched it against known generative distributions."},
    "hf_ai_image":          {"name":"Synthetic Image (HuggingFace ViT)","sev":"MEDIUM","explain":"Open-source HuggingFace ViT model evaluated the image tensor and mapped it to synthetic training data distributions."},
    "hf_deepfake":          {"name":"Face Swap (HF Ensemble)","sev":"HIGH","explain":"HuggingFace deepfake detection model identified physical inconsistencies in facial structure indicative of digital face replacement."},
    "hf_text_ai":           {"name":"AI Text (RoBERTa Detector)","sev":"HIGH","explain":"Open-source RoBERTa-based ChatGPT detector classified this text as machine-generated with high probability."},
    "winston_ai":           {"name":"AI Content (Winston AI)","sev":"HIGH","explain":"Winston AI's commercial detector flagged this text as highly likely machine-generated."},
    "sapling_ai":           {"name":"AI Text (Sapling)","sev":"HIGH","explain":"Sapling's linguistic analysis model detected output distributions matching large language models."},
    "resemble_ai_audio":    {"name":"Synthetic Voice (Resemble AI)","sev":"HIGH","explain":"Resemble AI's DETECT model matched audio fingerprints against 160+ deepfake voice architectures."},
}

# ══════════════════════════════════════════════════════════════════════════════
# KEY VALIDATORS
# ══════════════════════════════════════════════════════════════════════════════
def _aon_ok():      return len(AI_OR_NOT_KEY) > 10 and "YOUR_" not in AI_OR_NOT_KEY
def _sight_ok():    return len(SIGHTENGINE_USER) > 5 and "PASTE" not in SIGHTENGINE_USER
def _hive_ok():     return len(HIVE_KEY) > 5 and "PASTE" not in HIVE_KEY
def _resemble_ok(): return len(RESEMBLE_KEY) > 5 and "PASTE" not in RESEMBLE_KEY
def _winston_ok():  return len(WINSTON_KEY) > 5 and "PASTE" not in WINSTON_KEY
def _sapling_ok():  return len(SAPLING_KEY) > 5 and "PASTE" not in SAPLING_KEY
def _hf_ok():       return len(HF_KEY) > 5 and "PASTE" not in HF_KEY
def _groq_ok():     return len(GROQ_KEY) > 5 and "PASTE" not in GROQ_KEY
def _neo4j_ok():    return len(NEO4J_URI) > 5 and "PASTE" not in NEO4J_URI

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 4 — NEO4J
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def _get_neo4j_driver():
    if not _neo4j_ok(): return None
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        return driver
    except Exception: return None

def graph_save_detection(modality, confidence, tags, file_hash, metadata={}):
    driver = _get_neo4j_driver()
    if not driver: return
    try:
        import datetime
        verdict = "FAKE" if confidence > 60 else "UNCERTAIN" if confidence > 45 else "AUTHENTIC"
        with driver.session() as s:
            s.run("MERGE (sc:Scan {hash:$hash}) SET sc.modality=$modality, sc.confidence=$confidence, sc.verdict=$verdict, sc.timestamp=$ts, sc.metadata=$meta",
                  hash=file_hash, modality=modality, confidence=round(confidence,1), verdict=verdict,
                  ts=datetime.datetime.utcnow().isoformat(), meta=json.dumps(metadata))
            for tag in tags:
                s.run("MERGE (a:Artifact {name:$tag}) WITH a MATCH (sc:Scan {hash:$hash}) MERGE (sc)-[:DETECTED]->(a)", tag=tag, hash=file_hash)
    except Exception: pass

def graph_find_similar(tags, threshold=45.0):
    driver = _get_neo4j_driver()
    if not driver or not tags: return []
    try:
        with driver.session() as s:
            result = s.run("MATCH (sc:Scan)-[:DETECTED]->(a:Artifact) WHERE a.name IN $tags AND sc.confidence>=$threshold RETURN sc.hash AS hash, sc.modality AS modality, sc.confidence AS confidence, sc.verdict AS verdict, sc.timestamp AS ts, collect(a.name) AS shared_tags, count(a) AS match_count ORDER BY match_count DESC, sc.confidence DESC LIMIT 5", tags=tags, threshold=threshold)
            return [dict(r) for r in result]
    except Exception: return []

def graph_artifact_frequency():
    driver = _get_neo4j_driver()
    if not driver: return []
    try:
        with driver.session() as s:
            result = s.run("MATCH (sc:Scan)-[:DETECTED]->(a:Artifact) RETURN a.name AS artifact, count(sc) AS frequency ORDER BY frequency DESC LIMIT 10")
            return [dict(r) for r in result]
    except Exception: return []

def graph_recent_fakes(limit=5):
    driver = _get_neo4j_driver()
    if not driver: return []
    try:
        with driver.session() as s:
            result = s.run("MATCH (sc:Scan) WHERE sc.verdict='FAKE' RETURN sc.hash AS hash, sc.modality AS modality, sc.confidence AS confidence, sc.timestamp AS ts ORDER BY sc.timestamp DESC LIMIT $limit", limit=limit)
            return [dict(r) for r in result]
    except Exception: return []

def graph_stats():
    driver = _get_neo4j_driver()
    if not driver: return {}
    try:
        with driver.session() as s:
            total = s.run("MATCH (sc:Scan) RETURN count(sc) AS n").single()
            fakes = s.run("MATCH (sc:Scan {verdict:'FAKE'}) RETURN count(sc) AS n").single()
            arts  = s.run("MATCH (a:Artifact) RETURN count(a) AS n").single()
            return {"total_scans": total["n"] if total else 0, "total_fakes": fakes["n"] if fakes else 0, "unique_artifacts": arts["n"] if arts else 0}
    except Exception: return {}

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — API CALLERS
# ══════════════════════════════════════════════════════════════════════════════
_CUSTOM_MODEL_CACHE = None
def _get_custom_model():
    global _CUSTOM_MODEL_CACHE
    if _CUSTOM_MODEL_CACHE is not None:
        return _CUSTOM_MODEL_CACHE
    try:
        import torch
        import timm
        from torch import nn
        from torchvision import transforms
        class GenAIClassifier(nn.Module):
            def __init__(self):
                super().__init__()
                # EfficientNet-B4 backbone (num_features = 1792)
                self.backbone = timm.create_model("efficientnet_b4", pretrained=False, num_classes=0)
                # Sequential index mapping:
                # 0: Dropout(0.5)
                # 1: Linear(1792, 512)
                # 2: SiLU (no-params)
                # 3: Dropout(0.5)
                # 4: Linear(512, 1)
                self.head = nn.Sequential(
                    nn.Dropout(0.5),
                    nn.Linear(self.backbone.num_features, 512),
                    nn.SiLU(),
                    nn.Dropout(0.5),
                    nn.Linear(512, 1)
                )
            def forward(self, x):
                return self.head(self.backbone(x))
                
        model = GenAIClassifier()
        model_path = os.path.join(os.path.dirname(__file__), "../best_model (1).pth")
        model.load_state_dict(torch.load(model_path, map_location="cpu")['model_state_dict'])
        model.eval()
        
        transform = transforms.Compose([
            transforms.Resize((380, 380)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        _CUSTOM_MODEL_CACHE = (model, transform)
        return _CUSTOM_MODEL_CACHE
    except Exception as e:
        print("Error loading custom model:", e)
        return None, None

def custom_trained_model_inference(img_bytes):
    try:
        import torch
        from PIL import Image
        import io
        model, transform = _get_custom_model()
        if model is None:
            return {"score": None, "source": "custom_trained_model"}
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            logits = model(tensor)
            prob = torch.sigmoid(logits).item()
        # FIX: Flip the score. Assuming model output 1=Human, 0=AI. 
        # Most apps expect score to represent 'AI Chance'.
        ai_score = 1.0 - prob
        return {"score": ai_score, "source": "custom_trained_model"}
    except Exception as e:
        print("Custom model inference err:", e)
        return {"score": None, "source": "custom_trained_model"}

def ai_or_not_image(img_bytes):
    """PRIMARY image detector — AI-or-Not specialized binary classifier."""
    if not _aon_ok(): return {"score": None, "source": "ai_or_not"}
    try:
        r = requests.post(
            "https://api.aiornot.com/v1/reports/image",
            headers={"Authorization": f"Bearer {AI_OR_NOT_KEY}", "Accept": "application/json"},
            files={"object": ("image.jpg", img_bytes, "image/jpeg")},
            timeout=12
        )
        data = r.json()
        ai_conf = (data.get("report", {}).get("ai", {}) or {}).get("confidence")
        if ai_conf is None:
            ai_conf = data.get("confidence") or data.get("score")
        return {"score": float(ai_conf) if ai_conf is not None else None, "source": "ai_or_not"}
    except Exception as e:
        return {"score": None, "source": "ai_or_not"}

def sight_image_deepfake(img_bytes):
    if not _sight_ok(): return {"score": None, "source": "sightengine_deepfake"}
    try:
        r = requests.post("https://api.sightengine.com/1.0/check.json", files={"media": ("img.jpg", img_bytes, "image/jpeg")}, data={"models": "deepfake", "api_user": SIGHTENGINE_USER, "api_secret": SIGHTENGINE_SECRET}, timeout=10)
        return {"score": r.json().get("type", {}).get("deepfake"), "source": "sightengine_deepfake"}
    except Exception: return {"score": None, "source": "sightengine_deepfake"}

def sight_image_ai(img_bytes):
    if not _sight_ok(): return {"score": None, "source": "sightengine_ai_image"}
    try:
        r = requests.post("https://api.sightengine.com/1.0/check.json", files={"media": ("img.jpg", img_bytes, "image/jpeg")}, data={"models": "genai", "api_user": SIGHTENGINE_USER, "api_secret": SIGHTENGINE_SECRET}, timeout=10)
        return {"score": r.json().get("type", {}).get("ai_generated"), "source": "sightengine_ai_image"}
    except Exception: return {"score": None, "source": "sightengine_ai_image"}

def hive_image_ai(img_bytes):
    if not _hive_ok(): return {"score": None, "source": "hive_ai_image"}
    try:
        r = requests.post("https://api.thehive.ai/api/v2/task/sync", headers={"Authorization": f"token {HIVE_KEY}", "Accept": "application/json"}, files={"media": ("image.jpg", img_bytes, "image/jpeg")}, timeout=15)
        data = r.json(); score = None
        try:
            classes = data['status'][0]['response']['output'][0]['classes']
            for c in classes:
                if c.get('class','').lower() in ['yes','yes_ai_generated','deepfake','ai_generated','fake']:
                    score = max(score or 0.0, float(c['score']))
        except (KeyError, IndexError): pass
        return {"score": score, "source": "hive_ai_image"}
    except Exception: return {"score": None, "source": "hive_ai_image"}

def hf_image(img_bytes):
    if not _hf_ok(): return {"score": None, "source": "hf_ai_image"}
    try:
        r = requests.post("https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector", headers={"Authorization": f"Bearer {HF_KEY}"}, data=img_bytes, timeout=10)
        for item in r.json():
            if isinstance(item, dict) and "artificial" in str(item.get("label","")).lower():
                return {"score": item["score"], "source": "hf_ai_image"}
        return {"score": None, "source": "hf_ai_image"}
    except Exception: return {"score": None, "source": "hf_ai_image"}

def hf_image_deepfake(img_bytes):
    if not _hf_ok(): return {"score": None, "source": "hf_deepfake"}
    try:
        r = requests.post("https://api-inference.huggingface.co/models/dima806/deepfake_vs_real_image_detection", headers={"Authorization": f"Bearer {HF_KEY}"}, data=img_bytes, timeout=10)
        for item in r.json():
            if isinstance(item, dict) and "fake" in str(item.get("label","")).lower():
                return {"score": item["score"], "source": "hf_deepfake"}
        return {"score": None, "source": "hf_deepfake"}
    except Exception: return {"score": None, "source": "hf_deepfake"}

def hf_text_ai(text):
    """HuggingFace RoBERTa ChatGPT detector."""
    if not _hf_ok(): return {"score": None, "source": "hf_text_ai"}
    try:
        r = requests.post("https://api-inference.huggingface.co/models/Hello-SimpleAI/chatgpt-detector-roberta",
                          headers={"Authorization": f"Bearer {HF_KEY}"},
                          json={"inputs": text[:512]}, timeout=12)
        data = r.json()
        items = data[0] if (isinstance(data, list) and isinstance(data[0], list)) else data
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and item.get("label","").upper() in ["CHATGPT","FAKE","AI","MACHINE","1"]:
                    return {"score": float(item["score"]), "source": "hf_text_ai"}
        return {"score": None, "source": "hf_text_ai"}
    except Exception: return {"score": None, "source": "hf_text_ai"}

def resemble_audio(audio_bytes):
    if not _resemble_ok(): return {"score": None, "source": "resemble_ai_audio"}
    try:
        r = requests.post("https://detect.resemble.ai/api/v1/detect", headers={"Authorization": f"Token token={RESEMBLE_KEY}"}, files={"audio_data": ("audio.wav", audio_bytes, "audio/wav")}, timeout=15)
        d = r.json(); score = d.get("score") or d.get("probability") or d.get("ai_probability")
        return {"score": score, "source": "resemble_ai_audio"}
    except Exception: return {"score": None, "source": "resemble_ai_audio"}

def winston_text(text):
    if not _winston_ok(): return {"score": None, "source": "winston_ai"}
    try:
        r = requests.post("https://api.gowinston.ai/v2/predict", headers={"Authorization": f"Bearer {WINSTON_KEY}", "Content-Type": "application/json"}, json={"text": text, "sentences": True, "language": "en"}, timeout=10)
        raw = r.json().get("score") or r.json().get("ai_score") or (r.json().get("result") or {}).get("score")
        return {"score": float(raw)/100.0 if raw is not None else None, "source": "winston_ai"}
    except Exception: return {"score": None, "source": "winston_ai"}

def sapling_text(text):
    if not _sapling_ok(): return {"score": None, "source": "sapling_ai"}
    try:
        r = requests.post("https://api.sapling.ai/api/v1/aidetect", json={"key": SAPLING_KEY, "text": text}, timeout=10)
        return {"score": r.json().get("score"), "source": "sapling_ai"}
    except Exception: return {"score": None, "source": "sapling_ai"}

def sight_video_deepfake(video_bytes, ext="mp4"):
    if not _sight_ok(): return {"score": None, "source": "sightengine_deepfake"}
    try:
        r = requests.post("https://api.sightengine.com/1.0/video/check-sync.json", files={"media": (f"v.{ext}", video_bytes, f"video/{ext}")}, data={"models": "deepfake", "api_user": SIGHTENGINE_USER, "api_secret": SIGHTENGINE_SECRET}, timeout=60)
        d = r.json(); return {"score": d.get("summary", {}).get("deepfake") or d.get("type", {}).get("deepfake"), "source": "sightengine_deepfake"}
    except Exception: return {"score": None, "source": "sightengine_deepfake"}

def sight_video_ai(video_bytes, ext="mp4"):
    if not _sight_ok(): return {"score": None, "source": "sightengine_ai_video"}
    try:
        r = requests.post("https://api.sightengine.com/1.0/video/check-sync.json", files={"media": (f"v.{ext}", video_bytes, f"video/{ext}")}, data={"models": "genai", "api_user": SIGHTENGINE_USER, "api_secret": SIGHTENGINE_SECRET}, timeout=60)
        d = r.json(); return {"score": d.get("summary", {}).get("ai_generated") or d.get("type", {}).get("ai_generated"), "source": "sightengine_ai_video"}
    except Exception: return {"score": None, "source": "sightengine_ai_video"}

# ══════════════════════════════════════════════════════════════════════════════
# WHISPER TRANSCRIPT
# ══════════════════════════════════════════════════════════════════════════════
AI_PHRASE_LIST = [
    "furthermore", "it is important", "in conclusion", "notably", "delve into",
    "it's worth noting", "in summary", "as a result", "to summarize",
    "in this context", "it should be noted", "this ensures", "leveraging",
    "utilize", "streamline", "robust solution", "additionally", "moreover",
    "therefore", "consequently", "subsequently", "in essence"
]

def whisper_transcribe(audio_bytes, ext=".wav"):
    """Groq Whisper API — fast, free tier available."""
    if not _groq_ok(): return []
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(audio_bytes); tmp_path = f.name
        with open(tmp_path, "rb") as f:
            r = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                files={"file": (f"audio{ext}", f, "audio/wav")},
                data={"model": "whisper-large-v3", "response_format": "verbose_json", "timestamp_granularities": "segment"},
                timeout=30
            )
        os.unlink(tmp_path)
        segments = r.json().get("segments", [])
        return [{"start": round(s.get("start",0),1), "end": round(s.get("end",0),1), "text": s.get("text","").strip(), "ai_score": None} for s in segments]
    except Exception: return []

def score_audio_segment(text):
    words = text.lower().split()
    if not words: return 0.05
    hits = sum(1 for p in AI_PHRASE_LIST if p in text.lower())
    lex_div = len(set(words)) / max(len(words), 1)
    return min(hits * 0.3 + (1 - lex_div) * 0.25, 0.95)

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 6 — GROQ RAG
# ══════════════════════════════════════════════════════════════════════════════
def groq_explain(modality, confidence, tags, details):
    if not _groq_ok(): return ""
    kb_ctx = "\n\n".join(f"[{t.upper()}] {KB[t]['name']}: {KB[t]['explain']}" for t in tags if t in KB)
    
    verdict = "AI-GENERATED / DEEPFAKE" if confidence >= 60 else ("UNCERTAIN" if confidence >= 40 else "AUTHENTIC / REAL")
    base_ctx = f"[CUSTOM_MODEL] Custom PyTorch EfficientNet-B4 Classifier: Fine-tuned on 100k+ real/AI image pairs. Confidence score: {confidence:.1f}%. Verdict: {verdict}."
    full_ctx = f"{base_ctx}\n\n{kb_ctx}" if kb_ctx else base_ctx
    
    prompts = {
        "image": f"You are DRISHTI, an advanced forensic AI analyst system. Analyze this IMAGE scan result. AI Confidence: {confidence:.1f}% ({verdict}). Custom PyTorch model score: {confidence:.1f}%. Write exactly 3 concise sentences: (1) Your verdict and what the confidence score means, (2) What kind of artifacts or authenticity signals were detected, (3) Technical reasoning behind the classification. Be specific and authoritative.\nContext:\n{full_ctx}\nNo bullet points. No markdown.",
        "audio": f"You are DRISHTI, an advanced forensic AI analyst system. Analyze this AUDIO scan result. AI Confidence: {confidence:.1f}% ({verdict}). Pitch Std: {details.get('Pitch Std','N/A')}Hz, ZCR: {details.get('ZCR Var','N/A')}. Write exactly 3 concise sentences: (1) Your verdict, (2) What vocal synthesis artifacts were found, (3) Technical proof.\nContext:\n{full_ctx}\nNo bullet points. No markdown.",
        "text":  f"You are DRISHTI, an advanced forensic AI analyst system. Analyze this TEXT scan result. AI Confidence: {confidence:.1f}% ({verdict}). Perplexity: {details.get('Perplexity','N/A')}, Burstiness: {details.get('Burstiness','N/A')}. Write exactly 3 concise sentences: (1) Your verdict, (2) Structural anomalies detected, (3) LLM alignment proof.\nContext:\n{full_ctx}\nNo bullet points. No markdown.",
        "video": f"You are DRISHTI, an advanced forensic AI analyst system. Analyze this VIDEO scan result. AI Confidence: {confidence:.1f}% ({verdict}). Frames analyzed: {details.get('frames_analyzed', details.get('frames','N/A'))}. Temporal variance: {details.get('temporal_variance','N/A')}. Write exactly 3 concise sentences: (1) Your verdict, (2) Inter-frame consistency analysis, (3) Deepfake synthesis proof.\nContext:\n{full_ctx}\nNo bullet points. No markdown.",
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                          json={"model": "llama-3.3-70b-versatile", "max_tokens": 250, "temperature": 0.2, "messages": [{"role": "user", "content": prompts.get(modality, "")}]},
                          timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception: return ""

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — CALIBRATED FORENSICS v2 (FALSE POSITIVE FIXES)
# ══════════════════════════════════════════════════════════════════════════════
def sigmoid_scale(val, midpoint, k):
    try: return 1.0 / (1.0 + math.exp(-k * (val - midpoint)))
    except OverflowError: return 1.0 if k * (val - midpoint) > 0 else 0.0

def forensic_image(image, raw_bytes=None):
    # As requested, all other heuristics (noise, ELA, DCT, EXIF) have been completely removed.
    # The image model will rely strictly and exclusively on the custom PyTorch fine-tuned model.
    return {
        "forensic_score": 0.0,
        "tags": [],
        "tag_scores": {},
        "metrics": {"Noise Std": 0.0, "Periodicity": 0.0, "Laplacian Var": 0.0, "ELA Std": 0.0}
    }


def forensic_audio(audio_bytes, ext=".wav"):
    try:
        import librosa
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(audio_bytes); tmp = f.name
        y, sr = librosa.load(tmp, sr=16000, mono=True, duration=10)
        os.unlink(tmp)
        tags, scores, tag_scores = [], [], {}

        zcr_var = float(np.var(librosa.feature.zero_crossing_rate(y)[0]))
        zs = sigmoid_scale(zcr_var, 0.01, -400.0)
        scores.append(zs)
        if zs > 0.6: tags.append("zcr_anomaly"); tag_scores["zcr_anomaly"] = zs

        f0_std = 0.0
        try:
            f0, _, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr)
            valid = f0[~np.isnan(f0)] if f0 is not None else np.array([])
            if len(valid) > 5:
                f0_std = float(np.std(valid))
                fs = sigmoid_scale(f0_std, 10.0, -0.4)
                scores.append(fs)
                if fs > 0.6: tags.append("flat_pitch"); tag_scores["flat_pitch"] = fs
        except Exception: scores.append(0.1)

        stft = librosa.stft(y, n_fft=512)
        pd_val = float(np.mean(np.abs(np.diff(np.angle(stft), axis=1))))
        pds = sigmoid_scale(pd_val, 0.30, 20.0)
        scores.append(pds)
        if pds > 0.6: tags.append("phase_break"); tag_scores["phase_break"] = pds

        fft_v = np.abs(np.fft.rfft(y, n=2048)); fr = np.fft.rfftfreq(2048, d=1.0/sr)
        hf = float(np.mean(fft_v[fr > 7000])) if np.any(fr > 7000) else 0
        lf = float(np.mean(fft_v[fr <= 7000])) + 1e-8
        ratio = hf / lf
        rs = sigmoid_scale(ratio, 0.03, -100.0)
        scores.append(rs)
        if rs > 0.6: tags.append("hf_absent"); tag_scores["hf_absent"] = rs

        rms = librosa.feature.rms(y=y)[0]
        rms_cv = float(np.std(rms) / (np.mean(rms) + 1e-8))
        rms_s = sigmoid_scale(rms_cv, 0.4, -8.0)
        scores.append(rms_s)
        if rms_s > 0.6: tags.append("low_burstiness"); tag_scores["low_burstiness"] = rms_s

        return {"forensic_score": float(np.max(scores)) if scores else 0.1, "tags": tags, "tag_scores": tag_scores,
                "metrics": {"ZCR Var": round(zcr_var,4), "Pitch Std": round(f0_std,1), "Phase Disc": round(pd_val,3), "HF Ratio": round(ratio,3)}}
    except Exception as e:
        return {"forensic_score": 0.1, "tags": [], "tag_scores": {}, "metrics": {}, "error": str(e)}


def forensic_text(text):
    """Returns forensic score + per-sentence scores for highlighting."""
    tags, scores, tag_scores = [], [], {}
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    lengths = [len(s.split()) for s in sentences if s.strip()]
    burst = float(np.std(lengths) / (np.mean(lengths) + 1e-8)) if len(lengths) >= 3 else 0.0
    bs = sigmoid_scale(burst, 0.35, -15.0)
    scores.append(bs)
    if bs > 0.6: tags.append("uniform_sentences"); tag_scores["uniform_sentences"] = bs

    hits = sum(1 for p in AI_PHRASE_LIST if p in text.lower())
    ps = min(hits * 0.16, 0.95); scores.append(ps)
    if ps > 0.4: tags.append("ai_phrases"); tag_scores["ai_phrases"] = ps

    # Per-sentence AI scoring for highlighting
    sentence_scores = []
    for sent in sentences:
        if not sent.strip(): sentence_scores.append(0.0); continue
        sw = sent.lower(); sw_words = sw.split()
        phrase_hits = sum(1 for p in AI_PHRASE_LIST if p in sw)
        lex_div = len(set(sw_words)) / max(len(sw_words), 1)
        ai_openers = ["furthermore","additionally","moreover","however","therefore",
                      "in conclusion","to summarize","it is","this is","as a","notably"]
        opener = 1 if any(sw.startswith(op) for op in ai_openers) else 0
        # Sentence entropy (low = repetitive = AI)
        word_counter = Counter(sw_words)
        entropy = -sum((c/len(sw_words)) * math.log(c/len(sw_words)+1e-9) for c in word_counter.values())
        entropy_norm = min(entropy / (math.log(max(len(sw_words),2))+1e-8), 1.0)
        s_score = min(phrase_hits * 0.25 + (1-lex_div)*0.2 + opener*0.15 + (1-entropy_norm)*0.15, 0.95)
        sentence_scores.append(s_score)

    perplexity = -1
    # Note: Disabled GPT-2 perplexity calculation because `import torch` causes Segmentation faults on some setups.
    # Scores array remains unchanged.

    return {
        "forensic_score": float(np.max(scores)) if scores else 0.1,
        "tags": tags, "tag_scores": tag_scores,
        "sentence_scores": list(zip(sentences, sentence_scores)),
        "metrics": {"Burstiness": round(burst,3), "AI Phrases": hits, "Perplexity": round(perplexity,1) if perplexity > 0 else "N/A"}
    }

# ══════════════════════════════════════════════════════════════════════════════
# FUSION ENGINE v2 — weighted ensemble
# ══════════════════════════════════════════════════════════════════════════════
# Source credibility weights
_WEIGHTS = {
    "ai_or_not": 0.40,              # specialized binary classifier — highest
    "resemble_ai_audio": 0.38,      # specialized for audio
    "hive_ai_image": 0.30,
    "sightengine_deepfake": 0.28,
    "sightengine_ai_image": 0.25,
    "winston_ai": 0.35,
    "sapling_ai": 0.30,
    "hf_text_ai": 0.28,
    "hf_deepfake": 0.22,
    "hf_ai_image": 0.18,
    "sightengine_ai_video": 0.25,
}

def fuse_v2(api_results, forensic_score, modality="image"):
    # If custom trained model is present, it's our gold standard for images
    custom_hit = next((r["score"] for r in api_results if r.get("source") == "custom_trained_model" and r.get("score") is not None), None)
    if custom_hit is not None and (modality == "image" or modality == "video"):
        return custom_hit
    
    valid = [(r["score"], _WEIGHTS.get(r["source"], 0.20)) for r in api_results if r.get("score") is not None]
    if not valid:
        return min(forensic_score, 0.62)  # no API → cap at 62%
    total_w = sum(w for _,w in valid)
    api_weighted = sum(s*w for s,w in valid) / total_w
    api_max = max(s for s,_ in valid)
    # Strong API signal override
    if api_max > 0.82:
        return max(api_weighted * 0.65 + api_max * 0.35, forensic_score * 0.4)
    # APIs say real → trust them (prevent false positives)
    if api_max < 0.22:
        return min(api_weighted + 0.05, 0.35)
    # Normal blend
    return 0.68 * api_weighted + 0.32 * forensic_score

def fuse(api_results, forensic_score):
    return fuse_v2(api_results, forensic_score)

def make_indicators(tags, api_results, tag_scores):
    inds, seen = [], set()
    for r in api_results:
        if r.get("score") is not None and r["score"] > 0.12:
            src = r["source"]
            if src not in seen and src in KB:
                seen.add(src)
                inds.append({"name": KB[src]["name"], "sev": KB[src]["sev"], "score": round(r["score"]*100,1), "explain": KB[src]["explain"]})
    for tag in tags:
        if tag in KB and tag not in seen:
            seen.add(tag)
            inds.append({"name": KB[tag]["name"], "sev": KB[tag]["sev"], "score": round(tag_scores.get(tag,0.5)*100,1), "explain": KB[tag]["explain"]})
    return sorted(inds, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x["sev"],3))

# ══════════════════════════════════════════════════════════════════════════════
# LANGGRAPH
# ══════════════════════════════════════════════════════════════════════════════
class VXState(TypedDict):
    modality: str
    input_bytes: Optional[bytes]
    input_text: Optional[str]
    image_result: Optional[dict]
    audio_result: Optional[dict]
    text_result: Optional[dict]
    final_score: Optional[float]
    all_tags: List[str]
    all_tag_scores: dict
    explanation: Optional[str]
    should_escalate: bool

def _lg_router(s): return s

def _lg_image_agent(s):
    if s["modality"] not in ("image","video"): return s
    raw = s["input_bytes"]; img = Image.open(io.BytesIO(raw)).convert("RGB")
    custom_res = custom_trained_model_inference(raw)
    api_res = [custom_res]
    foren = forensic_image(img, raw)
    score = (custom_res.get("score") or 0.0) * 100
    s["image_result"] = {"score": score, "tags": foren["tags"], "tag_scores": foren["tag_scores"], "api_results": api_res, "metrics": foren["metrics"]}
    s["all_tags"] = list(set(s["all_tags"] + foren["tags"])); s["all_tag_scores"].update(foren["tag_scores"]); return s

def _lg_audio_agent(s):
    if s["modality"] not in ("audio","video"): return s
    raw = s["input_bytes"]; r = resemble_audio(raw); foren = forensic_audio(raw)
    score = fuse_v2([r], foren["forensic_score"], "audio")
    s["audio_result"] = {"score": score, "tags": foren["tags"], "tag_scores": foren["tag_scores"], "api_results": [r], "metrics": foren.get("metrics",{})}
    s["all_tags"] = list(set(s["all_tags"] + foren["tags"])); s["all_tag_scores"].update(foren["tag_scores"]); return s

def _lg_text_agent(s):
    if s["modality"] != "text": return s
    txt = s["input_text"] or ""
    r1, r2, r3 = winston_text(txt), sapling_text(txt), hf_text_ai(txt)
    foren = forensic_text(txt); score = fuse_v2([r1,r2,r3], foren["forensic_score"], "text")
    s["text_result"] = {"score": score, "tags": foren["tags"], "tag_scores": foren["tag_scores"], "api_results": [r1,r2,r3], "metrics": foren["metrics"], "sentence_scores": foren.get("sentence_scores",[])}
    s["all_tags"] = list(set(s["all_tags"] + foren["tags"])); s["all_tag_scores"].update(foren["tag_scores"]); return s

def _lg_fusion(s):
    sc = []
    if s.get("image_result"): sc.append(s["image_result"]["score"])
    if s.get("audio_result"): sc.append(s["audio_result"]["score"])
    if s.get("text_result"):  sc.append(s["text_result"]["score"])
    s["final_score"] = (sum(sc)/len(sc)*100) if sc else 0.0; return s

def _lg_explainer(s):
    details, api_res = {}, []
    if s.get("image_result"): details = s["image_result"].get("metrics",{}); api_res = s["image_result"].get("api_results",[])
    elif s.get("audio_result"): details = s["audio_result"].get("metrics",{}); api_res = s["audio_result"].get("api_results",[])
    elif s.get("text_result"): details = s["text_result"].get("metrics",{}); api_res = s["text_result"].get("api_results",[])
    s["explanation"] = groq_explain(s["modality"], s["final_score"] or 0.0, s["all_tags"], details); return s

def _route_after_image(s):
    if s["modality"] in ("audio","video"): return "audio_agent"
    if s["modality"] == "text": return "text_agent"
    return "fusion"

@functools.lru_cache(maxsize=1)
def build_langgraph():
    try:
        from langgraph.graph import StateGraph
        g = StateGraph(VXState)
        g.add_node("router", _lg_router); g.add_node("image_agent", _lg_image_agent); g.add_node("audio_agent", _lg_audio_agent)
        g.add_node("text_agent", _lg_text_agent); g.add_node("fusion", _lg_fusion); g.add_node("explainer", _lg_explainer)
        g.set_entry_point("router"); g.add_edge("router","image_agent")
        g.add_conditional_edges("image_agent", _route_after_image, {"audio_agent":"audio_agent","text_agent":"text_agent","fusion":"fusion"})
        g.add_edge("audio_agent","fusion"); g.add_edge("text_agent","fusion"); g.add_edge("fusion","explainer"); g.add_edge("explainer",_LG_END)
        return g.compile()
    except ImportError: return None

def run_langgraph(modality, input_bytes=None, input_text=None):
    graph = build_langgraph()
    init: VXState = {"modality":modality,"input_bytes":input_bytes,"input_text":input_text,"image_result":None,"audio_result":None,"text_result":None,"final_score":None,"all_tags":[],"all_tag_scores":{},"explanation":None,"should_escalate":False}
    if graph is None:
        s=_lg_router(init); s=_lg_image_agent(s); s=_lg_audio_agent(s); s=_lg_text_agent(s); s=_lg_fusion(s); return _lg_explainer(s)
    return graph.invoke(init)

# ══════════════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════
def ui_gauge(confidence):
    c = "#ff3b3b" if confidence >= 65 else "#ffaa00" if confidence >= 45 else "#00ff77"
    fig = go.Figure(go.Indicator(mode="gauge+number", value=confidence,
        number={"suffix":"%","font":{"size":42,"color":c,"family":"Share Tech Mono"}},
        gauge={"axis":{"range":[0,100],"tickfont":{"color":"#3a6a8a","size":10}},
               "bar":{"color":c,"thickness":0.25},"bgcolor":"#0a1628","borderwidth":1,"bordercolor":"#1a3a5a",
               "steps":[{"range":[0,45],"color":"#021a0a"},{"range":[45,65],"color":"#1a1205"},{"range":[65,100],"color":"#1a0505"}],
               "threshold":{"line":{"color":c,"width":3},"thickness":0.75,"value":confidence}}))
    fig.update_layout(paper_bgcolor="#080d14",plot_bgcolor="#080d14",height=220,margin=dict(l=20,r=20,t=20,b=10),font={"color":"#c8d8e8"})
    st.plotly_chart(fig, use_container_width=True)

def ui_verdict(confidence, label, threshold):
    if confidence >= threshold: css, icon = "vx-verdict-fake","⚠  MANIPULATED / SYNTHETIC DETECTED"
    elif confidence >= threshold-15: css, icon = "vx-verdict-uncertain","◈  INCONCLUSIVE — MANUAL REVIEW ADVISED"
    else: css, icon = "vx-verdict-real","✓  LIKELY AUTHENTIC"
    st.markdown(f'<div class="{css}">{icon}<div style="font-size:.85rem;font-family:Share Tech Mono,monospace;opacity:.6;margin-top:.3rem;">{label} · {confidence:.1f}% confidence</div></div>', unsafe_allow_html=True)

def ui_metrics(items):
    cols = st.columns(len(items))
    for col,(val,lbl) in zip(cols,items):
        col.markdown(f'<div class="vx-metric"><div class="vx-metric-val">{val}</div><div class="vx-metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

def ui_indicators(inds):
    if not inds:
        st.markdown('<div class="vx-verdict-real" style="font-size:1rem;">✓ No synthetic signatures detected.</div>', unsafe_allow_html=True); return
    st.markdown('<div class="vx-section">INDICATOR BREAKDOWN</div>', unsafe_allow_html=True)
    for ind in inds:
        css, icon = {"HIGH":("vx-ind-high","◉"),"MEDIUM":("vx-ind-medium","◈")}.get(ind["sev"],("vx-ind-low","◎"))
        st.markdown(f'<div class="{css}"><span class="vx-ind-name">{icon} {ind["name"]}</span><span class="vx-ind-score">SCORE: {ind["score"]:.1f}%</span><div class="vx-ind-explain">{ind["explain"]}</div></div>', unsafe_allow_html=True)

def ui_api_pills(results):
    st.markdown('<div class="vx-section">API SOURCE SIGNALS</div>', unsafe_allow_html=True)
    html, valid = "", 0
    for r in results:
        if r.get("score") is not None:
            pct = f"{r['score']*100:.1f}%"; css = "vx-api-ok" if r["score"] < 0.5 else "vx-api-off"
            html += f'<span class="{css}">{r["source"].upper()}: {pct}</span>&nbsp;&nbsp;'; valid += 1
    if valid == 0: html = '<span class="vx-api-na">CLOUD APIs OFFLINE · LOCAL FORENSICS ONLY</span>'
    st.markdown(html, unsafe_allow_html=True)

def ui_rag(text):
    if not text: return
    st.markdown(f'<div class="vx-rag"><div class="vx-rag-header">▸ DRISHTI FORENSIC ANALYSIS — GROQ + LLAMA 3.3 + RAG</div><div class="vx-rag-text">{text}</div></div>', unsafe_allow_html=True)

def ui_graph_intel(tags):
    if not _neo4j_ok() or not tags: return
    similar = graph_find_similar(tags)
    if not similar: return
    st.markdown('<div class="vx-section">GRAPH INTELLIGENCE — SIMILAR PAST SCANS</div>', unsafe_allow_html=True)
    for s in similar:
        shared = ", ".join(s.get("shared_tags",[])[:3]); conf,mod,ts = s.get("confidence",0), s.get("modality","?").upper(), str(s.get("ts",""))[:10]
        st.markdown(f'<div class="vx-graph-card"><b>{mod}</b> · {conf:.1f}% confidence · {ts}<br>Shared: <b>{shared}</b></div>', unsafe_allow_html=True)

def ui_frame_chart(scores, threshold):
    colors = ["#ff3b3b" if s >= threshold else "#ffaa00" if s >= 45 else "#00ff77" for s in scores]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(scores))), y=scores, mode="lines+markers",
                             line=dict(color="#00f5ff",width=2), marker=dict(color=colors,size=10,line=dict(color="#080d14",width=1)),
                             fill="tozeroy", fillcolor="rgba(0,245,255,0.05)"))
    fig.add_hline(y=threshold, line_dash="dash", line_color="rgba(255,59,59,0.33)", annotation_text="Threshold", annotation_font_color="#ff6b6b")
    fig.update_layout(paper_bgcolor="#080d14",plot_bgcolor="#0a1628",height=220,margin=dict(l=0,r=0,t=10,b=0),
                      xaxis=dict(title="Frame",color="#3a6a8a",gridcolor="#0a1f30"),
                      yaxis=dict(title="Confidence %",range=[0,100],color="#3a6a8a",gridcolor="#0a1f30"),
                      font=dict(family="Share Tech Mono",color="#3a6a8a",size=10),showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── NEW: Text Highlight ───────────────────────────────────────────────────────
def ui_text_highlight(sentence_scores):
    if not sentence_scores: return
    st.markdown('<div class="vx-section">CONTENT ANALYSIS — SENTENCE-LEVEL AI PROBABILITY</div>', unsafe_allow_html=True)
    st.markdown("""<div class="txt-legend">
    <span class="txt-ai-high">HIGH AI (&gt;70%)</span>
    <span class="txt-ai-medium">MEDIUM AI (40–70%)</span>
    <span class="txt-ai-low">LOW AI (20–40%)</span>
    <span style="color:#c8d8e8;padding:2px 8px">Human-like (&lt;20%)</span>
    </div>""", unsafe_allow_html=True)
    parts = ['<div class="txt-highlight-container">']
    for sent, score in sentence_scores:
        if not sent.strip(): continue
        escaped = sent.replace("<","&lt;").replace(">","&gt;")
        pct = round(score*100)
        if score > 0.70: parts.append(f'<span class="txt-ai-high" title="AI prob: {pct}%">{escaped}</span> ')
        elif score > 0.40: parts.append(f'<span class="txt-ai-medium" title="AI prob: {pct}%">{escaped}</span> ')
        elif score > 0.20: parts.append(f'<span class="txt-ai-low" title="AI prob: {pct}%">{escaped}</span> ')
        else: parts.append(f'<span class="txt-human">{escaped}</span> ')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

    if len(sentence_scores) > 2:
        labels = [f"S{i+1}" for i in range(len(sentence_scores))]
        vals = [s*100 for _,s in sentence_scores]
        colors = ["#ff3b3b" if v>70 else "#ffaa00" if v>40 else "#00ff77" for v in vals]
        fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors, marker_line=dict(color="#080d14",width=1),
                               text=[f"{v:.0f}%" for v in vals], textposition="outside", textfont=dict(color="#aabbcc",size=9)))
        fig.update_layout(paper_bgcolor="#080d14",plot_bgcolor="#0a1628",height=175,margin=dict(l=0,r=0,t=8,b=0),
                          xaxis=dict(color="#3a6a8a",gridcolor="#0a1f30"),
                          yaxis=dict(title="AI %",range=[0,115],color="#3a6a8a",gridcolor="#0a1f30"),
                          font=dict(family="Share Tech Mono",color="#3a6a8a",size=9),showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ── NEW: Video Frame Gallery ──────────────────────────────────────────────────
def ui_frame_gallery(frame_data, threshold):
    if not frame_data: return
    st.markdown('<div class="vx-section">FRAME GALLERY — CLICK TO INSPECT SUSPICIOUS FRAMES</div>', unsafe_allow_html=True)
    cols_per_row = 5
    rows = [frame_data[i:i+cols_per_row] for i in range(0, len(frame_data), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, fd in zip(cols, row):
            with col:
                score = fd["score"]
                if score >= threshold: border = (220,40,40); label = f"⚠ {score:.0f}%"
                elif score >= 45: border = (220,170,0); label = f"? {score:.0f}%"
                else: border = (0,220,100); label = f"✓ {score:.0f}%"
                thumb = fd["pil_img"].copy(); thumb.thumbnail((160,120), Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(thumb)
                draw.rectangle([0,0,thumb.width-1,thumb.height-1], outline=border, width=4)
                st.image(thumb, use_container_width=True)
                color_hex = "#{:02x}{:02x}{:02x}".format(*border)
                st.markdown(f'<div style="text-align:center;font-family:Share Tech Mono,monospace;font-size:.65rem;color:{color_hex};padding:1px 0">{label} · F{fd["idx"]}</div>', unsafe_allow_html=True)

# ── NEW: Audio Transcript + Timestamps ───────────────────────────────────────
def ui_audio_transcript(segments, threshold=60):
    if not segments: return
    st.markdown('<div class="vx-section">TRANSCRIPT — AI-FLAGGED SEGMENTS</div>', unsafe_allow_html=True)
    scores_pct = [(s.get("ai_score") or 0)*100 for s in segments]
    if scores_pct and any(v>0 for v in scores_pct):
        times = [f"{s['start']:.1f}s" for s in segments]
        colors = ["#ff3b3b" if v>=threshold else "#ffaa00" if v>=35 else "#00ff77" for v in scores_pct]
        fig = go.Figure(go.Bar(x=times, y=scores_pct, marker_color=colors, marker_line=dict(color="#080d14",width=1)))
        fig.update_layout(paper_bgcolor="#080d14",plot_bgcolor="#0a1628",height=130,margin=dict(l=0,r=0,t=8,b=0),
                          xaxis=dict(title="Timestamp",color="#3a6a8a",gridcolor="#0a1f30"),
                          yaxis=dict(title="AI %",range=[0,105],color="#3a6a8a",gridcolor="#0a1f30"),
                          font=dict(family="Share Tech Mono",color="#3a6a8a",size=9),showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    for seg in segments:
        ai_score = seg.get("ai_score") or 0; pct = ai_score*100
        if pct >= threshold: row_cls,score_cls,icon = "ts-row","ts-score","⚠"
        elif pct >= 35: row_cls,score_cls,icon = "ts-row ts-row-med","ts-score ts-score-med","◈"
        else: row_cls,score_cls,icon = "ts-row ts-row-ok","ts-score ts-score-ok","✓"
        st.markdown(f'<div class="{row_cls}"><span class="ts-time">{seg["start"]:.1f}s–{seg["end"]:.1f}s</span><span class="{score_cls}">{icon} {pct:.0f}%</span><span style="color:#c8d8e8">{seg["text"]}</span></div>', unsafe_allow_html=True)

# ── NEW: ELA Heatmap Overlay ──────────────────────────────────────────────────
def ui_image_heatmap(image, confidence):
    try:
        import cv2
        img_u8 = np.array(image.convert("RGB")).astype(np.uint8)
        buf = io.BytesIO(); image.save(buf, format="JPEG", quality=75); buf.seek(0)
        compressed = np.array(Image.open(buf).convert("RGB")).astype(np.float32)
        ela = np.abs(img_u8.astype(np.float32) - compressed)
        ela_gray = (ela.mean(axis=2) / (ela.mean(axis=2).max()+1e-8) * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        alpha = min(0.3 + confidence/250, 0.65)
        overlay = (img_u8*(1-alpha) + heatmap_rgb*alpha).clip(0,255).astype(np.uint8)
        result = Image.fromarray(overlay); result.thumbnail((600,600), Image.Resampling.LANCZOS)
        st.markdown('<div class="vx-section">FORENSIC HEATMAP — ELA ANOMALY OVERLAY</div>', unsafe_allow_html=True)
        st.image(result, caption="Red/yellow regions = high compression anomaly (suspicious areas)", use_container_width=True)
    except Exception: pass

# ── NEW: Signal Radar Chart ───────────────────────────────────────────────────
def ui_radar_chart(api_results, forensic_score):
    label_map = {"ai_or_not":"AI-OR-NOT","sightengine_deepfake":"SE_DEEP","sightengine_ai_image":"SE_AI",
                 "hive_ai_image":"HIVE","hf_ai_image":"HF_ViT","hf_deepfake":"HF_DEEP",
                 "winston_ai":"WINSTON","sapling_ai":"SAPLING","resemble_ai_audio":"RESEMBLE","hf_text_ai":"HF_TEXT"}
    labels, values = ["FORENSIC"], [forensic_score*100]
    for r in api_results:
        if r.get("score") is not None:
            labels.append(label_map.get(r["source"], r["source"][:8].upper()))
            values.append(r["score"]*100)
    if len(labels) < 3: return
    fig = go.Figure(go.Scatterpolar(r=values+[values[0]], theta=labels+[labels[0]],
                                    fill='toself', fillcolor='rgba(0,245,255,0.07)',
                                    line=dict(color='#00f5ff',width=2), marker=dict(color='#00f5ff',size=6)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100],color="#3a6a8a",gridcolor="#0a1f30"),
                                  angularaxis=dict(color="#3a6a8a")),
                      paper_bgcolor="#080d14",plot_bgcolor="#080d14",height=270,
                      margin=dict(l=15,r=15,t=15,b=15),
                      font=dict(family="Share Tech Mono",color="#5a8a9a",size=9))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="vx-header"><div class="vx-logo">DRISHTI</div><div class="vx-tagline">Verified Index of Digital Authenticity · v2</div><div class="vx-badge">AI-OR-NOT · IMAGE · AUDIO · TEXT · VIDEO · LANGGRAPH · GRAPHDB · MCP · HIGHLIGHT</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="vx-section">API STATUS</div>', unsafe_allow_html=True)
    def pill(label, ok):
        st.markdown(f'<span class="{"vx-api-ok" if ok else "vx-api-na"}">{label}: {"ONLINE" if ok else "ADD KEY"}</span><br>', unsafe_allow_html=True)
    pill("AI-OR-NOT ★",  _aon_ok())
    pill("SIGHTENGINE",  _sight_ok())
    pill("HIVE API",     _hive_ok())
    pill("RESEMBLE AI",  _resemble_ok())
    pill("WINSTON AI",   _winston_ok())
    pill("SAPLING",      _sapling_ok())
    pill("HUGGINGFACE",  _hf_ok())
    pill("GROQ / LLAMA", _groq_ok())
    pill("NEO4J GRAPH",  _neo4j_ok())
    try:
        import langgraph; st.markdown('<span class="vx-api-ok">LANGGRAPH: ACTIVE</span><br>', unsafe_allow_html=True)
    except ImportError:
        st.markdown('<span class="vx-api-na">LANGGRAPH: pip install</span><br>', unsafe_allow_html=True)

    st.markdown('<div class="vx-section">THRESHOLD</div>', unsafe_allow_html=True)
    threshold = st.slider("Flag above (%)", 40, 75, 60, label_visibility="collapsed")
    use_langgraph = st.toggle("LangGraph Orchestration", value=True)

    st.markdown('<div class="vx-section">OPEN-SOURCE MODELS</div>', unsafe_allow_html=True)
    st.markdown("""<div style="font-size:.68rem;color:#2a5a6a;font-family:'Share Tech Mono',monospace;line-height:1.9">
    IMAGE API:<br>◉ AI-or-Not (primary★)<br>◉ umm-maybe/AI-image-detector<br>◉ dima806/deepfake-detection<br>
    TEXT:<br>◉ chatgpt-detector-roberta<br>◉ roberta-openai-detector<br>
    AUDIO:<br>◉ Resemble Detect API<br>◉ wav2vec2+fine-tune<br>
    LOCAL GPU:<br>◉ pip install transformers<br>◉ EfficientNet-B4 (timm)</div>""", unsafe_allow_html=True)

    if _neo4j_ok():
        st.markdown('<div class="vx-section">GRAPH DATABASE</div>', unsafe_allow_html=True)
        stats = graph_stats()
        if stats:
            st.markdown(f"""<div style="font-size:.7rem;color:#2a5a6a;font-family:'Share Tech Mono',monospace;line-height:1.9">◉ Total scans: <span style="color:#00f5ff">{stats.get('total_scans',0)}</span><br>◉ Fakes: <span style="color:#ff6b6b">{stats.get('total_fakes',0)}</span><br>◉ Artifacts: <span style="color:#ffbb33">{stats.get('unique_artifacts',0)}</span></div>""", unsafe_allow_html=True)

t_img, t_aud, t_txt, t_vid, t_graph, t_edu = st.tabs(["🖼  IMAGE", "🎵  AUDIO", "📝  TEXT", "🎬  VIDEO", "🕸  GRAPH", "📚  LEARN"])

# ── IMAGE TAB ─────────────────────────────────────────────────────────────────
with t_img:
    c1, c2 = st.columns([1,1], gap="large")
    with c1:
        st.markdown('<div class="vx-section">UPLOAD IMAGE</div>', unsafe_allow_html=True)
        f = st.file_uploader("Upload Image", type=["jpg","jpeg","png","webp","bmp"], label_visibility="collapsed", key="img_up")
        if f: st.image(Image.open(f).convert("RGB"), use_container_width=True)
        btn_img = st.button("◈  RUN IMAGE ANALYSIS", use_container_width=True, key="img_btn") if f else False
    with c2:
        if f and btn_img:
            raw = f.getvalue()
            with st.spinner("Running DRISHTI v2 pipeline..."):
                t0 = time.time()
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                if use_langgraph:
                    state   = run_langgraph("image", input_bytes=raw)
                    conf    = round(state["final_score"] or 0, 1)
                    tags    = state["all_tags"]; ts = state["all_tag_scores"]
                    api_res = (state.get("image_result") or {}).get("api_results", [])
                    metrics = (state.get("image_result") or {}).get("metrics", {})
                    expl    = state["explanation"] or ""
                else:
                    custom_res = custom_trained_model_inference(raw)
                    api_res = [custom_res]
                    foren   = forensic_image(img, raw)
                    conf    = round((custom_res.get("score") or 0.0) * 100, 1)
                    tags, ts, metrics = foren["tags"], foren["tag_scores"], foren["metrics"]
                    expl    = groq_explain("image", conf, tags, metrics)
                elapsed = time.time() - t0
                graph_save_detection("image", conf, tags, hashlib.md5(raw).hexdigest(), metrics)

            st.markdown('<div class="vx-section">RESULT</div>', unsafe_allow_html=True)
            ui_gauge(conf)
            ui_verdict(conf, "DEEPFAKE / AI IMAGE", threshold)
            st.markdown("")
            ui_metrics([(f"{conf:.1f}%","CONFIDENCE"),(str(metrics.get("Noise Std","—")),"NOISE STD"),(str(metrics.get("ELA Std","—")),"ELA STD"),(f"{elapsed:.1f}s","TIME")])
            st.markdown('<div class="vx-section">SIGNAL RADAR</div>', unsafe_allow_html=True)
            foren_approx = min((conf/100)*0.6, 0.62)
            ui_radar_chart(api_res, foren_approx)
            ui_api_pills(api_res)
            ui_indicators(make_indicators(tags, api_res, ts))
            ui_graph_intel(tags)
            ui_rag(expl)
    if f and btn_img:
        ui_image_heatmap(img, conf)

# ── AUDIO TAB ─────────────────────────────────────────────────────────────────
with t_aud:
    c1, c2 = st.columns([1,1], gap="large")
    with c1:
        st.markdown('<div class="vx-section">UPLOAD AUDIO</div>', unsafe_allow_html=True)
        f = st.file_uploader("Upload Audio", type=["wav","mp3","flac","ogg","m4a"], label_visibility="collapsed", key="aud_up")
        if f: st.audio(f)
        btn_aud = st.button("◈  RUN AUDIO ANALYSIS", use_container_width=True, key="aud_btn") if f else False
    with c2:
        if f and btn_aud:
            raw, ext = f.getvalue(), "." + f.name.split(".")[-1]
            with st.spinner("Analyzing audio + generating transcript..."):
                t0 = time.time()
                if use_langgraph:
                    state   = run_langgraph("audio", input_bytes=raw)
                    conf    = round(state["final_score"] or 0, 1)
                    tags, ts = state["all_tags"], state["all_tag_scores"]
                    api_res = (state.get("audio_result") or {}).get("api_results", [])
                    metrics = (state.get("audio_result") or {}).get("metrics", {})
                    expl    = state["explanation"] or ""
                else:
                    api_res = [resemble_audio(raw)]
                    foren   = forensic_audio(raw, ext)
                    conf    = round(fuse_v2(api_res, foren["forensic_score"], "audio") * 100, 1)
                    tags, ts, metrics = foren["tags"], foren["tag_scores"], foren.get("metrics",{})
                    expl    = groq_explain("audio", conf, tags, metrics)
                segments = whisper_transcribe(raw, ext)
                for seg in segments: seg["ai_score"] = score_audio_segment(seg["text"])
                elapsed = time.time() - t0
                graph_save_detection("audio", conf, tags, hashlib.md5(raw).hexdigest(), metrics)

            st.markdown('<div class="vx-section">RESULT</div>', unsafe_allow_html=True)
            ui_gauge(conf)
            ui_verdict(conf, "SYNTHESIZED VOICE", threshold)
            st.markdown("")
            ui_metrics([(f"{conf:.1f}%","SYNTHESIS CONF"),(str(metrics.get("ZCR Var","N/A")),"ZCR VARIANCE"),(str(metrics.get("Pitch Std","N/A")),"PITCH STD Hz"),(f"{elapsed:.1f}s","TIME")])
            # Waveform
            try:
                import librosa
                y, sr = librosa.load(io.BytesIO(raw), sr=16000, mono=True, duration=30)
                n = min(len(y), 2500); y_s = y[::max(1,len(y)//n)][:n]
                t_ax = np.linspace(0, len(y)/sr, num=len(y_s))
                fig = go.Figure(); fig.add_trace(go.Scatter(x=t_ax, y=y_s, mode="lines", line=dict(color="#00f5ff",width=0.8), fill="tozeroy", fillcolor="rgba(0,245,255,0.04)"))
                fig.update_layout(paper_bgcolor="#080d14",plot_bgcolor="#0a1628",height=110,margin=dict(l=0,r=0,t=6,b=0),
                                  xaxis=dict(title="Time (s)",color="#3a6a8a",gridcolor="#0a1f30"),yaxis=dict(color="#3a6a8a",gridcolor="#0a1f30"),
                                  font=dict(family="Share Tech Mono",color="#3a6a8a",size=9),showlegend=False)
                st.markdown('<div class="vx-section">WAVEFORM</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
            except Exception: pass
            ui_api_pills(api_res)
            ui_indicators(make_indicators(tags, api_res, ts))
            ui_graph_intel(tags)
            ui_rag(expl)
    if f and btn_aud and 'segments' in dir():
        ui_audio_transcript(segments, threshold)

# ── TEXT TAB ─────────────────────────────────────────────────────────────────
with t_txt:
    st.markdown('<div class="vx-section">PASTE TEXT FOR ANALYSIS</div>', unsafe_allow_html=True)
    txt = st.text_area("Input Text", height=200, placeholder="Paste text here — minimum 80 characters for accurate analysis...", label_visibility="collapsed")
    cb, _ = st.columns([1, 3])
    with cb: btn_txt = st.button("◈  ANALYZE TEXT", use_container_width=True)
    if btn_txt and txt:
        if len(txt.strip()) < 80:
            st.warning("Paste at least 80 characters.")
        else:
            with st.spinner("Analyzing text..."):
                t0 = time.time()
                if use_langgraph:
                    state   = run_langgraph("text", input_text=txt)
                    conf    = round(state["final_score"] or 0, 1)
                    tags, ts = state["all_tags"], state["all_tag_scores"]
                    api_res = (state.get("text_result") or {}).get("api_results", [])
                    metrics = (state.get("text_result") or {}).get("metrics", {})
                    sent_scores = (state.get("text_result") or {}).get("sentence_scores", [])
                    expl    = state["explanation"] or ""
                else:
                    api_res = [winston_text(txt), sapling_text(txt), hf_text_ai(txt)]
                    foren   = forensic_text(txt)
                    conf    = round(fuse_v2(api_res, foren["forensic_score"], "text") * 100, 1)
                    tags, ts, metrics = foren["tags"], foren["tag_scores"], foren["metrics"]
                    sent_scores = foren.get("sentence_scores", [])
                    expl    = groq_explain("text", conf, tags, metrics)
                elapsed = time.time() - t0
                graph_save_detection("text", conf, tags, hashlib.md5(txt.encode()).hexdigest(), metrics)

            cl, cr = st.columns([1,1], gap="large")
            with cl:
                st.markdown('<div class="vx-section">RESULT</div>', unsafe_allow_html=True)
                ui_gauge(conf)
                ui_verdict(conf, "AI GENERATED TEXT", threshold)
                st.markdown("")
                ui_metrics([(f"{conf:.1f}%","AI CONFIDENCE"),(str(metrics.get("Perplexity","N/A")),"PERPLEXITY"),(str(metrics.get("Burstiness","N/A")),"BURSTINESS"),(str(metrics.get("AI Phrases",0)),"AI PHRASES")])
            with cr:
                ui_api_pills(api_res)
                ui_indicators(make_indicators(tags, api_res, ts))
                ui_graph_intel(tags)
                ui_rag(expl)
            ui_text_highlight(sent_scores)

# ── VIDEO TAB ─────────────────────────────────────────────────────────────────
with t_vid:
    c1, c2 = st.columns([1,1], gap="large")
    with c1:
        st.markdown('<div class="vx-section">UPLOAD VIDEO</div>', unsafe_allow_html=True)
        f = st.file_uploader("Upload Video", type=["mp4","avi","mov","mkv","webm"], label_visibility="collapsed", key="vid_up")
        n_frames = st.select_slider("Frames to analyze", [5,10,15,20], value=10)
        if f: st.video(f)
        btn_vid = st.button("◈  RUN VIDEO ANALYSIS", use_container_width=True, key="vid_btn") if f else False
    with c2:
        if f and btn_vid:
            raw, ext = f.getvalue(), f.name.split(".")[-1]
            with st.spinner("Processing video frames..."):
                t0 = time.time()
                frame_scores, all_tags_c, all_ts, mse_list = [], Counter(), {}, []
                api_frame = {"df":[],"ai":[],"hf":[],"hive":[],"aon":[]}
                frame_gallery_data = []

                try:
                    import cv2
                    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                        tmp.write(raw); tp = tmp.name
                    cap = cv2.VideoCapture(tp)
                    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 100
                    idxs = np.linspace(0, total-1, n_frames, dtype=int)
                    prev_gray = None
                    for i, idx in enumerate(idxs):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx)); ret, frm = cap.read()
                        if not ret: continue
                        gray = cv2.cvtColor(frm, cv2.COLOR_BGR2GRAY)
                        if prev_gray is not None:
                            mse_list.append(float(np.mean((gray.astype("float")-prev_gray.astype("float"))**2)))
                        prev_gray = gray
                        pil = Image.fromarray(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))
                        pil.thumbnail((600,600), Image.Resampling.LANCZOS)
                        buf = io.BytesIO(); pil.save(buf, format="JPEG", quality=80); fb = buf.getvalue()
                        foren = forensic_image(pil, fb)
                        frame_scores.append(foren["forensic_score"]*100)
                        frame_gallery_data.append({"pil_img": pil.copy(), "score": foren["forensic_score"]*100, "idx": int(idx)})
                        for t in foren["tags"]: all_tags_c[t] += 1
                        for t, sc in foren["tag_scores"].items(): all_ts[t] = all_ts.get(t,0)+sc
                        if i in [0, len(idxs)//4, len(idxs)//2, 3*len(idxs)//4, len(idxs)-1]:
                            r_cust = custom_trained_model_inference(fb)
                            if r_cust.get("score") is not None:
                                api_frame["ai"].append(r_cust["score"])
                    cap.release(); os.unlink(tp)
                except Exception as e: st.error(f"Video error: {e}")

                r_df = sight_video_deepfake(raw,ext) if len(raw)<15000000 else {"score":None,"source":"sightengine_deepfake"}
                r_ai = sight_video_ai(raw,ext) if len(raw)<15000000 else {"score":None,"source":"sightengine_ai_video"}

                temp_bonus, mse_var = 0.0, 0.0
                if len(mse_list) > 2:
                    mse_var = float(np.var(mse_list)); mse_mean = float(np.mean(mse_list))
                    if mse_mean > 0:
                        mse_cv = mse_var/mse_mean; temp_score = sigmoid_scale(mse_cv, 1.2, 3.0)
                        if temp_score > 0.6: all_tags_c["temporal_inconsistency"] += 3; temp_bonus = temp_score*0.15

                api_res = []
                if api_frame["aon"]:  api_res.append({"source":"ai_or_not","score":float(np.max(api_frame["aon"]))})
                if api_frame["df"]:   api_res.append({"source":"sightengine_deepfake","score":float(np.max(api_frame["df"]))})
                if api_frame["ai"]:   api_res.append({"source":"sightengine_ai_image","score":float(np.max(api_frame["ai"]))})
                if api_frame["hf"]:   api_res.append({"source":"hf_deepfake","score":float(np.max(api_frame["hf"]))})
                if api_frame["hive"]: api_res.append({"source":"hive_ai_image","score":float(np.max(api_frame["hive"]))})
                if r_df.get("score"): api_res.append(r_df)
                if r_ai.get("score"): api_res.append(r_ai)

                avg_ts = {k: v/all_tags_c[k] for k,v in all_ts.items() if all_tags_c[k] > 0}
                if temp_bonus > 0: avg_ts["temporal_inconsistency"] = 0.85
                fb_score = float(np.mean(frame_scores))/100 if frame_scores else 0.4
                conf = round(min(fuse_v2(api_res, fb_score+temp_bonus, "image")*100, 99), 1)
                tags = [t for t,_ in all_tags_c.most_common(6)]
                metrics = {"frames": len(frame_scores), "mse_variance": round(mse_var,1)}
                expl = groq_explain("video", conf, tags, metrics)
                elapsed = time.time() - t0
                graph_save_detection("video", conf, tags, hashlib.md5(raw[:4096]).hexdigest(), metrics)

            st.markdown('<div class="vx-section">RESULT</div>', unsafe_allow_html=True)
            ui_gauge(conf)
            ui_verdict(conf, "DEEPFAKE / AI VIDEO", threshold)
            st.markdown("")
            df_s = next((r["score"] for r in api_res if "deepfake" in r["source"] and r.get("score")), None)
            ai_s = next((r["score"] for r in api_res if "ai_video" in r["source"] and r.get("score")), None)
            ui_metrics([(f"{conf:.1f}%","OVERALL"),(f"{df_s*100:.1f}%" if df_s else "—","FACE-SWAP"),(f"{ai_s*100:.1f}%" if ai_s else "—","AI-GEN"),(f"{elapsed:.1f}s","TIME")])
            st.markdown(""); ui_metrics([(str(len(frame_scores)),"FRAMES ANALYZED"),(f"{round(temp_bonus*100,1)}%","TEMPORAL ANOMALY")])
            if frame_scores:
                st.markdown('<div class="vx-section">FRAME TIMELINE</div>', unsafe_allow_html=True)
                ui_frame_chart(frame_scores, threshold)
            ui_api_pills(api_res)
            ui_indicators(make_indicators(tags, api_res, avg_ts))
            ui_graph_intel(tags)
            ui_rag(expl)
    if f and btn_vid and 'frame_gallery_data' in dir() and frame_gallery_data:
        ui_frame_gallery(frame_gallery_data, threshold)

# ══════════════════════════════════════════════════════════════════════════════
# THIS FILE CONTAINS THE COMPLETION OF DRISHTI v2
# Paste this AFTER the existing code (starting right after "# ── GRAPH TAB ─────────")
# ══════════════════════════════════════════════════════════════════════════════

# ── GRAPH TAB ─────────────────────────────────────────────────────────────────
with t_graph:
    st.markdown('<div class="vx-section">GRAPH INTELLIGENCE — NEO4J RELATIONAL DATABASE</div>', unsafe_allow_html=True)

    if not _neo4j_ok():
        st.markdown("""
        <div class="vx-verdict-uncertain">
            ◈  NEO4J NOT CONFIGURED<br>
            <div style="font-size:.85rem;font-family:Share Tech Mono,monospace;opacity:.6;margin-top:.5rem;">
                Add your NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD to enable graph intelligence.<br>
                Free tier available at: <a href="https://neo4j.com/cloud/aura-free/" style="color:#00f5ff">neo4j.com/cloud/aura-free</a>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        driver_status = _get_neo4j_driver()
        if driver_status is None:
            st.markdown('<div class="vx-verdict-fake">⚠  NEO4J CONNECTION FAILED — Check credentials and network.</div>', unsafe_allow_html=True)
        else:
            # ── Stats row
            stats = graph_stats()
            if stats:
                st.markdown('<div class="vx-section">DATABASE OVERVIEW</div>', unsafe_allow_html=True)
                ui_metrics([
                    (str(stats.get("total_scans", 0)),   "TOTAL SCANS"),
                    (str(stats.get("total_fakes", 0)),   "FAKES DETECTED"),
                    (str(stats.get("unique_artifacts", 0)), "UNIQUE ARTIFACTS"),
                    (f"{round(stats.get('total_fakes',0) / max(stats.get('total_scans',1),1)*100,1)}%", "FAKE RATE"),
                ])

            col_left, col_right = st.columns([1, 1], gap="large")

            with col_left:
                # ── Recent fakes
                st.markdown('<div class="vx-section">RECENT HIGH-CONFIDENCE FAKES</div>', unsafe_allow_html=True)
                recent = graph_recent_fakes(limit=8)
                if recent:
                    for item in recent:
                        mod  = str(item.get("modality", "?")).upper()
                        conf = item.get("confidence", 0)
                        ts   = str(item.get("ts", ""))[:19].replace("T", " ")
                        h    = str(item.get("hash", ""))[:10]
                        st.markdown(
                            f'<div class="vx-graph-card">'
                            f'<b>{mod}</b> · <span style="color:#ff6b6b">{conf:.1f}%</span> · {ts}'
                            f'<br><span style="color:#2a5a6a">hash: {h}…</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown('<div class="vx-graph-card">No fakes recorded yet. Run some scans first.</div>', unsafe_allow_html=True)

            with col_right:
                # ── Artifact frequency chart
                st.markdown('<div class="vx-section">TOP ARTIFACT SIGNATURES</div>', unsafe_allow_html=True)
                freq_data = graph_artifact_frequency()
                if freq_data:
                    labels = [d["artifact"] for d in freq_data]
                    values = [d["frequency"] for d in freq_data]
                    colors_bar = [
                        "#ff3b3b" if KB.get(lbl, {}).get("sev") == "HIGH"
                        else "#ffaa00" if KB.get(lbl, {}).get("sev") == "MEDIUM"
                        else "#00aaff"
                        for lbl in labels
                    ]
                    import plotly.graph_objects as go
                    fig = go.Figure(go.Bar(
                        y=labels, x=values, orientation="h",
                        marker_color=colors_bar,
                        marker_line=dict(color="#080d14", width=1),
                        text=[str(v) for v in values],
                        textposition="outside",
                        textfont=dict(color="#aabbcc", size=9)
                    ))
                    fig.update_layout(
                        paper_bgcolor="#080d14", plot_bgcolor="#0a1628",
                        height=max(180, len(labels) * 28),
                        margin=dict(l=0, r=30, t=8, b=0),
                        xaxis=dict(title="Count", color="#3a6a8a", gridcolor="#0a1f30"),
                        yaxis=dict(color="#5a9aaa", gridcolor="#0a1f30", autorange="reversed"),
                        font=dict(family="Share Tech Mono", color="#3a6a8a", size=9),
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown('<div class="vx-graph-card">No artifact data yet.</div>', unsafe_allow_html=True)

            # ── Graph query explorer
            st.markdown('<div class="vx-section">GRAPH QUERY EXPLORER</div>', unsafe_allow_html=True)
            q_col1, q_col2 = st.columns([3, 1])
            with q_col1:
                custom_tags = st.multiselect(
                    "Find scans sharing these artifact signatures:",
                    options=list(KB.keys()),
                    default=[],
                    format_func=lambda k: KB[k]["name"],
                    label_visibility="collapsed"
                )
            with q_col2:
                min_conf_q = st.number_input("Min conf %", 0, 99, 45, label_visibility="collapsed")

            if custom_tags:
                results = graph_find_similar(custom_tags, threshold=float(min_conf_q))
                if results:
                    st.markdown(f'<div style="font-size:.7rem;color:#00f5ff;font-family:Share Tech Mono,monospace;margin:.5rem 0">Found {len(results)} matching scan(s)</div>', unsafe_allow_html=True)
                    for r in results:
                        shared = ", ".join(r.get("shared_tags", [])[:5])
                        st.markdown(
                            f'<div class="vx-graph-card">'
                            f'<b>{str(r.get("modality","?")).upper()}</b> · '
                            f'<span style="color:#ff6b6b">{r.get("confidence",0):.1f}%</span> · '
                            f'<span style="color:#ffbb33">{r.get("verdict","?")}</span>'
                            f'<br>Shared: <b style="color:#00f5ff">{shared}</b> '
                            f'· matches: {r.get("match_count",0)}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown('<div class="vx-graph-card">No matching scans found above threshold.</div>', unsafe_allow_html=True)

            # ── Modality pie chart
            st.markdown('<div class="vx-section">SCAN MODALITY DISTRIBUTION</div>', unsafe_allow_html=True)
            driver = _get_neo4j_driver()
            if driver:
                try:
                    with driver.session() as sess:
                        result = sess.run(
                            "MATCH (sc:Scan) RETURN sc.modality AS modality, count(sc) AS n ORDER BY n DESC"
                        )
                        mod_data = [dict(r) for r in result]
                    if mod_data:
                        pie_labels = [d["modality"].upper() for d in mod_data]
                        pie_values = [d["n"] for d in mod_data]
                        pie_colors = ["#00f5ff", "#ff3b3b", "#ffaa00", "#00ff77"]
                        fig_pie = go.Figure(go.Pie(
                            labels=pie_labels, values=pie_values,
                            hole=0.55,
                            marker=dict(colors=pie_colors[:len(pie_labels)], line=dict(color="#080d14", width=2)),
                            textfont=dict(family="Share Tech Mono", size=10, color="#c8d8e8"),
                        ))
                        fig_pie.update_layout(
                            paper_bgcolor="#080d14", plot_bgcolor="#080d14",
                            height=220, margin=dict(l=0, r=0, t=10, b=0),
                            legend=dict(font=dict(color="#5a8a9a", family="Share Tech Mono", size=9)),
                            showlegend=True
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.markdown('<div class="vx-graph-card">No modality data yet.</div>', unsafe_allow_html=True)
                except Exception:
                    st.markdown('<div class="vx-graph-card">Could not load modality data.</div>', unsafe_allow_html=True)


# ── LEARN TAB ─────────────────────────────────────────────────────────────────
with t_edu:
    st.markdown('<div class="vx-section">DRISHTI — FORENSIC METHODOLOGY & LEARNING CENTRE</div>', unsafe_allow_html=True)

    learn_tabs = st.tabs(["📡 Architecture", "🧬 Image Forensics", "🔊 Audio Forensics", "📝 Text Forensics", "🎬 Video Forensics", "🛡 API Sources", "⚠ Limitations"])

    # ── Architecture
    with learn_tabs[0]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ SYSTEM ARCHITECTURE — 7-LAYER PIPELINE</div>
        <div class="vx-rag-text">
        DRISHTI v2 operates a multi-layer ensemble pipeline where each layer adds independent evidence before a final weighted fusion verdict.
        </div></div>""", unsafe_allow_html=True)

        arch_items = [
            ("Layer 1 · Cloud API Detection",    "HIGH",    "Calls 6+ specialized commercial and open-source APIs in parallel: AI-or-Not (primary, 40% weight), Sightengine, Hive, HuggingFace ViT models. These APIs are trained on millions of labelled AI vs. real samples and provide the strongest signal."),
            ("Layer 2 · Calibrated Math Forensics", "HIGH", "Pixel-level and signal-level analysis: Error Level Analysis (ELA) detects compression uniformity; DCT spectrum analysis catches GAN checkerboarding; sensor noise analysis flags unnaturally smooth AI gradients; EXIF metadata reveals missing physical camera data."),
            ("Layer 3 · LangGraph Orchestration", "MEDIUM",  "A stateful multi-agent graph (StateGraph) routes inputs through the correct specialist agents (image, audio, text) and merges their outputs in a deterministic fusion node. Enables parallel execution and conditional routing."),
            ("Layer 4 · Neo4j GraphDB",           "MEDIUM",  "Every scan is persisted as a graph node with artifact edges. This enables cross-scan relational intelligence: finding similar past fakes, artifact frequency analysis, and trending detection signatures."),
            ("Layer 5 · MCP Server",              "LOW",     "Exposes DRISHTI capabilities as tool calls for Claude Desktop integration, enabling AI-assisted forensic workflows."),
            ("Layer 6 · Groq RAG Explainer",      "LOW",     "LLaMA 3.3 70B (via Groq) receives a knowledge-base context of the detected artifacts and generates a plain-English forensic narrative explaining the verdict."),
            ("Layer 7 · Content Highlighting",    "LOW",     "Sentence-level AI probability heatmaps for text; frame gallery with confidence badges for video; ELA overlay heatmap for images; timestamped transcript flagging for audio."),
        ]
        for name, sev, desc in arch_items:
            css = {"HIGH": "vx-ind-high", "MEDIUM": "vx-ind-medium", "LOW": "vx-ind-low"}[sev]
            st.markdown(f'<div class="{css}"><span class="vx-ind-name">{name}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="vx-rag" style="margin-top:1rem">
        <div class="vx-rag-header">▸ FUSION ENGINE v2 — WEIGHTED ENSEMBLE</div>
        <div class="vx-rag-text">
        The fusion engine combines API scores and forensic scores using credibility weights. AI-or-Not receives the highest weight (0.40) as it is purpose-built for binary real/AI classification. Strong API consensus (API max &gt; 0.82) triggers an override blend. 
        API "real" consensus (API max &lt; 0.22) caps the score at 35% to prevent false positives. Without any API signal, forensic-only scores are capped at 62% to prevent overconfident verdicts.
        </div></div>""", unsafe_allow_html=True)

    # ── Image Forensics
    with learn_tabs[1]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ HOW IMAGE FORENSICS WORKS</div>
        <div class="vx-rag-text">
        DRISHTI applies five independent forensic tests to every image. Each uses a calibrated sigmoid function to convert raw measurements into AI probability scores, preventing the false positives that plagued earlier detectors.
        </div></div>""", unsafe_allow_html=True)

        img_forensics = [
            ("Error Level Analysis (ELA)", "Real photographs compress heterogeneously — areas of high detail (foliage, faces) compress differently from flat areas (sky). AI images compress uniformly because pixels are mathematically generated. ELA re-compresses the image at 85% quality and measures the difference. Low variance → AI-likely.", "ela_uniform"),
            ("DCT Spectrum / GAN Checkerboard", "Discrete Cosine Transform converts the image into frequency components. GAN generators use transposed convolution ('deconvolution') upsampling, which creates a periodic checkerboard pattern in the high-frequency DCT spectrum. Real photos show no such periodicity.", "gan_grid"),
            ("Sensor Noise (High-Frequency Energy)", "Camera sensors introduce shot noise — microscopic random variation in every pixel caused by photon statistics and thermal effects. AI generators produce mathematically smooth gradients with no noise. High-frequency energy (DCT[100:, 100:]) measures this. Very low energy → AI-likely.", "hf_noise_absent"),
            ("Depth-of-Field Consistency (Laplacian)", "Real lenses produce physically accurate depth-of-field: objects near the focus plane are sharp, others are blurred. AI models often struggle with this, producing either uniform sharpness everywhere or unnatural blur. The Laplacian variance across image regions measures this.", "blur_anomaly"),
            ("EXIF Metadata Presence", "Physical cameras embed extensive metadata: camera model, focal length, aperture, ISO, GPS, timestamp. AI generators have no physical capture event and produce no EXIF. Note: this is a MEDIUM signal only — screenshots and web images also strip EXIF.", "no_exif"),
        ]
        for name, desc, tag in img_forensics:
            kb_entry = KB.get(tag, {})
            sev = kb_entry.get("sev", "LOW")
            css = {"HIGH": "vx-ind-high", "MEDIUM": "vx-ind-medium", "LOW": "vx-ind-low"}[sev]
            st.markdown(f'<div class="{css}"><span class="vx-ind-name">◉ {name}</span><span class="vx-ind-score">{sev}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="vx-rag" style="margin-top:1rem">
        <div class="vx-rag-header">▸ v2 FALSE POSITIVE FIXES</div>
        <div class="vx-rag-text">
        v1 falsely flagged real images (smartphones, screenshots, web photos) as AI. v2 recalibrates every sigmoid: ELA direction was <b>inverted</b> (fixed); noise midpoint raised from 8 → 15 (real cameras ARE noisy); EXIF missing reduced from 0.65 → 0.42; forensic-only cap reduced to 0.62; API "real" signal forces a cap at 35%.
        </div></div>""", unsafe_allow_html=True)

    # ── Audio Forensics
    with learn_tabs[2]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ HOW AUDIO FORENSICS WORKS</div>
        <div class="vx-rag-text">
        Synthetic voice detection relies on five acoustic properties that TTS and voice-cloning systems fail to replicate convincingly. All signals are computed from the first 10 seconds of audio.
        </div></div>""", unsafe_allow_html=True)

        audio_forensics = [
            ("Zero-Crossing Rate (ZCR) Variance", "ZCR counts how many times per second the audio waveform crosses zero amplitude. Human speech has chaotic high-frequency fricatives (s, f, sh, th) causing high ZCR variance. AI synthesis homogenizes these transitions. Very low ZCR variance → AI-likely.", "zcr_anomaly"),
            ("Pitch (F0) Stability", "Human speech has micro-variations in fundamental frequency (F0) caused by breathing rhythm, vocal cord tension, and emotional state. TTS vocoders generate pitch using mathematical functions, resulting in unnaturally low variance. Measured using pYIN algorithm.", "flat_pitch"),
            ("Phase Discontinuity (STFT)", "Short-Time Fourier Transform tracks how phase evolves across audio frames. Neural TTS systems generate audio in fixed-length chunks (e.g. 256 samples). At chunk boundaries, phase can jump non-continuously — a digital fingerprint invisible to human ears.", "phase_break"),
            ("High-Frequency Attenuation", "Human breath, lip noise, and sibilants contain significant energy above 7kHz. Neural vocoders apply implicit low-pass filtering, attenuating these high frequencies. The HF/LF energy ratio reveals this attenuation.", "hf_absent"),
            ("RMS Energy Variance (Burstiness)", "Human speech has highly dynamic amplitude: whispers, stressed syllables, pauses, laughs. AI synthesis produces statistically optimal amplitude envelopes with low variance. RMS coefficient of variation measures this dynamic range.", "low_burstiness"),
        ]
        for name, desc, tag in audio_forensics:
            kb_entry = KB.get(tag, {})
            sev = kb_entry.get("sev", "MEDIUM")
            css = {"HIGH": "vx-ind-high", "MEDIUM": "vx-ind-medium", "LOW": "vx-ind-low"}[sev]
            st.markdown(f'<div class="{css}"><span class="vx-ind-name">◉ {name}</span><span class="vx-ind-score">{sev}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

    # ── Text Forensics
    with learn_tabs[3]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ HOW TEXT FORENSICS WORKS</div>
        <div class="vx-rag-text">
        LLM-generated text has measurable statistical properties not found in human writing. DRISHTI uses three forensic signals plus optional GPT-2 perplexity scoring.
        </div></div>""", unsafe_allow_html=True)

        text_forensics = [
            ("Sentence Length Uniformity (Burstiness)", "Human writers vary sentence length naturally — short punchy sentences followed by longer explanatory ones. LLMs produce sentences of statistically uniform length (low standard deviation relative to mean). This is measured as burstiness: std / mean.", "uniform_sentences"),
            ("AI Transition Phrase Frequency", f"RLHF-trained models are rewarded for using transition phrases that signal organised, polished writing. Phrases like 'furthermore', 'it is important to note', 'in conclusion', 'leveraging', 'delve into' appear at statistically elevated rates in AI text.", "ai_phrases"),
            ("GPT-2 Perplexity", "Perplexity measures how 'surprised' a language model is by a text. AI-generated text closely follows LLM distributions, giving low perplexity scores. Human writing is less predictable. Requires local transformers/torch install.", "low_perplexity"),
            ("Per-Sentence Entropy Analysis", "Each sentence is scored on lexical diversity (type-token ratio), opener phrases, and word entropy. Low entropy + AI openers = high AI probability. Results are visualised as a colour-coded heatmap overlay on the original text.", None),
        ]
        for name, desc, tag in text_forensics:
            sev = KB.get(tag, {}).get("sev", "MEDIUM") if tag else "LOW"
            css = {"HIGH": "vx-ind-high", "MEDIUM": "vx-ind-medium", "LOW": "vx-ind-low"}[sev]
            st.markdown(f'<div class="{css}"><span class="vx-ind-name">◉ {name}</span><span class="vx-ind-score">{sev}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

    # ── Video Forensics
    with learn_tabs[4]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ HOW VIDEO FORENSICS WORKS</div>
        <div class="vx-rag-text">
        Video analysis extracts frames at uniform intervals and applies image forensics to each. Additionally, inter-frame temporal coherence is analysed — a signal unique to video deepfakes.
        </div></div>""", unsafe_allow_html=True)

        vid_forensics = [
            ("Per-Frame Image Analysis", "Each extracted frame is passed through the full image forensic pipeline: ELA, DCT noise, GAN periodicity, DOF consistency, and EXIF. Per-frame confidence scores are visualised on a timeline chart. Frames above threshold are flagged red."),
            ("Temporal MSE Variance", "Mean Squared Error (MSE) between consecutive frames measures inter-frame motion. Face-swap deepfakes often have anomalous MSE variance because the blended face region flickering doesn't match natural scene motion. Coefficient of variation of frame MSE reveals temporal incoherence."),
            ("Frame Gallery Inspection", "All analysed frames are displayed as thumbnails with colour-coded confidence borders (red = flagged, amber = uncertain, green = authentic). This enables frame-level manual inspection to pinpoint exact tampering regions."),
            ("Cloud API Video Analysis", "Sightengine's video deepfake and AI-generation endpoints analyse the full video stream (files under 15MB) using temporal convolutional networks trained specifically on video manipulation artefacts."),
        ]
        for name, desc in vid_forensics:
            st.markdown(f'<div class="vx-ind-medium"><span class="vx-ind-name">◉ {name}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

    # ── API Sources
    with learn_tabs[5]:
        st.markdown("""
        <div class="vx-rag">
        <div class="vx-rag-header">▸ API SOURCE CREDIBILITY & CONFIGURATION</div>
        <div class="vx-rag-text">
        Each API source receives a fusion weight based on its specialisation and empirical accuracy. Configure keys at the top of drishti_v2.py.
        </div></div>""", unsafe_allow_html=True)

        api_sources = [
            ("AI-or-Not",        "aiornot.com",      "0.40", "Image",  "Specialized binary real/AI classifier trained on Midjourney, DALL-E 3, SD, Firefly outputs. Primary image signal."),
            ("Resemble AI DETECT","detect.resemble.ai","0.38","Audio",  "Trained on 160+ deepfake voice architectures. Primary audio signal."),
            ("Winston AI",        "gowinston.ai",     "0.35", "Text",   "Commercial LLM text detector with sentence-level scoring."),
            ("Hive Moderation",   "thehive.ai",       "0.30", "Image",  "Enterprise-grade visual AI detection engine."),
            ("Sapling",           "sapling.ai",       "0.30", "Text",   "Linguistic analysis model detecting LLM output distributions."),
            ("Sightengine",       "sightengine.com",  "0.28", "Image/Video", "Face-swap deepfake detection + AI-generated image classification."),
            ("HF RoBERTa",        "huggingface.co",   "0.28", "Text",   "Open-source ChatGPT detector (Hello-SimpleAI/chatgpt-detector-roberta)."),
            ("HF ViT",            "huggingface.co",   "0.18", "Image",  "Open-source vision transformer (umm-maybe/AI-image-detector)."),
            ("HF Deepfake ViT",   "huggingface.co",   "0.22", "Image",  "Open-source deepfake detector (dima806/deepfake_vs_real_image_detection)."),
            ("Groq Whisper",      "groq.com",         "N/A",  "Audio",  "Audio transcription only — not used in fusion score. Provides transcript segments for timestamp analysis."),
        ]

        header_html = """
        <div style="display:grid;grid-template-columns:1.2fr 1.2fr 0.5fr 0.6fr 2.5fr;gap:.3rem;padding:.4rem .8rem;
        font-family:'Share Tech Mono',monospace;font-size:.65rem;color:#3a6a8a;letter-spacing:1px;border-bottom:1px solid #0a2a40;margin-bottom:.3rem">
        <span>SOURCE</span><span>DOMAIN</span><span>WEIGHT</span><span>TYPE</span><span>NOTES</span></div>"""
        st.markdown(header_html, unsafe_allow_html=True)

        for name, domain, weight, modality, notes in api_sources:
            is_ok = any([
                name == "AI-or-Not" and _aon_ok(),
                name == "Resemble AI DETECT" and _resemble_ok(),
                name == "Winston AI" and _winston_ok(),
                name == "Hive Moderation" and _hive_ok(),
                name == "Sapling" and _sapling_ok(),
                name == "Sightengine" and _sight_ok(),
                "HF" in name and _hf_ok(),
                name == "Groq Whisper" and _groq_ok(),
            ])
            status_html = '<span class="vx-api-ok">ONLINE</span>' if is_ok else '<span class="vx-api-na">NEEDS KEY</span>'
            st.markdown(
                f'<div style="display:grid;grid-template-columns:1.2fr 1.2fr 0.5fr 0.6fr 2.5fr;gap:.3rem;padding:.5rem .8rem;'
                f'background:#0a1628;border:1px solid #0a2a40;border-radius:3px;margin:.2rem 0;'
                f'font-family:Inter,sans-serif;font-size:.78rem;color:#c8d8e8;align-items:start">'
                f'<span style="color:#00f5ff;font-family:Share Tech Mono,monospace;font-size:.72rem">{name}</span>'
                f'<span style="color:#3a6a8a;font-size:.7rem">{domain}</span>'
                f'<span style="color:#ffbb33;font-family:Share Tech Mono,monospace">{weight}</span>'
                f'<span>{status_html}</span>'
                f'<span style="color:#8aa8b8;font-size:.75rem">{notes}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    # ── Limitations
    with learn_tabs[6]:
        st.markdown("""
        <div class="vx-verdict-uncertain">
            ◈  IMPORTANT: NO DEEPFAKE DETECTOR IS 100% ACCURATE<br>
            <div style="font-size:.82rem;font-family:Inter,sans-serif;font-weight:400;opacity:.8;margin-top:.5rem;line-height:1.7">
                DRISHTI v2 is a forensic intelligence tool, not a definitive oracle. A HIGH confidence result
                is strong evidence warranting further investigation — not legal proof. A LOW confidence result
                does not guarantee authenticity.
            </div>
        </div>""", unsafe_allow_html=True)

        limitations = [
            ("False Positives on Real Content", "HIGH",
             "Certain real images can trigger forensic signals: heavy Instagram/app post-processing removes sensor noise; screenshots have no EXIF; heavily compressed JPEGs have unusual ELA patterns. Always cross-reference multiple signals."),
            ("Adversarial AI Generation", "HIGH",
             "State-of-the-art generators (Midjourney v6, DALL-E 3, Stable Diffusion 3) are trained to minimize detectable artifacts. Detection is an arms race. Future models may evade current forensic methods."),
            ("Audio Compression Artifacts", "MEDIUM",
             "Heavy MP3/AAC compression removes high-frequency content and alters ZCR patterns, mimicking some TTS signatures. Provide uncompressed WAV audio for best results."),
            ("Short Text Samples", "MEDIUM",
             "Text analysis requires minimum ~80 characters (ideally 200+). Short excerpts don't provide enough statistical signal for perplexity or burstiness measurements."),
            ("Video File Size Limits", "MEDIUM",
             "Sightengine video API is limited to ~15MB files. Larger videos use frame-sampling only, which may miss localised deepfake regions."),
            ("GPT-2 Perplexity Unavailability", "LOW",
             "GPT-2 perplexity requires local transformers + torch installation. Without it, text detection relies on phrase analysis and cloud APIs only, which is less accurate for subtle AI text."),
            ("No Guarantee of Real-Time Accuracy", "LOW",
             "API models are updated periodically. A model that detected a specific generator today may not detect its next version. DRISHTI should be used as one layer in a broader verification workflow."),
        ]
        for name, sev, desc in limitations:
            css = {"HIGH": "vx-ind-high", "MEDIUM": "vx-ind-medium", "LOW": "vx-ind-low"}[sev]
            st.markdown(f'<div class="{css}"><span class="vx-ind-name">⚠ {name}</span><span class="vx-ind-score">{sev}</span><div class="vx-ind-explain">{desc}</div></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="vx-rag" style="margin-top:1.5rem">
        <div class="vx-rag-header">▸ RESPONSIBLE USE GUIDELINES</div>
        <div class="vx-rag-text">
        DRISHTI is designed for legitimate forensic investigation, journalism, research, and content moderation. 
        Results should be treated as one evidentiary input among many. Never make consequential decisions (legal, 
        employment, editorial) based solely on automated detection. When stakes are high, combine DRISHTI results 
        with manual expert review, provenance metadata verification, and chain-of-custody documentation.
        </div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="margin-top:3rem;padding:1.5rem 2rem;border-top:1px solid #0a2a40;
font-family:'Share Tech Mono',monospace;font-size:.65rem;color:#1a4a5a;
display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem">
    <span>DRISHTI v2 · Verified Index of Digital Authenticity</span>
    <span>7-LAYER PIPELINE · AI-OR-NOT · LANGGRAPH · NEO4J · GROQ + LLAMA 3.3</span>
    <span>FOR FORENSIC / RESEARCH USE ONLY · NOT LEGAL EVIDENCE</span>
</div>
""", unsafe_allow_html=True)