/**
 * DRISHTI — Popup JavaScript  (FIXED v2.1)
 * ─────────────────────────────────────────────────────────────────────────────
 * FIX 1: Meeting detection directly from active tab URL (not SW state)
 * FIX 2: Graceful handling if chrome.runtime.sendMessage returns null
 * FIX 3: All settings saved to chrome.storage.session (SW-safe)
 */

"use strict";

// ── i18n Strings ───────────────────────────────────────────────────────────────
const STRINGS = {
    en: { meet_active: "🟢 IN GOOGLE MEET", meet_inactive: "⊘ Not in a Google Meet", lbl_scanned: "SCANNED", lbl_suspicious: "SUSPICIOUS", lbl_safe: "SAFE", lbl_participants: "PARTICIPANT ANALYSIS", lbl_empty: "Open a Google Meet to start detection", lbl_detection: "Detection", lbl_voice: "Voice Alerts", lbl_threshold: "Threshold:", verdict_real: "REAL", verdict_uncertain: "UNCERTAIN", verdict_fake: "DEEPFAKE", verdict_analyzing: "SCANNING", be_online: "ONLINE", be_offline: "OFFLINE", btn_clear: "Clear Results", btn_open: "Open App ↗", btn_save: "Save", btn_cancel: "Cancel" },
    hi: { meet_active: "🟢 मीट में हैं", meet_inactive: "⊘ Google Meet में नहीं", lbl_scanned: "स्कैन", lbl_suspicious: "संदिग्ध", lbl_safe: "सुरक्षित", lbl_participants: "प्रतिभागी विश्लेषण", lbl_empty: "पहचान के लिए Google Meet खोलें", lbl_detection: "पहचान", lbl_voice: "आवाज़ चेतावनी", lbl_threshold: "सीमा:", verdict_real: "वास्तविक", verdict_uncertain: "अनिश्चित", verdict_fake: "डीपफेक", verdict_analyzing: "स्कैनिंग", be_online: "ऑनलाइन", be_offline: "ऑफलाइन", btn_clear: "साफ़ करें", btn_open: "ऐप खोलें ↗", btn_save: "सहेजें", btn_cancel: "रद्द करें" },
    es: { meet_active: "🟢 EN GOOGLE MEET", meet_inactive: "⊘ No estás en Google Meet", lbl_scanned: "ESCANEADOS", lbl_suspicious: "SOSPECHOSOS", lbl_safe: "SEGUROS", lbl_participants: "ANÁLISIS DE PARTICIPANTES", lbl_empty: "Abre Google Meet para comenzar", lbl_detection: "Detección", lbl_voice: "Alertas de Voz", lbl_threshold: "Umbral:", verdict_real: "REAL", verdict_uncertain: "INCIERTO", verdict_fake: "FALSO", verdict_analyzing: "ANALIZANDO", be_online: "EN LÍNEA", be_offline: "DESCONECTADO", btn_clear: "Limpiar", btn_open: "Abrir App ↗", btn_save: "Guardar", btn_cancel: "Cancelar" },
    fr: { meet_active: "🟢 DANS GOOGLE MEET", meet_inactive: "⊘ Pas dans Google Meet", lbl_scanned: "SCANNÉS", lbl_suspicious: "SUSPECTS", lbl_safe: "SÛRS", lbl_participants: "ANALYSE DES PARTICIPANTS", lbl_empty: "Ouvre Google Meet pour démarrer", lbl_detection: "Détection", lbl_voice: "Alertes Vocales", lbl_threshold: "Seuil:", verdict_real: "RÉEL", verdict_uncertain: "INCERTAIN", verdict_fake: "DEEPFAKE", verdict_analyzing: "ANALYSE", be_online: "EN LIGNE", be_offline: "HORS LIGNE", btn_clear: "Effacer", btn_open: "Ouvrir App ↗", btn_save: "Enregistrer", btn_cancel: "Annuler" },
    ar: { meet_active: "🟢 في جوجل ميت", meet_inactive: "⊘ لست في جوجل ميت", lbl_scanned: "فحص", lbl_suspicious: "مشبوه", lbl_safe: "آمن", lbl_participants: "تحليل الحضور", lbl_empty: "افتح جوجل ميت للبدء", lbl_detection: "الكشف", lbl_voice: "تنبيهات صوتية", lbl_threshold: "الحد:", verdict_real: "حقيقي", verdict_uncertain: "مشكوك", verdict_fake: "مزيف", verdict_analyzing: "تحليل", be_online: "متصل", be_offline: "غير متصل", btn_clear: "مسح", btn_open: "فتح التطبيق ↗", btn_save: "حفظ", btn_cancel: "إلغاء" },
    zh: { meet_active: "🟢 在 Google Meet 中", meet_inactive: "⊘ 未在 Google Meet 中", lbl_scanned: "已扫描", lbl_suspicious: "可疑", lbl_safe: "安全", lbl_participants: "参与者分析", lbl_empty: "打开 Google Meet 开始检测", lbl_detection: "检测", lbl_voice: "语音提醒", lbl_threshold: "阈值：", verdict_real: "真实", verdict_uncertain: "不确定", verdict_fake: "深度伪造", verdict_analyzing: "扫描中", be_online: "在线", be_offline: "离线", btn_clear: "清除", btn_open: "打开应用 ↗", btn_save: "保存", btn_cancel: "取消" },
};

