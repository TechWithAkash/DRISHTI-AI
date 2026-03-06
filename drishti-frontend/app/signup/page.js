'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Image as ImageIcon, Mic, FileText, Video, Shield, Globe, Zap, UserPlus } from 'lucide-react';
import styles from '../login/login.module.css'; // Reusing login styles for consistency
import { createMockJWT } from '@/lib/auth';

export default function SignupPage() {
    const router = useRouter();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    async function handleSignup(e) {
        e.preventDefault();
        setError('');

        if (password.length < 6) {
            setError('Password must be at least 6 characters.');
            return;
        }

        setLoading(true);
        await new Promise(r => setTimeout(r, 800)); // simulate auth lag

        // localstorage user saving
        const users = JSON.parse(localStorage.getItem('drishti_users') || '[]');
        if (users.find(u => u.email === email)) {
            setError('User with this email already exists.');
            setLoading(false);
            return;
        }

        users.push({ name, email, password });
        localStorage.setItem('drishti_users', JSON.stringify(users));

        // auto login
        const token = createMockJWT({ email, name, role: 'analyst' });
        localStorage.setItem('drishti_token', token);

        router.push('/dashboard');
    }

    return (
        <div className={`${styles.page} grid-bg`}>
            {/* LEFT PANEL */}
            <div className={styles.leftPanel}>
                <div className={styles.leftContent}>
                    <Link href="/" className={`${styles.logo} mono glow`}>DRISHTI</Link>
                    <p className={`${styles.logoSub} title`}>Deepfake Detection Platform</p>

                    <div className={styles.features}>
                        {[
                            { icon: <ImageIcon size={18} />, label: 'Image & Video Analysis' },
                            { icon: <Mic size={18} />, label: 'Voice Clone Detection' },
                            { icon: <FileText size={18} />, label: 'AI Text Forensics' },
                            { icon: <Video size={18} />, label: 'Real-time Video Scan' },
                            { icon: <Shield size={18} />, label: 'Google Meet Shield' },
                            { icon: <Globe size={18} />, label: '6-Language Support' },
                        ].map(f => (
                            <div key={f.label} className={styles.featureItem}>
                                <span className={styles.featureItemIcon}>{f.icon}</span>
                                <span className={styles.featureItemLabel}>{f.label}</span>
                            </div>
                        ))}
                    </div>

                    <div className={styles.leftBadge}>
                        <span className={styles.liveDot} />
                        <span className="mono" style={{ fontSize: 10, letterSpacing: 2, color: '#00d4ff' }}>BACKEND DETECTION ENGINE</span>
                    </div>
                </div>
                <div className={styles.leftGlow} />
            </div>

            {/* RIGHT PANEL - FORM */}
            <div className={styles.rightPanel}>
                <div className={`${styles.card} glass animate-fade-in`}>
                    <div className={styles.cardHeader}>
                        <h1 className={`${styles.cardTitle} title`}>Create Account</h1>
                        <p className={styles.cardSub}>Join the DRISHTI forensic platform</p>
                    </div>

                    {error && (
                        <div className={styles.errorBox} style={{ display: 'flex', gap: 6 }}>
                            <Shield size={16} /> {error}
                        </div>
                    )}

                    <form onSubmit={handleSignup} className={styles.form}>
                        <div className={styles.field}>
                            <label className="mono" style={{ fontSize: 10, letterSpacing: 2, color: '#4a6a80' }}>FULL NAME</label>
                            <input
                                type="text"
                                className="input"
                                placeholder="Akash Vishwakarma"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                required
                            />
                        </div>
                        <div className={styles.field}>
                            <label className="mono" style={{ fontSize: 10, letterSpacing: 2, color: '#4a6a80' }}>EMAIL ADDRESS</label>
                            <input
                                type="email"
                                className="input"
                                placeholder="analyst@agency.gov"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                required
                                autoComplete="email"
                            />
                        </div>
                        <div className={styles.field}>
                            <label className="mono" style={{ fontSize: 10, letterSpacing: 2, color: '#4a6a80' }}>PASSWORD</label>
                            <input
                                type="password"
                                className="input"
                                placeholder="••••••••"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className={`btn btn-primary ${styles.submitBtn}`}
                            disabled={loading}
                            style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}
                        >
                            {loading ? <span className={styles.spinner} /> : <><UserPlus size={16} /> Sign Up</>}
                        </button>
                    </form>

                    <p className={styles.backLink} style={{ textAlign: 'center', marginTop: 24 }}>
                        <span style={{ color: '#4a6a80', fontSize: 13 }}>Already have an account? </span>
                        <Link href="/login">Sign in here</Link>
                    </p>
                </div>

                <p className={styles.backLink}>
                    <Link href="/">← Back to home</Link>
                </p>
            </div>
        </div>
    );
}
