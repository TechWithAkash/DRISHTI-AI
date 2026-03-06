'use client';
import { CheckCircle, HelpCircle, AlertTriangle, Timer, BrainCircuit, Film } from 'lucide-react';
import styles from './AnalysisResult.module.css';

const VERDICT_CONFIG = {
    REAL: { cls: styles.verdictReal, icon: <CheckCircle size={28} />, label: 'AUTHENTIC', color: '#00ff77' },
    AUTHENTIC: { cls: styles.verdictReal, icon: <CheckCircle size={28} />, label: 'AUTHENTIC', color: '#00ff77' },
    UNCERTAIN: { cls: styles.verdictUncertain, icon: <HelpCircle size={28} />, label: 'UNCERTAIN', color: '#ffaa00' },
    DEEPFAKE: { cls: styles.verdictFake, icon: <AlertTriangle size={28} />, label: 'DEEPFAKE', color: '#ff3b3b' },
    AI_GENERATED: { cls: styles.verdictFake, icon: <AlertTriangle size={28} />, label: 'AI-GENERATED', color: '#ff3b3b' },
    UNKNOWN: { cls: styles.verdictUnknown, icon: <HelpCircle size={28} />, label: 'UNKNOWN', color: '#4a6a80' },
};

function ConfidenceGauge({ score, color }) {
    const r = 60; const circ = Math.PI * r;
    const offset = circ - (Math.max(0, Math.min(100, score || 0)) / 100) * circ;
    return (
        <svg width="140" height="80" viewBox="0 0 140 80" className={styles.gauge}>
            <path d={`M 10 70 A ${r} ${r} 0 0 1 130 70`} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" strokeLinecap="round" />
            <path d={`M 10 70 A ${r} ${r} 0 0 1 130 70`} fill="none" stroke={color}
                strokeWidth="10" strokeLinecap="round"
                strokeDasharray={circ} strokeDashoffset={offset || 0}
                style={{ transition: 'stroke-dashoffset 1s ease', filter: `drop-shadow(0 0 6px ${color})` }}
            />
            <text x="70" y="68" textAnchor="middle" fill={color} fontSize="22" fontFamily="Share Tech Mono" fontWeight="bold">
                {Number(score || 0).toFixed(0)}%
            </text>
        </svg>
    );
}

export default function AnalysisResult({ result, modality }) {
    const verdict = result.verdict || 'UNKNOWN';
    const conf = result.confidence ?? result.score ?? 0;
    const confVisual = conf <= 1 ? conf * 100 : conf;
    const cfg = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.UNKNOWN;

    const indicators = result.indicators || result.tags?.map?.(t => ({ name: t, severity: 'medium', explanation: '' })) || [];
    const apiResults = result.api_results || [];

    return (
        <div className={`${styles.wrap} animate-fade-in`}>

            {/* VERDICT */}
            <div className={`${styles.verdict} ${cfg.cls}`}>
                <div className={styles.verdictLeft}>
                    <span className={styles.verdictIcon}>{cfg.icon}</span>
                    <div>
                        <div className={`${styles.verdictLabel} mono`}>{cfg.label}</div>
                        <div className={styles.verdictSub}>Analysis complete · {modality}</div>
                    </div>
                </div>
                <ConfidenceGauge score={confVisual} color={cfg.color} />
            </div>

            {/* ELAPSED */}
            {result.elapsed_s && (
                <div className={styles.metaRow} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Timer size={12} color="#2a5a70" />
                    <span className="mono" style={{ fontSize: 10, color: '#2a5a70' }}>
                        {result.elapsed_s.toFixed(2)}s · {(result.api_results?.length || 0)} APIs queried
                    </span>
                </div>
            )}

            {/* API RESULTS */}
            {apiResults.length > 0 && (
                <div className={styles.section}>
                    <p className="section-label">API SIGNALS</p>
                    <div className={styles.apiGrid}>
                        {apiResults.map((a, i) => {
                            const pct = a.score != null ? (a.score <= 1 ? a.score * 100 : a.score) : null;
                            const color = pct == null ? '#2a5a70' : pct >= 60 ? '#ff5555' : pct >= 35 ? '#ffaa00' : '#00ff77';
                            return (
                                <div key={i} className={styles.apiCard}>
                                    <div className={styles.apiSource}>{a.source || a.api}</div>
                                    <div style={{ fontSize: 18, fontFamily: 'monospace', color, fontWeight: 700 }}>
                                        {pct != null ? `${pct.toFixed(0)}%` : a.verdict || '–'}
                                    </div>
                                    <div className={styles.apiBar}>
                                        <div className={styles.apiBarFill} style={{ width: `${pct ?? 0}%`, background: color, boxShadow: `0 0 6px ${color}` }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* INDICATORS */}
            {indicators.length > 0 && (
                <div className={styles.section}>
                    <p className="section-label">FORENSIC INDICATORS</p>
                    <div className={styles.indicators}>
                        {indicators.map((ind, i) => {
                            const sev = ind.severity?.toLowerCase() || 'low';
                            return (
                                <div key={i} className={`${styles.indicator} ${styles['ind_' + sev]}`}>
                                    <div className={styles.indTop}>
                                        <span className={styles.indName}>{ind.name?.replace(/_/g, ' ')}</span>
                                        {ind.score != null && (
                                            <span className="mono" style={{ fontSize: 11, color: '#3a6a7a' }}>{(ind.score <= 1 ? ind.score * 100 : ind.score).toFixed(0)}%</span>
                                        )}
                                    </div>
                                    {ind.explanation && <p className={styles.indExpl}>{ind.explanation}</p>}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* EXTRACTED VIDEO FRAMES */}
            {result.frames && result.frames.length > 0 && (
                <div className={styles.section}>
                    <p className="section-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Film size={14} color="#00f5ff" /> EXTRACTED VIDEO FRAMES
                    </p>
                    <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 10 }}>
                        {result.frames.map((src, i) => (
                            <img key={i} src={src} style={{ height: 100, borderRadius: 6, border: '1px solid #1a3a4a', backgroundColor: '#07151e' }} alt={`Frame ${i}`} />
                        ))}
                    </div>
                </div>
            )}

            {/* RAG EXPLANATION */}
            {result.explanation && (
                <div className={styles.section}>
                    <p className="section-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <BrainCircuit size={14} color="#00f5ff" /> AI FORENSIC EXPLANATION
                    </p>
                    <div className={styles.ragBox}>
                        <p className={styles.ragText}>{result.explanation}</p>
                    </div>
                </div>
            )}

            {/* TAGS */}
            {result.tags?.length > 0 && (
                <div className={styles.section}>
                    <p className="section-label">ARTIFACT TAGS</p>
                    <div className={styles.tagWrap}>
                        {result.tags.map((tag, i) => (
                            <span key={i} className={`${styles.tag} mono`}>{tag.replace(/_/g, ' ')}</span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