// ── Regex to identify a Google Meet room URL ──────────────────────────────────
const MEET_ROOM_REGEX = /meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}/;

// ── State ──────────────────────────────────────────────────────────────────────
let settings = { enabled: true, threshold: 60, analysisInterval: 8000, language: "en", voiceAlerts: false, backendUrl: "http://localhost:8000" };
let s = STRINGS["en"];
let participantResults = {};
let activeMeetTabId = null;

// ── DOM Refs ───────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

// ── Init ───────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    // Load saved settings
    const stored = await chrome.storage.local.get("settings");
    if (stored.settings) settings = { ...settings, ...stored.settings };

    applySettings();
    applyLanguage(settings.language);
    bindEvents();

    // ── FIX 1: Detect meeting from active tab URL directly ──────────────────────
    // NOTE: Do NOT call chrome.scripting.executeScript here.
    // The manifest content_scripts already injects content.js automatically.
    // A second injection would cause "Identifier already declared" SyntaxError.
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        if (!tab) return;
        const isMeet = MEET_ROOM_REGEX.test(tab.url || "");
        activeMeetTabId = isMeet ? tab.id : null;
        updateMeetStatus(isMeet, tab.url);
    });

    // Start polling
    refresh();
    setInterval(refresh, 2000);
});

// ── Null-safe DOM helper ───────────────────────────────────────────────────────
function setText(id, val) {
    const el = $(id);
    if (el) el.textContent = val;
}

// ── Apply Settings to UI ───────────────────────────────────────────────────────
function applySettings() {
    const toggleEnabled = $("toggleEnabled");
    const toggleVoice = $("toggleVoice");
    const range = $("thresholdRange");
    const rangeVal = $("thresholdVal");
    if (toggleEnabled) toggleEnabled.checked = settings.enabled;
    if (toggleVoice) toggleVoice.checked = settings.voiceAlerts;
    if (range) range.value = settings.threshold;
    if (rangeVal) rangeVal.textContent = settings.threshold;
}

// ── Language ────────────────────────────────────────────────────────────────────
function applyLanguage(lang) {
    s = STRINGS[lang] || STRINGS["en"];
    // All of these may or may not be in DOM at any given moment — use setText()
    setText("lbl_scanned", s.lbl_scanned);
    setText("lbl_suspicious", s.lbl_suspicious);
    setText("lbl_safe", s.lbl_safe);
    setText("lbl_participants", s.lbl_participants);
    setText("lbl_empty", s.lbl_empty);    // lives inside .empty-state — may not exist
    setText("lbl_detection", s.lbl_detection);
    setText("lbl_voice", s.lbl_voice);
    setText("btnClear", s.btn_clear);
    setText("btnOpenApp", s.btn_open);
    document.body.dir = lang === "ar" ? "rtl" : "ltr";
    document.querySelectorAll(".lang-btn").forEach(b => b.classList.toggle("active", b.dataset.lang === lang));
}

// ── Refresh (every 2s) ─────────────────────────────────────────────────────────
async function refresh() {
    // FIX 1: Always re-check active tab URL — most reliable meeting detection
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        if (!tab) return;
        const isMeet = MEET_ROOM_REGEX.test(tab.url || "");
        activeMeetTabId = isMeet ? tab.id : null;
        updateMeetStatus(isMeet, tab.url);
    });

    // FIX 2: Get participant results from background with null check
    safeMessage({ type: "GET_STATUS" }, (resp) => {
        if (!resp) return;
        updateBackendStatus(resp.backendAlive);
        participantResults = resp.participantResults || {};
        renderParticipants(participantResults);
    });
}

// ── FIX 2: Safe messaging helper ───────────────────────────────────────────────
function safeMessage(msg, cb) {
    try {
        chrome.runtime.sendMessage(msg, (res) => {
            if (chrome.runtime.lastError) { cb(null); return; }
            cb(res);
        });
    } catch { cb(null); }
}

// ── Meet Status ────────────────────────────────────────────────────────────────
function updateMeetStatus(isMeet, url) {
    const meetStatus = $("meetStatus");
    const meetLabel = $("meetLabel");
    const meetIcon = $("meetIcon");
    if (!meetStatus) return;

    meetStatus.className = `meet-status ${isMeet ? "active" : "inactive"}`;
    meetLabel.textContent = isMeet ? s.meet_active : s.meet_inactive;
    meetIcon.textContent = isMeet ? "⬤" : "⊘";

    // Show meeting code if active
    if (isMeet && url) {
        const match = url.match(/\/([a-z]{3}-[a-z]{4}-[a-z]{3})/);
        if (match) {
            meetLabel.textContent = `${s.meet_active} · ${match[1]}`;
        }
    }
}

