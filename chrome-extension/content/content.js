/**
 * DRISHTI — Content Script v2.2 (Double-Injection Safe)
 *
 * CRITICAL FIX: Wrapped in IIFE + window guard.
 * Chrome manifest auto-injects this AND popup.js tried to inject it again.
 * The guard makes any second injection a no-op — zero errors.
 */
(function () {
    "use strict";

    // ── GUARD: Exit immediately if already running ──────────────────────────────
    if (window.__DRISHTI_CS_LOADED__) {
        console.log("[DRISHTI] Already loaded — skipping duplicate injection.");
        return;
    }
    window.__DRISHTI_CS_LOADED__ = true;

    // ── Meeting URL check ───────────────────────────────────────────────────────
    const MEET_REGEX = /meet\.google\.com\/[a-z]{3}-[a-z]{4}-[a-z]{3}/;
    if (!MEET_REGEX.test(window.location.href)) {
        console.log("[DRISHTI] Not in a meeting room, skipping.");
        return;
    }
    console.log("[DRISHTI] ✅ Meeting detected:", window.location.href);

    // ── i18n ────────────────────────────────────────────────────────────────────
    const I18N = {
        en: { real: "✓ REAL", uncertain: "? UNCERTAIN", fake: "⚠ DEEPFAKE", analyzing: "◌ SCANNING", offline: "OFFLINE", alert_msg: "⚠ DEEPFAKE DETECTED", alert_sub: "Suspicious participant detected. Exercise caution.", panel_title: "DRISHTI", scanned: "Scanned", suspicious: "Suspicious", backend: "Backend", online: "ONLINE", down: "OFFLINE" },
        hi: { real: "✓ वास्तविक", uncertain: "? अनिश्चित", fake: "⚠ डीपफेक", analyzing: "◌ स्कैनिंग", offline: "ऑफलाइन", alert_msg: "⚠ डीपफेक मिला", alert_sub: "संदिग्ध प्रतिभागी। सावधान रहें।", panel_title: "DRISHTI", scanned: "स्कैन", suspicious: "संदिग्ध", backend: "बैकएंड", online: "ऑनलाइन", down: "बंद" },
        es: { real: "✓ REAL", uncertain: "? INCIERTO", fake: "⚠ FALSO", analyzing: "◌ ANALIZANDO", offline: "DESCONECTADO", alert_msg: "⚠ DEEPFAKE DETECTADO", alert_sub: "Participante sospechoso detectado.", panel_title: "DRISHTI", scanned: "Escaneados", suspicious: "Sospechosos", backend: "Servidor", online: "EN LÍNEA", down: "CAÍDO" },
        fr: { real: "✓ RÉEL", uncertain: "? INCERTAIN", fake: "⚠ DEEPFAKE", analyzing: "◌ ANALYSE", offline: "HORS LIGNE", alert_msg: "⚠ DEEPFAKE DÉTECTÉ", alert_sub: "Participant suspect détecté.", panel_title: "DRISHTI", scanned: "Scannés", suspicious: "Suspects", backend: "Serveur", online: "EN LIGNE", down: "HORS SERVICE" },
        ar: { real: "✓ حقيقي", uncertain: "? مشكوك", fake: "⚠ مزيف", analyzing: "◌ تحليل", offline: "غير متصل", alert_msg: "⚠ تم اكتشاف تزوير", alert_sub: "مشارك مشبوه. كن حذرًا.", panel_title: "DRISHTI", scanned: "فحص", suspicious: "مشبوه", backend: "خادم", online: "متصل", down: "معطل" },
        zh: { real: "✓ 真实", uncertain: "? 不确定", fake: "⚠ 深度伪造", analyzing: "◌ 扫描中", offline: "离线", alert_msg: "⚠ 检测到深度伪造", alert_sub: "检测到可疑参与者。", panel_title: "DRISHTI", scanned: "已扫描", suspicious: "可疑", backend: "服务器", online: "在线", down: "离线" },
    };

    // ── State ───────────────────────────────────────────────────────────────────
    let cfg = { enabled: true, threshold: 60, analysisInterval: 10000, language: "en", voiceAlerts: false };
    let t = I18N["en"];
    let backendAlive = false;
    let scanCount = 0;
    let suspiciousCount = 0;
    let analysisPending = {};
    let lastAnalysis = {};
    let panelMinimized = false;
    let alertShown = false;
    let tileObserver = null;

    // ── Kick off ────────────────────────────────────────────────────────────────
    chrome.storage.local.get("settings", ({ settings }) => {
        if (settings) { cfg = { ...cfg, ...settings }; t = I18N[cfg.language] || I18N["en"]; }

        safeSend({ type: "MEETING_STATUS", active: true, url: window.location.href });
        safeSend({ type: "CHECK_BACKEND" }, (res) => { backendAlive = res?.alive ?? false; updatePanel(); });

        injectPanel();
        injectAlertBanner();
        startTileObserver();

        // Start scanning: immediately, then every 3s
        setTimeout(scanForTiles, 1000);
        setInterval(scanForTiles, 3000);
    });

    chrome.storage.onChanged.addListener((changes) => {
        if (changes.settings) {
            cfg = { ...cfg, ...changes.settings.newValue };
            t = I18N[cfg.language] || I18N["en"];
            updatePanel();
        }
    });

    chrome.runtime.onMessage.addListener((msg) => {
        if (msg.type === "BACKEND_STATUS") { backendAlive = msg.alive; updatePanel(); }
    });

    window.addEventListener("beforeunload", () => {
        safeSend({ type: "MEETING_STATUS", active: false });
    });

    // ── Safe messaging ──────────────────────────────────────────────────────────
    function safeSend(msg, cb) {
        try {
            if (cb) {
                chrome.runtime.sendMessage(msg, (res) => {
                    if (chrome.runtime.lastError) { cb(null); return; }
                    cb(res);
                });
            } else {
                chrome.runtime.sendMessage(msg).catch(() => { });
            }
        } catch (e) {
            if (cb) cb(null);
        }
    }

    // ── MutationObserver for dynamic Meet tiles ─────────────────────────────────
    function startTileObserver() {
        if (tileObserver) tileObserver.disconnect();
        // Debounce MutationObserver calls to avoid thrashing
        let debounceTimer = null;
        tileObserver = new MutationObserver(() => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(scanForTiles, 500);
        });
        tileObserver.observe(document.body, { childList: true, subtree: true });
    }

    // ── Core: Scan for participant tiles ────────────────────────────────────────
    function scanForTiles() {
        if (!cfg.enabled) return;

        const now = Date.now();
        const processed = new Set();

        // PRIMARY — Google Meet uses [data-participant-id] on tile containers
        // This works whether camera is ON, OFF, or screen-sharing
        const containers = document.querySelectorAll('[data-participant-id]');

        containers.forEach((container, idx) => {
            const pid = container.getAttribute('data-participant-id') || `p-${idx}`;
            if (processed.has(pid)) return;
            processed.add(pid);

            // Ensure positioned so our absolute badge renders correctly
            if (window.getComputedStyle(container).position === 'static') {
                container.style.position = 'relative';
            }

            const name = getParticipantName(container);
            ensureBadge(container, pid, name);

            // Skip if already pending or analysed recently
            if (analysisPending[pid]) return;
            if (lastAnalysis[pid] && now - lastAnalysis[pid] < cfg.analysisInterval) return;

            const video = container.querySelector('video');
            if (video && video.readyState >= 1) {
                captureVideoFrame(video, pid, name);
            } else {
                captureAvatarFrame(container, pid, name);
            }
        });

        // FALLBACK — any visible <video> not inside a data-participant-id container
        document.querySelectorAll('video').forEach((vid, idx) => {
            if (vid.readyState < 2 || vid.videoWidth < 80) return;
            const ctr = findNearestContainer(vid);
            if (!ctr) return;
            const pid = `vid-${idx}`;
            if (processed.has(pid)) return;
            processed.add(pid);
            if (window.getComputedStyle(ctr).position === 'static') ctr.style.position = 'relative';
            ensureBadge(ctr, pid, 'Participant');
            if (!analysisPending[pid] && !(lastAnalysis[pid] && now - lastAnalysis[pid] < cfg.analysisInterval)) {
                captureVideoFrame(vid, pid, 'Participant');
            }
        });
    }

    // ── Get name from Meet tile ─────────────────────────────────────────────────
    function getParticipantName(container) {
        const selectors = [
            '[data-self-name]', '[data-participant-name]',
            '.zWGUib', '.NREBhe', '[jsname="PcmDee"]', '.VfPpkd-cnG4Ld',
        ];
        for (const sel of selectors) {
            const el = container.querySelector(sel);
            const txt = el?.textContent?.trim();
            if (txt) return txt;
        }
        const nameAttr = container.getAttribute('data-self-name')
            || container.getAttribute('data-participant-name')
            || container.getAttribute('data-user-name');
        if (nameAttr) return nameAttr;

        // Last resort: find first short text node that looks like a name
        for (const el of container.querySelectorAll('span, div')) {
            const txt = el.textContent?.trim();
            if (txt && txt.length > 1 && txt.length < 40 && /^[\w\u0900-\u097F\s\-'.]+$/u.test(txt)) {
                return txt;
            }
        }
        return 'Participant';
    }

    function findNearestContainer(video) {
        let el = video.parentElement;
        for (let i = 0; i < 8; i++) {
            if (!el) break;
            if (el.getAttribute('data-participant-id') || el.getAttribute('data-ssrc')) return el;
            el = el.parentElement;
        }
        return video.parentElement;
    }

    // ── Badge injection ─────────────────────────────────────────────────────────
    function ensureBadge(container, tileId, name) {
        if (container.querySelector(`[data-drishti="${CSS.escape(tileId)}"]`)) return;
        const badge = document.createElement('div');
        badge.className = 'drishti-badge analyzing';
        badge.setAttribute('data-drishti', tileId);
        badge.innerHTML = `<span class="drishti-dot"></span><span class="drishti-label">${t.analyzing}</span>`;
        badge.addEventListener('click', (e) => { e.stopPropagation(); showTooltip(badge, tileId); });
        container.appendChild(badge);
    }

    function updateBadge(tileId, result) {
        const badge = document.querySelector(`[data-drishti="${CSS.escape(tileId)}"]`);
        if (!badge) return;

        const score = typeof result.score === 'number' ? result.score : 0;
        let cls, label, scoreText;

        if (result.source === 'offline' || result.verdict === 'UNKNOWN') {
            cls = 'offline'; label = t.offline; scoreText = '';
        } else if (score >= cfg.threshold) {
            cls = 'fake'; label = t.fake; scoreText = `${score.toFixed(0)}%`;
        } else if (score >= cfg.threshold - 20) {
            cls = 'uncertain'; label = t.uncertain; scoreText = `${score.toFixed(0)}%`;
        } else {
            cls = 'real'; label = t.real; scoreText = `${score.toFixed(0)}%`;
        }

        badge.className = `drishti-badge ${cls}`;
        badge.innerHTML = `
      <span class="drishti-dot"></span>
      <span class="drishti-label">${label}</span>
      ${scoreText ? `<span class="drishti-score">${scoreText}</span>` : ''}
    `;
        badge._result = result;

        if (cls === 'fake' && !alertShown) {
            alertShown = true;
            showAlertBanner(result.name || 'Participant');
            if (cfg.voiceAlerts) speakAlert(result.name || 'Participant');
            setTimeout(() => { alertShown = false; }, 30_000);
        }
    }

    // ── Frame capture helpers ───────────────────────────────────────────────────
    function captureVideoFrame(video, tileId, name) {
        analysisPending[tileId] = true;
        lastAnalysis[tileId] = Date.now();

        const W = Math.min(video.videoWidth || 320, 320);
        const H = Math.min(video.videoHeight || 240, 240);
        const canvas = document.createElement('canvas');
        canvas.width = W; canvas.height = H;

        try {
            canvas.getContext('2d').drawImage(video, 0, 0, W, H);
        } catch {
            analysisPending[tileId] = false;
            return;
        }
        sendForAnalysis(canvas.toDataURL('image/jpeg', 0.75).split(',')[1], tileId, name);
    }

    function captureAvatarFrame(container, tileId, name) {
        analysisPending[tileId] = true;
        lastAnalysis[tileId] = Date.now();

        try {
            const rect = container.getBoundingClientRect();
            const W = Math.min(Math.round(rect.width) || 320, 320);
            const H = Math.min(Math.round(rect.height) || 240, 240);
            const canvas = document.createElement('canvas');
            canvas.width = W; canvas.height = H;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#1a73e8';
            ctx.fillRect(0, 0, W, H);
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.round(H * 0.35)}px sans-serif`;
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText((name[0] || '?').toUpperCase(), W / 2, H / 2);
            sendForAnalysis(canvas.toDataURL('image/jpeg', 0.75).split(',')[1], tileId, name);
        } catch {
            analysisPending[tileId] = false;
        }
    }

    function sendForAnalysis(base64, tileId, name) {
        safeSend({
            type: 'ANALYZE_FRAME',
            frameBase64: base64,
            participantId: tileId,
            participantName: name,
        }, (result) => {
            analysisPending[tileId] = false;
            if (!result || result.skipped || result.error) {
                updateBadge(tileId, { score: 0, verdict: 'UNKNOWN', source: 'offline', name });
                return;
            }
            scanCount++;
            if ((result.score ?? 0) >= cfg.threshold) suspiciousCount++;
            updateBadge(tileId, result);
            updatePanel();
        });
    }

    // ── Tooltip ─────────────────────────────────────────────────────────────────
    let activeTooltip = null;
    function showTooltip(badge, tileId) {
        if (activeTooltip) { activeTooltip.remove(); activeTooltip = null; return; }
        const result = badge._result;
        if (!result) return;

        const tip = document.createElement('div');
        tip.className = 'drishti-tooltip';
        const verdict = (result.score ?? 0) >= cfg.threshold ? t.fake
            : (result.score ?? 0) >= cfg.threshold - 20 ? t.uncertain : t.real;
        const tagHtml = (result.tags || []).slice(0, 5)
            .map(tag => `<span class="tip-tag">${tag.replace(/_/g, ' ')}</span>`).join('');
        const expl = result.explanation
            ? `<div class="tip-expl">${result.explanation.slice(0, 180)}…</div>` : '';

        tip.innerHTML = `
      <div class="tip-title">${t.panel_title} — ${verdict.replace(/[✓⚠?◌]/g, '').trim()}</div>
      <div>AI Score: <b style="color:#00f5ff">${(result.score || 0).toFixed(1)}%</b> | Source: ${result.source === 'backend' ? 'API' : 'Local'}</div>
      <div style="margin-top:5px">${tagHtml || '<span style="color:#446688">No tags</span>'}</div>
      ${expl}
    `;
        badge.style.position = 'relative';
        badge.appendChild(tip);
        activeTooltip = tip;

        const dismiss = (e) => {
            if (!badge.contains(e.target)) {
                tip.remove(); activeTooltip = null;
                document.removeEventListener('click', dismiss);
            }
        };
        setTimeout(() => document.addEventListener('click', dismiss), 50);
    }

    // ── Alert Banner ────────────────────────────────────────────────────────────
    function injectAlertBanner() {
        if (document.getElementById('drishti-alert-banner')) return;
        const banner = document.createElement('div');
        banner.id = 'drishti-alert-banner';
        banner.className = 'fake-alert';
        banner.innerHTML = `
      <span>
        ${t.alert_msg} — <span id="drishti-alert-name"></span>
        <span style="font-weight:400;font-size:12px;opacity:.7;margin-left:10px">${t.alert_sub}</span>
      </span>
      <span class="alert-close" id="drishti-alert-close">✕</span>
    `;
        document.body.prepend(banner);
        document.getElementById('drishti-alert-close')
            .addEventListener('click', () => banner.classList.remove('show'));
    }

    function showAlertBanner(name) {
        const banner = document.getElementById('drishti-alert-banner');
        if (!banner) return;
        const nameEl = document.getElementById('drishti-alert-name');
        if (nameEl) nameEl.textContent = name;
        banner.classList.add('show');
        setTimeout(() => banner.classList.remove('show'), 8000);
    }

    // ── Floating Panel ──────────────────────────────────────────────────────────
    function injectPanel() {
        if (document.getElementById('drishti-panel')) return;
        const panel = document.createElement('div');
        panel.id = 'drishti-panel';
        panel.innerHTML = `
      <div id="drishti-panel-header">
        <span id="drishti-panel-title">${t.panel_title}</span>
        <span id="drishti-panel-toggle" title="Minimize">▼</span>
      </div>
      <div id="drishti-panel-body">
        <div class="drishti-panel-row">
          <span class="label">${t.backend}</span>
          <span class="value" id="drishti-be-status">
            <span id="drishti-backend-dot" class="dead"></span>
            <span id="drishti-be-text">${t.down}</span>
          </span>
        </div>
        <div class="drishti-panel-row">
          <span class="label">${t.scanned}</span>
          <span class="value" id="drishti-scan-count">0</span>
        </div>
        <div class="drishti-panel-row">
          <span class="label">${t.suspicious}</span>
          <span class="value danger" id="drishti-sus-count">0</span>
        </div>
        <div style="margin-top:8px;font-size:9px;color:#334455;text-align:center;font-family:'Share Tech Mono',monospace">
          DRISHTI v2 · Deepfake Detection
        </div>
      </div>
    `;
        document.body.appendChild(panel);

        document.getElementById('drishti-panel-toggle').addEventListener('click', () => {
            panelMinimized = !panelMinimized;
            document.getElementById('drishti-panel-body').style.display = panelMinimized ? 'none' : 'block';
            document.getElementById('drishti-panel-toggle').textContent = panelMinimized ? '▲' : '▼';
        });

        makeDraggable(panel);
        updatePanel();
    }

    function updatePanel() {
        const scanEl = document.getElementById('drishti-scan-count');
        const susEl = document.getElementById('drishti-sus-count');
        const dotEl = document.getElementById('drishti-backend-dot');
        const beText = document.getElementById('drishti-be-text');
        if (scanEl) scanEl.textContent = scanCount;
        if (susEl) {
            susEl.textContent = suspiciousCount;
            susEl.className = `value ${suspiciousCount > 0 ? 'danger' : 'safe'}`;
        }
        if (dotEl) dotEl.className = `be-dot ${backendAlive ? 'alive' : 'dead'}`;
        if (beText) beText.textContent = backendAlive ? t.online : t.down;
    }

    function makeDraggable(el) {
        let oX, oY, dragging = false;
        el.addEventListener('mousedown', (e) => {
            if (e.target.id === 'drishti-panel-toggle') return;
            dragging = true;
            oX = e.clientX - el.getBoundingClientRect().left;
            oY = e.clientY - el.getBoundingClientRect().top;
        });
        document.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            el.style.right = 'auto'; el.style.bottom = 'auto';
            el.style.left = (e.clientX - oX) + 'px';
            el.style.top = (e.clientY - oY) + 'px';
        });
        document.addEventListener('mouseup', () => { dragging = false; });
    }

    // ── Voice Alerts ────────────────────────────────────────────────────────────
    function speakAlert(name) {
        if (!('speechSynthesis' in window)) return;
        const langMap = { hi: 'hi-IN', es: 'es-ES', fr: 'fr-FR', ar: 'ar-SA', zh: 'zh-CN' };
        const utt = new SpeechSynthesisUtterance(
            `Warning! Deepfake detected for ${name}. Please verify this participant.`
        );
        utt.lang = langMap[cfg.language] || 'en-US';
        utt.rate = 0.95;
        window.speechSynthesis.speak(utt);
    }

})(); // ← End of IIFE guard
