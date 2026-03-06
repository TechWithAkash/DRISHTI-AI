'use client';
import { useState } from 'react';
import { Mic, Zap, Search, Loader2 } from 'lucide-react';
import styles from '../analysis.module.css';
import AnalysisResult from '@/components/AnalysisResult';
import UploadZone from '@/components/UploadZone';

export default function AudioAnalysisPage() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoad] = useState(false);
    const [error, setError] = useState('');

    function handleFile(f) {
        if (!f) return;
        setFile(f); setResult(null); setError('');
    }

    async function analyze() {
        if (!file) return;
        setLoad(true); setError(''); setResult(null);
        const fd = new FormData();
        fd.append('file', file);
        try {
            const r = await fetch('http://localhost:8000/analyze/audio', { method: 'POST', body: fd });
            if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Analysis failed'); }
            setResult(await r.json());
        } catch (e) {
            setError(e.message || 'Backend connection failed.');
        } finally { setLoad(false); }
    }

    return (
        <div className={styles.page}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={`${styles.pageTitle} title`} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <Mic size={28} color="#00f5ff" /> Audio Analysis
                    </h1>
                    <p className={styles.pageSub}>
                        Detect voice cloning, AI-generated speech, and synthetic audio using multi-layer signal forensics.
                    </p>
                </div>
                <div className={styles.apiCaps}>
                    {['Resemble AI', 'Hive Audio', 'ZCR Forensics', 'Pitch Analysis', 'Groq Whisper', 'RAG Explainer'].map(api => (
                        <span key={api} className={`${styles.capBadge} mono`}>{api}</span>
                    ))}
                </div>
            </div>

            <div className={styles.grid2}>
                <div className={styles.uploadCol}>
                    <UploadZone
                        accept="audio/mpeg,audio/wav,audio/ogg,audio/mp4,audio/flac"
                        label="Drop audio file here"
                        hint="MP3 · WAV · OGG · FLAC — max 25 MB"
                        onFile={handleFile}
                    />
                    {file && (
                        <div className={`${styles.previewBox} glass`}>
                            <p className="section-label" style={{ marginBottom: 10 }}>LOADED FILE</p>
                            <div className={styles.audioPreview}>
                                <Mic size={32} color="#00f5ff" />
                                <div>
                                    <p style={{ color: '#c8d8e8', fontSize: 14 }}>{file.name}</p>
                                    <p className="mono" style={{ color: '#3a6a7a', fontSize: 11 }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            </div>
                            <audio controls src={URL.createObjectURL(file)} style={{ width: '100%', marginTop: 12, borderRadius: 6 }} />
                        </div>
                    )}
                    <button className={`btn btn-primary ${styles.analyzeBtn}`} onClick={analyze} disabled={!file || loading} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {loading ? <><Loader2 size={18} className={styles.spin} /> Analyzing…</> : <><Zap size={18} /> Run Detection</>}
                    </button>
                    {error && <div className={styles.errorBox}>⚠ {error}</div>}
                </div>

                <div className={styles.resultCol}>
                    {!result && !loading && (
                        <div className={styles.emptyResult}>
                            <div className={styles.emptyIcon}><Search size={48} color="#2a5a70" /></div>
                            <p>Upload an audio file and click <strong>Run Detection</strong></p>
                            <p style={{ fontSize: 12, color: '#2a5a70', marginTop: 8 }}>Voice clone and synthesis detection</p>
                        </div>
                    )}
                    {loading && (
                        <div className={styles.scanningAnim}>
                            <div className={styles.scanBar} />
                            <p className="mono" style={{ color: '#00f5ff', fontSize: 12, letterSpacing: 2, marginTop: 20 }}>
                                ANALYZING AUDIO SIGNALS…
                            </p>
                        </div>
                    )}
                    {result && <AnalysisResult result={result} modality="audio" />}
                </div>
            </div>
        </div>
    );
}
