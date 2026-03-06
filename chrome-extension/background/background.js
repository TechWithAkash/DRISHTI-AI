/**
 * DRISHTI — Background Service Worker  (FIXED v2.1)
 * ─────────────────────────────────────────────────────────────────────────────
 * FIX: MV3 service workers sleep and LOSE module-level variables.
 *      All state is now stored in chrome.storage.session (persists across SW wakes).
 * FIX: /analyze/frame always called with full error handling + timeout.
 * FIX: MEETING_STATUS stored persistently so popup can always read it.
 */

const BACKEND_URL_DEFAULT = "http://localhost:8000";

// ── Persistent state via chrome.storage.session ───────────────────────────────
// (Unlike module-level vars, these survive SW sleep/wake cycles)
async function getState() {
    const data = await chrome.storage.session.get([
        "backendAlive", "meetingActive", "participantResults", "backendUrl"
    ]);
    return {
        backendAlive: data.backendAlive ?? false,
        meetingActive: data.meetingActive ?? false,
        participantResults: data.participantResults ?? {},
        backendUrl: data.backendUrl ?? BACKEND_URL_DEFAULT,
    };
}

async function setState(patch) {
    await chrome.storage.session.set(patch);
}

// ── Init ──────────────────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(async () => {
    const stored = await chrome.storage.local.get("settings");
    if (!stored.settings) {
        await chrome.storage.local.set({
            settings: { enabled: true, threshold: 60, analysisInterval: 8000, language: "en", voiceAlerts: false, backendUrl: BACKEND_URL_DEFAULT }
        });
    }
    await checkBackendHealth();
});

chrome.runtime.onStartup.addListener(() => checkBackendHealth());

// ── Backend Health Check ──────────────────────────────────────────────────────
async function checkBackendHealth() {
    const { backendUrl } = await getState();
    const url = backendUrl || BACKEND_URL_DEFAULT;
    let alive = false;
    try {
        const r = await fetch(`${url}/health`, {
            method: "GET",
            signal: AbortSignal.timeout(4000)
        });
        alive = r.ok;
    } catch { alive = false; }

    await setState({ backendAlive: alive, backendUrl: url });

    // Notify all Meet tabs
    chrome.tabs.query({ url: "https://meet.google.com/*" }, (tabs) => {
        tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, { type: "BACKEND_STATUS", alive }).catch(() => { });
        });
    });
    return alive;
}

// Health poll every 30s (alarm-based so it survives SW sleep)
chrome.alarms.create("healthCheck", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "healthCheck") checkBackendHealth();
});

// ── Message Handler ───────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    handleMessage(msg, sender).then(sendResponse).catch(err => sendResponse({ error: err?.message }));
    return true;  // always async
});

async function handleMessage(msg, sender) {
    const state = await getState();

    switch (msg.type) {

        case "ANALYZE_FRAME": {
            const result = await analyzeFrame(msg, state);
            // Update participant results
            const results = state.participantResults;
            results[msg.participantId] = result;
            await setState({ participantResults: results });
            return result;
        }

        case "GET_STATUS": {
            // FIX: Also detect meeting from the sender tab URL if state is stale
            let meetingActive = state.meetingActive;
            if (!meetingActive && sender?.tab?.url) {
                meetingActive = /meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}/.test(sender.tab.url);
            }
            return {
                backendAlive: state.backendAlive,
                enabled: true,
                language: "en",
                meetingActive,
                participantResults: state.participantResults,
            };
        }

        case "MEETING_STATUS": {
            await setState({ meetingActive: msg.active });
            if (!msg.active) await setState({ participantResults: {} });
            return { ok: true };
        }

        case "SETTINGS_UPDATE": {
            const stored = await chrome.storage.local.get("settings");
            const merged = { ...(stored.settings || {}), ...msg.settings };
            await chrome.storage.local.set({ settings: merged });
            if (msg.settings.backendUrl) {
                await setState({ backendUrl: msg.settings.backendUrl });
                await checkBackendHealth();
            }
            return { ok: true };
        }

        case "CHECK_BACKEND": {
            const alive = await checkBackendHealth();
            return { alive };
        }

        case "CLEAR_RESULTS": {
            await setState({ participantResults: {} });
            return { ok: true };
        }

        default:
            return { ignored: true };
    }
}

// ── Core: Analyze Frame ───────────────────────────────────────────────────────
async function analyzeFrame({ frameBase64, participantId, participantName }, state) {
    const settings = (await chrome.storage.local.get("settings")).settings || {};
    if (settings.enabled === false) return { skipped: true };

    const backendUrl = state.backendUrl || BACKEND_URL_DEFAULT;

    if (state.backendAlive) {
        try {
            const resp = await fetch(`${backendUrl}/analyze/frame`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frame_base64: frameBase64, participant_id: participantId }),
                signal: AbortSignal.timeout(15_000),
            });
            if (resp.ok) {
                const data = await resp.json();
                return {
                    score: data.confidence ?? 0,
                    verdict: data.verdict ?? "UNKNOWN",
                    tags: data.tags ?? [],
                    explanation: data.explanation ?? "",
                    source: "backend",
                    timestamp: Date.now(),
                    name: participantName,
                };
            }
        } catch (e) {
            // Backend call failed — mark as dead and use local fallback
            await setState({ backendAlive: false });
        }
    }

    // Local heuristic fallback
    return {
        score: localScoreHeuristic(frameBase64),
        verdict: "UNCERTAIN",
        tags: [],
        explanation: "⚠ Backend offline — connect the DRISHTI server for accurate analysis.",
        source: "local",
        timestamp: Date.now(),
        name: participantName,
    };
}

// ── Local Heuristic (no backend) ──────────────────────────────────────────────
function localScoreHeuristic(base64) {
    // Very rough: measure base64 entropy as a proxy for image complexity
    // High entropy = complex real photo = lower AI score
    // Low entropy (like a black frame) = suspicious
    if (!base64 || base64.length < 500) return 15;
    const unique = new Set(base64.slice(0, 1000)).size;
    const complexity = unique / 64;   // 0–1, higher = more complex
    return Math.max(5, Math.round((1 - complexity) * 55));
}
