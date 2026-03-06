'use client';
import { useState, useEffect } from 'react';
import { LayoutDashboard, RefreshCw, AlertTriangle, CheckCircle, HelpCircle } from 'lucide-react';
import styles from './history.module.css';

const VERDICT_COLOR = {
    REAL: '#00ff77', AUTHENTIC: '#00ff77',
    UNCERTAIN: '#ffaa00',
    DEEPFAKE: '#ff3b3b', AI_GENERATED: '#ff3b3b',
    UNKNOWN: '#4a6a80',
};

function getVerdictIcon(verdict, color) {
    if (verdict === 'REAL' || verdict === 'AUTHENTIC') return <CheckCircle size={14} color={color} />;
    if (verdict === 'DEEPFAKE' || verdict === 'AI_GENERATED') return <AlertTriangle size={14} color={color} />;
    return <HelpCircle size={14} color={color} />;
}

function StatCard({ value, label, color }) {
    return (
        <div className={`${styles.statCard} glass`}>
            <div className="mono" style={{ fontSize: 36, color: color || '#00f5ff', fontWeight: 700 }}>{value}</div>
            <div className="mono" style={{ fontSize: 10, color: '#2a5a70', letterSpacing: 2, marginTop: 4 }}>{label}</div>
        </div>
    );
}

export default function HistoryPage() {
    const [stats, setStats] = useState(null);
    const [recent, setRecent] = useState([]);
    const [freq, setFreq] = useState([]);
    const [loading, setLoad] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        load();
    }, []);

    async function load() {
        setLoad(true); setError('');
        try {
            const [sRes, rRes, fRes] = await Promise.all([
                fetch('http://localhost:8000/graph/stats'),
                fetch('http://localhost:8000/graph/recent'),
                fetch('http://localhost:8000/graph/artifacts')
            ]);
            if (sRes.ok) setStats(await sRes.json());
            if (rRes.ok) setRecent(await rRes.json());
            if (fRes.ok) setFreq(await fRes.json());
        } catch {
            setError('Could not load graph data. Make sure Neo4j is configured and the backend is running.');
        } finally { setLoad(false); }
    }

    return (
        <div className={styles.page}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <LayoutDashboard size={28} color="#00f5ff" /> Scan History & Intelligence
                    </h1>
                    <p className={styles.pageSub}>Neo4j graph-powered threat intelligence — cross-referenced scan history and artifact patterns.</p>
                </div>
                <button className="btn btn-ghost" onClick={load} style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {error && <div className={styles.errorBox} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <AlertTriangle size={16} /> {error}
            </div>}

            {/* STATS */}
            {stats ? (
                <div className={styles.statsGrid}>
                    <StatCard value={stats.total_scans ?? 0} label="TOTAL SCANS" color="#00f5ff" />
                    <StatCard value={stats.total_fakes ?? 0} label="FAKES DETECTED" color="#ff3b3b" />
                    <StatCard value={stats.unique_artifacts ?? 0} label="UNIQUE ARTIFACTS" color="#ffaa00" />
                    <StatCard value={stats.detection_rate != null ? `${(stats.detection_rate * 100).toFixed(0)}%` : '–'} label="DETECTION RATE" color="#00ff77" />
                </div>
            ) : null}

            <div className={styles.grid2}>
                {/* RECENT SCANS */}
                <div>
                    <p className="section-label">RECENT DETECTIONS</p>
                    {loading && (
                        <div className={styles.loadBox}>
                            <div className={styles.spinner} />
                        </div>
                    )}
                    {!loading && recent.length === 0 && (
                        <div className={styles.emptyBox}>No scan history found. Run some analyses first.</div>
                    )}
                    {recent.map((scan, i) => {
                        const vColor = VERDICT_COLOR[scan.verdict] || '#4a6a80';
                        return (
                            <div key={i} className={`${styles.scanRow} glass`}>
                                <span className={styles.scanDot} style={{ background: vColor, boxShadow: `0 0 5px ${vColor}` }} />
                                <div className={styles.scanInfo}>
                                    <span className="mono" style={{ fontSize: 11, color: '#3a6a7a' }}>{scan.modality?.toUpperCase()}</span>
                                    <span style={{ marginLeft: 8, fontSize: 13, color: '#a8c8d8' }}>{scan.hash?.slice(0, 16)}…</span>
                                </div>
                                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span className="mono" style={{ fontSize: 13, color: vColor, fontWeight: 700 }}>
                                        {((scan.confidence ?? 0) * 100).toFixed(0)}%
                                    </span>
                                    <span className={styles.verdictPill} style={{ background: `${vColor}18`, border: `1px solid ${vColor}44`, color: vColor, display: 'flex', alignItems: 'center', gap: 4 }}>
                                        {getVerdictIcon(scan.verdict, vColor)} {scan.verdict}
                                    </span>
                                    <span className="mono" style={{ fontSize: 10, color: '#2a4a5a' }}>
                                        {scan.timestamp ? new Date(scan.timestamp).toLocaleTimeString() : ''}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* ARTIFACT FREQUENCY */}
                <div>
                    <p className="section-label">TOP FORENSIC ARTIFACTS</p>
                    {!loading && freq.length === 0 && (
                        <div className={styles.emptyBox}>No artifact data yet.</div>
                    )}
                    {freq.slice(0, 12).map((item, i) => {
                        const max = freq[0]?.count ?? 1;
                        const pct = Math.round((item.count / max) * 100);
                        return (
                            <div key={i} className={styles.freqRow}>
                                <span className="mono" style={{ fontSize: 11, color: '#3a6a7a', minWidth: 140 }}>
                                    {item.artifact?.replace(/_/g, ' ')}
                                </span>
                                <div className={styles.freqBarWrap}>
                                    <div className={styles.freqBar} style={{ width: `${pct}%` }} />
                                </div>
                                <span className="mono" style={{ fontSize: 11, color: '#00f5ff', minWidth: 32, textAlign: 'right' }}>
                                    {item.count}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
