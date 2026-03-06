'use client';
import { useCallback } from 'react';
import { UploadCloud } from 'lucide-react';
import styles from './UploadZone.module.css';

export default function UploadZone({ accept, label, hint, onFile }) {
    const onDrop = useCallback((e) => {
        e.preventDefault();
        const f = e.dataTransfer?.files?.[0];
        if (f) onFile(f);
    }, [onFile]);

    return (
        <label
            className={styles.zone}
            onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add(styles.dragOver); }}
            onDragLeave={e => e.currentTarget.classList.remove(styles.dragOver)}
            onDrop={e => { e.currentTarget.classList.remove(styles.dragOver); onDrop(e); }}
        >
            <input
                type="file" accept={accept} className={styles.input}
                onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); }}
            />
            <div className={styles.icon}><UploadCloud size={36} color="#00f5ff" /></div>
            <p className={styles.label}>{label}</p>
            <p className={styles.hint}>{hint}</p>
            <div className="btn btn-ghost" style={{ fontSize: 12, pointerEvents: 'none', marginTop: 8 }}>
                Browse Files
            </div>
        </label>
    );
}
