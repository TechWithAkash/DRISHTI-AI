'use client';
import { useState } from 'react';
import { FileText, Zap, Search, Loader2 } from 'lucide-react';
import styles from '../analysis.module.css';
import AnalysisResult from '@/components/AnalysisResult';

const DEMO_TEXT = `The rapid advancement of artificial intelligence has fundamentally transformed how we interact with information and technology. Machine learning models, particularly large language models, have demonstrated remarkable capability in generating coherent and contextually appropriate text across diverse domains. These systems leverage sophisticated neural network architectures trained on vast corpora of human-generated content to produce outputs that increasingly mirror human writing styles and cognitive patterns.`;

export default function TextAnalysisPage() {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoad] = useState(false);
    const [error, setError] = useState('');

    async function analyze() {
        const t = text.trim();
        if (t.length < 50) { setError('Please enter at least 50 characters.'); return; }
        setLoad(true); setError(''); setResult(null);
        try {
            const r = await fetch('http://localhost:8000/analyze/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: t }),
            });
            if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Analysis failed'); }
            setResult(await r.json());
        } catch (e) {
            setError(e.message || 'Backend connection failed.');
        } finally { setLoad(false); }
    }

    // Highlight sentences by AI probability if result available
    function renderHighlighted() {
        if (!result?.sentence_scores) return null;
        return result.sentence_scores.map((s, i) => {
            const cls = s.score >= 0.7 ? styles.hlHigh : s.score >= 0.4 ? styles.hlMid : styles.hlLow;
            return (
                <span key={i} className={cls} title={`AI probability: ${(s.score * 100).toFixed(0)}%`}>
                    {s.text}{' '}
                </span>
            );
        });
    }

    return (
        <div className={styles.page}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={`${styles.pageTitle} title`} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <FileText size={28} color="#00f5ff" /> Text Analysis
                    </h1>
                    <p className={styles.pageSub}>
                        Detect AI-generated text with sentence-level heatmap using RoBERTa, Winston AI, Sapling AI ensemble.
                    </p>
                </div>
                <div className={styles.apiCaps}>
                    {['Winston AI', 'Sapling AI', 'RoBERTa', 'HuggingFace', 'Groq RAG', 'Sentence Heatmap'].map(api => (
                        <span key={api} className={`${styles.capBadge} mono`}>{api}</span>
                    ))}
                </div>
            </div>

            <div className={styles.grid2}>
                <div className={styles.uploadCol}>
                    <div className={`${styles.textArea} glass`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                            <p className="section-label" style={{ marginBottom: 0 }}>INPUT TEXT</p>
                            <button
                                className="btn btn-ghost"
                                style={{ fontSize: 11, padding: '4px 10px' }}
                                onClick={() => { setText(DEMO_TEXT); setResult(null); setError(''); }}
                            >
                                Load Demo Text
                            </button>
                        </div>
                        <textarea
                            className={`input ${styles.textarea}`}
                            rows={12}
                            placeholder="Paste text to analyze — minimum 50 characters…"
                            value={text}
                            onChange={e => { setText(e.target.value); setResult(null); }}
                        />
                        <div className={styles.textMeta}>
                            <span className="mono" style={{ fontSize: 11, color: '#2a5a70' }}>
                                {text.split(/\s+/).filter(Boolean).length} words · {text.length} chars
                            </span>
                            {text.length < 50 && text.length > 0 && (
                                <span className="mono" style={{ fontSize: 11, color: '#ff8866' }}>
                                    Need {50 - text.length} more characters
                                </span>
                            )}
                        </div>
                    </div>

                    <button
                        className={`btn btn-primary ${styles.analyzeBtn}`}
                        onClick={analyze}
                        disabled={text.trim().length < 50 || loading}
                        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                    >
                        {loading ? <><Loader2 size={18} className={styles.spin} /> Analyzing…</> : <><Zap size={18} /> Run Detection</>}
                    </button>
                    {error && <div className={styles.errorBox}>⚠ {error}</div>}

                    {/* Heatmap legend */}
                    {result?.sentence_scores && (
                        <div className={`${styles.legend} glass`}>
                            <p className="section-label" style={{ marginBottom: 10 }}>SENTENCE AI HEATMAP</p>
                            <div className={styles.legendItems}>
                                <span className={styles.hlHigh}>■ High AI (≥70%)</span>
                                <span className={styles.hlMid}>■ Medium (40–70%)</span>
                                <span className={styles.hlLow}>■ Low (&lt;40%)</span>
                            </div>
                            <div className={styles.highlightedText}>{renderHighlighted()}</div>
                        </div>
                    )}
                </div>

                <div className={styles.resultCol}>
                    {!result && !loading && (
                        <div className={styles.emptyResult}>
                            <div className={styles.emptyIcon}><Search size={48} color="#2a5a70" /></div>
                            <p>Paste text and click <strong>Run Detection</strong></p>
                            <p style={{ fontSize: 12, color: '#2a5a70', marginTop: 8 }}>Sentence-level AI probability heatmap</p>
                        </div>
                    )}
                    {loading && (
                        <div className={styles.scanningAnim}>
                            <div className={styles.scanBar} />
                            <p className="mono" style={{ color: '#00f5ff', fontSize: 12, letterSpacing: 2, marginTop: 20 }}>
                                ANALYZING TEXT PATTERNS…
                            </p>
                        </div>
                    )}
                    {result && <AnalysisResult result={result} modality="text" />}
                </div>
            </div>
        </div>
    );
}
