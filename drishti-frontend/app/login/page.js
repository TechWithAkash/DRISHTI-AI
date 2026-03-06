'use client';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Image as ImageIcon, Mic, FileText, Video, Shield, Globe, Zap } from 'lucide-react';
import styles from './login.module.css';
import { createMockJWT } from '@/lib/auth';

const DEMO = { email: 'akash@drishti.ai', password: 'Password@123' };

export default function LoginPage() {
    return (
        <Suspense fallback={<div className="grid-bg" style={{ minHeight: '100vh' }}>Loading...</div>}>
            <LoginContent />
        </Suspense>
    );
}

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (searchParams.get('demo') === 'true') {
            setEmail(DEMO.email);
            setPassword(DEMO.password);
        }
    }, [searchParams]);

    async function handleLogin(e) {
        e.preventDefault();
        setError('');
        setLoading(true);

        await new Promise(r => setTimeout(r, 800)); // simulate auth lag

        const users = JSON.parse(localStorage.getItem('drishti_users') || '[]');
        const user = users.find(u => u.email === email && u.password === password);

        if (user) {
            const token = createMockJWT({ email: user.email, name: user.name, role: 'analyst' });
            localStorage.setItem('drishti_token', token);
            router.push('/dashboard');
        } else if (email === DEMO.email && password === DEMO.password) {
            // Fallback demo user
            const token = createMockJWT({ email, name: 'Akash Vishwakarma', role: 'analyst' });
            localStorage.setItem('drishti_token', token);
            router.push('/dashboard');
        } else {
            setError('Invalid credentials. Please sign up or use demo login.');
        }
        setLoading(false);
    }

    function handleDemo() {
        setEmail(DEMO.email);
        setPassword(DEMO.password);
        setError('');
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
                        <h1 className={`${styles.cardTitle} title`}>Sign In</h1>
                        <p className={styles.cardSub}>Access the DRISHTI detection platform</p>
                    </div>

                    {error && (
                        <div className={styles.errorBox}>
                            <Shield size={16} /> {error}
                        </div>
                    )}

                    <form onSubmit={handleLogin} className={styles.form}>
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
                            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                        >
                            {loading ? <span className={styles.spinner} /> : <><Zap size={16} /> Sign In</>}
                        </button>
                    </form>

                    <div className={styles.divider}>
                        <span>or</span>
                    </div>

                    <button className={`btn btn-ghost ${styles.demoBtn}`} onClick={handleDemo} type="button" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Video size={16} /> Use Demo Credentials
                    </button>

                    <div className={styles.demoHint}>
                        <span className="mono" style={{ fontSize: 10, color: '#2a5a70', letterSpacing: 1 }}>
                            DEMO → {DEMO.email} / {DEMO.password}
                        </span>
                    </div>

                    <p className={styles.backLink} style={{ textAlign: 'center', marginTop: 16 }}>
                        <span style={{ color: '#4a6a80', fontSize: 13 }}>Need an account? </span>
                        <Link href="/signup">Sign up here</Link>
                    </p>
                </div>

                <p className={styles.backLink}>
                    <Link href="/">← Back to home</Link>
                </p>
            </div>
        </div>
    );
}
