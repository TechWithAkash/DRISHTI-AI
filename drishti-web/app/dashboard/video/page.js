'use client';
import { useState } from 'react';
import { Video, Zap, Search, Loader2 } from 'lucide-react';
import styles from '../analysis.module.css';
import AnalysisResult from '@/components/AnalysisResult';
import UploadZone from '@/components/UploadZone';

export default function VideoAnalysisPage() {
    const [file, setFile] = useState(null);
    const [preview, setPrev] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoad] = useState(false);
    const [error, setError] = useState('');
    const [progress, setProgress] = useState(0);

    function handleFile(f) {
        if (!f) return;
        setFile(f); setResult(null); setError(''); setPrev(null);
        setPrev(URL.createObjectURL(f));
    }

    async function analyze() {
        if (!file) return;
        setLoad(true); setError(''); setResult(null); setProgress(0);
        // Simulate progress
        const prog = setInterval(() => setProgress(p => Math.min(p + Math.random() * 8, 90)), 600);
        const fd = new FormData();
        fd.append('file', file);
        try {
            const r = await fetch('http://localhost:8000/analyze/video', { method: 'POST', body: fd });
            if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Analysis failed'); }
            setResult(await r.json());
        } catch (e) {
            setError(e.message || 'Backend connection failed — ensure the backend server is running.');
        } finally {
            clearInterval(prog); setProgress(100);
            setTimeout(() => setLoad(false), 300);
        }
    }

    return (
        <div className={styles.page}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={`${styles.pageTitle} title`} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <Video size={28} color="#00f5ff" /> Video Analysis
                    </h1>
                    <p className={styles.pageSub}>
                        Frame-by-frame deepfake detection with temporal consistency analysis and facial artifact scoring.
                    </p>
                </div>
                <div className={styles.apiCaps}>
                    {['Sightengine', 'Hive Video', 'Frame Sampling', 'Temporal Analysis', 'Groq Whisper', 'RAG Explainer'].map(api => (
                        <span key={api} className={`${styles.capBadge} mono`}>{api}</span>
                    ))}
                </div>
            </div>

            <div className={styles.grid2}>
                <div className={styles.uploadCol}>
                    <UploadZone
                        accept="video/mp4,video/webm,video/mov,video/avi"
                        label="Drop a video here"
                        hint="MP4 · WEBM · MOV — max 100 MB"
                        onFile={handleFile}
                    />
                    {preview && (
                        <div className={`${styles.previewBox} glass`}>
                            <p className="section-label" style={{ marginBottom: 10 }}>PREVIEW</p>
                            <video controls src={preview} className={styles.previewImg} />
                            <p className={styles.fileName}>{file?.name} · {(file?.size / 1024 / 1024).toFixed(1)} MB</p>
                        </div>
                    )}

                    {loading && (
                        <div className={styles.progressBar}>
                            <div className={styles.progressFill} style={{ width: `${progress}%` }} />
                            <span className="mono" style={{ fontSize: 10, color: '#00f5ff' }}>{Math.round(progress)}%</span>
                        </div>
                    )}

                    <button className={`btn btn-primary ${styles.analyzeBtn}`} onClick={analyze} disabled={!file || loading} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {loading ? <><Loader2 size={18} className={styles.spin} /> Analyzing frames…</> : <><Zap size={18} /> Run Detection</>}
                    </button>
                    {error && <div className={styles.errorBox}>⚠ {error}</div>}
                </div>

                <div className={styles.resultCol}>
                    {!result && !loading && (
                        <div className={styles.emptyResult}>
                            <div className={styles.emptyIcon}><Search size={48} color="#2a5a70" /></div>
                            <p>Upload a video and click <strong>Run Detection</strong></p>
                            <p style={{ fontSize: 12, color: '#2a5a70', marginTop: 8 }}>Frame-by-frame deepfake detection</p>
                        </div>
                    )}
                    {loading && (
                        <div className={styles.scanningAnim}>
                            <div className={styles.scanBar} />
                            <p className="mono" style={{ color: '#00f5ff', fontSize: 12, letterSpacing: 2, marginTop: 20 }}>
                                SAMPLING VIDEO FRAMES…
                            </p>
                        </div>
                    )}
                    {result && <AnalysisResult result={result} modality="video" />}
                </div>
            </div>
        </div>
    );
}