// ── Backend Status ─────────────────────────────────────────────────────────────
function updateBackendStatus(alive) {
    const beDot = $("beDot");
    const beLabel = $("beLabel");
    const pill = $("backendPill");
    const cls = alive ? "alive" : "dead";
    if (beDot) beDot.className = `be-dot ${cls}`;
    if (beLabel) beLabel.textContent = alive ? s.be_online : s.be_offline;
    if (pill) pill.className = `backend-pill ${cls}`;
}

// ── Participant Cards ──────────────────────────────────────────────────────────
function renderParticipants(results) {
    const entries = Object.entries(results);
    const total = entries.length;
    const fakes = entries.filter(([, r]) => (r.score ?? 0) >= settings.threshold).length;
    const safes = entries.filter(([, r]) => (r.score ?? 0) < settings.threshold - 20).length;

    setText("scanCount", total);
    setText("fakeCount", fakes);
    setText("safeCount", safes);

    const pList = $("participantList");
    if (total === 0) {
        pList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">${activeMeetTabId ? "🔍" : "🎥"}</div>
        <div>${activeMeetTabId ? "Scanning participants..." : s.lbl_empty}</div>
      </div>`;
        return;
    }

    const sorted = entries.sort(([, a], [, b]) => (b.score ?? 0) - (a.score ?? 0));
    pList.innerHTML = sorted.map(([id, r]) => {
        const score = r.score ?? 0;
        const cls = score >= settings.threshold ? "fake" : score >= settings.threshold - 20 ? "uncertain" : "real";
        const verdict = s[`verdict_${cls}`] || cls.toUpperCase();
        const name = (r.name || id).slice(0, 26);
        const age = r.timestamp ? relTime(r.timestamp) : "";
        const srcBadge = r.source === "backend" ? "API" : "local";
        return `
      <div class="p-card ${cls}">
        <span class="p-dot"></span>
        <span class="p-name" title="${name}">${name}</span>
        <span class="p-source">${srcBadge}</span>
        <span class="p-verdict">${verdict}</span>
        <span class="p-score">${score.toFixed(0)}%</span>
      </div>`;
    }).join("");
}

function relTime(ts) {
    const d = Math.round((Date.now() - ts) / 1000);
    if (d < 5) return "now";
    if (d < 60) return `${d}s`;
    return `${Math.round(d / 60)}m`;
}

// ── Event Bindings ─────────────────────────────────────────────────────────────
// Helper: bind an event only if the element exists
function on(id, event, handler) {
    const el = $(id);
    if (el) el.addEventListener(event, handler);
}

function bindEvents() {
    on("toggleEnabled", "change", () => {
        const el = $("toggleEnabled");
        if (el) { settings.enabled = el.checked; saveSettings(); }
    });
    on("toggleVoice", "change", () => {
        const el = $("toggleVoice");
        if (el) { settings.voiceAlerts = el.checked; saveSettings(); }
    });
    on("thresholdRange", "input", () => {
        const el = $("thresholdRange");
        if (el) {
            settings.threshold = parseInt(el.value);
            setText("thresholdVal", settings.threshold);
            saveSettings();
        }
    });
    on("langGrid", "click", (e) => {
        const btn = e.target.closest(".lang-btn");
        if (!btn) return;
        settings.language = btn.dataset.lang;
        applyLanguage(settings.language);
        saveSettings();
    });
    on("btnClear", "click", () => {
        safeMessage({ type: "CLEAR_RESULTS" }, () => {
            participantResults = {};
            renderParticipants({});
        });
    });
    on("btnOpenApp", "click", () => chrome.tabs.create({ url: "http://localhost:8501" }));
    on("btnSetup", "click", () => {
        const urlInput = $("backendUrlInput");
        if (urlInput) urlInput.value = settings.backendUrl || "http://localhost:8000";
        const modal = $("setupModal");
        if (modal) modal.classList.remove("hidden");
    });
    on("btnCloseModal", "click", () => {
        const modal = $("setupModal");
        if (modal) modal.classList.add("hidden");
    });
    on("btnSaveUrl", "click", () => {
        const urlInput = $("backendUrlInput");
        if (urlInput) settings.backendUrl = urlInput.value.trim();
        saveSettings();
        const modal = $("setupModal");
        if (modal) modal.classList.add("hidden");
        safeMessage({ type: "CHECK_BACKEND" }, (res) => {
            if (res) updateBackendStatus(res.alive);
        });
    });
}

function saveSettings() {
    chrome.storage.local.set({ settings });
    safeMessage({ type: "SETTINGS_UPDATE", settings }, () => { });
}
