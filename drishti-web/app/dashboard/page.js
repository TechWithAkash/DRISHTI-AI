'use client';
import { useState } from 'react';
import { Image as ImageIcon, Zap, Search, Loader2 } from 'lucide-react';
import styles from './analysis.module.css';
import AnalysisResult from '@/components/AnalysisResult';
import UploadZone from '@/components/UploadZone';

export default function ImageAnalysisPage() {
    const [file, setFile] = useState(null);
    const [preview, setPrev] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoad] = useState(false);
    const [error, setError] = useState('');

    function handleFile(f) {
        if (!f) return;
        setFile(f); setResult(null); setError('');
        const reader = new FileReader();
        reader.onload = e => setPrev(e.target.result);
        reader.readAsDataURL(f);
    }

    async function analyze() {
        if (!file) return;
        setLoad(true); setError(''); setResult(null);
        const fd = new FormData();
        fd.append('file', file);
        try {
            const r = await fetch('http://localhost:8000/analyze/image', { method: 'POST', body: fd });
            if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Analysis failed'); }
            const data = await r.json();
            setResult(data);
        } catch (e) {
            setError(e.message || 'Failed to connect to backend. Make sure it is running on port 8000.');
        } finally { setLoad(false); }
    }

    return (
        <div className={styles.page}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={`${styles.pageTitle} title`} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <ImageIcon size={28} color="#00f5ff" /> Image Analysis
                    </h1>
                    <p className={styles.pageSub}>
                        Upload an image to detect AI-generation or deepfake manipulation using 8 forensic layers.
                    </p>
                </div>
                <div className={styles.apiCaps}>
                    {['AI-or-Not', 'Sightengine', 'Hive', 'HuggingFace', 'ELA', 'DCT', 'EXIF', 'Groq RAG'].map(api => (
                        <span key={api} className={`${styles.capBadge} mono`}>{api}</span>
                    ))}
                </div>
            </div>

            <div className={styles.grid2}>
                {/* UPLOAD */}
                <div className={styles.uploadCol}>
                    <UploadZone
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        label="Drop an image here"
                        hint="JPG · PNG · WEBP · GIF — max 10 MB"
                        onFile={handleFile}
                    />

                    {preview && (
                        <div className={`${styles.previewBox} glass`}>
                            <p className="section-label" style={{ marginBottom: 12 }}>PREVIEW</p>
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={preview} alt="preview" className={styles.previewImg} />
                            <p className={styles.fileName}>{file?.name}</p>
                        </div>
                    )}

                    <button
                        className={`btn btn-primary ${styles.analyzeBtn}`}
                        onClick={analyze}
                        disabled={!file || loading}
                        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                    >
                        {loading ? <><Loader2 size={18} className={styles.spin} /> Analyzing…</> : <><Zap size={18} /> Run Detection</>}
                    </button>

                    {error && <div className={styles.errorBox}>⚠ {error}</div>}
                </div>

                {/* RESULTS */}
                <div className={styles.resultCol}>
                    {!result && !loading && (
                        <div className={styles.emptyResult}>
                            <div className={styles.emptyIcon}><Search size={48} color="#2a5a70" /></div>
                            <p>Upload an image and click <strong>Run Detection</strong></p>
                            <p style={{ fontSize: 12, color: '#2a5a70', marginTop: 8 }}>Uses 8-layer AI forensic pipeline</p>
                        </div>
                    )}
                    {loading && (
                        <div className={styles.scanningAnim}>
                            <div className={styles.scanBar} />
                            <p className="mono" style={{ color: '#00f5ff', fontSize: 12, letterSpacing: 2, marginTop: 20 }}>
                                ANALYZING FORENSIC SIGNALS…
                            </p>
                        </div>
                    )}
                    {result && <AnalysisResult result={result} modality="image" />}
                </div>
            </div>
        </div>
    );
}
