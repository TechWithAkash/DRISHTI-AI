'use client';
import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { Image as ImageIcon, Mic, FileText, Video, LayoutDashboard, ChevronLeft, ChevronRight, LogOut, Activity } from 'lucide-react';
import styles from './layout.module.css';
import { parseMockJWT } from '@/lib/auth';

const NAV = [
    { href: '/dashboard', icon: <ImageIcon size={18} />, label: 'Image Analysis', tag: 'IMAGE' },
    { href: '/dashboard/audio', icon: <Mic size={18} />, label: 'Audio Analysis', tag: 'AUDIO' },
    { href: '/dashboard/text', icon: <FileText size={18} />, label: 'Text Analysis', tag: 'TEXT' },
    { href: '/dashboard/video', icon: <Video size={18} />, label: 'Video Analysis', tag: 'VIDEO' },
    { href: '/dashboard/history', icon: <LayoutDashboard size={18} />, label: 'Scan History', tag: 'GRAPH' },
];

export default function DashboardLayout({ children }) {
    const router = useRouter();
    const pathname = usePathname();
    const [user, setUser] = useState(null);
    const [backendOk, setBe] = useState(null);
    const [sidebarOpen, setSide] = useState(true);

    useEffect(() => {
        // Check JWT
        const token = localStorage.getItem('drishti_token');
        const u = token ? parseMockJWT(token) : null;

        if (!u) {
            localStorage.removeItem('drishti_token'); // clean if invalid
            router.replace('/login');
            return;
        }
        setUser(u);

        // Health check
        fetch('http://localhost:8000/health')
            .then(r => setBe(r.ok))
            .catch(() => setBe(false));

        const interval = setInterval(() => {
            fetch('http://localhost:8000/health').then(r => setBe(r.ok)).catch(() => setBe(false));
        }, 30000);
        return () => clearInterval(interval);
    }, [router]);

    function logout() {
        localStorage.removeItem('drishti_token');
        router.push('/login');
    }

    if (!user) return (
        <div className={styles.loading}>
            <div className={styles.loadingSpinner} />
        </div>
    );

    return (
        <div className={styles.shell}>
            {/* ── SIDEBAR ── */}
            <aside className={`${styles.sidebar} ${sidebarOpen ? '' : styles.sidebarClosed}`}>
                <div className={styles.sidebarTop}>
                    <Link href="/" className={`${styles.sidebarLogo} mono`}>DRISHTI</Link>
                    <span className={`${styles.sidebarVersion} mono`}>v2</span>
                </div>

                <p className="section-label" style={{ padding: '0 20px', marginBottom: 8, minHeight: 20 }}>
                    {sidebarOpen ? 'DETECTION MODULES' : ''}
                </p>

                <nav className={styles.nav}>
                    {NAV.map(item => {
                        const active = pathname === item.href;
                        return (
                            <Link key={item.href} href={item.href}
                                className={`${styles.navItem} ${active ? styles.navActive : ''}`}>
                                <span className={styles.navIcon}>{item.icon}</span>
                                {sidebarOpen && (
                                    <>
                                        <span className={styles.navLabel}>{item.label}</span>
                                        <span className={`${styles.navTag} mono`}>{item.tag}</span>
                                    </>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                <div className={styles.sidebarBottom}>
                    <div className={styles.beStatus} style={{ minHeight: 40, justifyContent: sidebarOpen ? 'flex-start' : 'center' }}>
                        {sidebarOpen ? (
                            <>
                                <span className={`${styles.beDot} ${backendOk === null ? styles.bePending : backendOk ? styles.beAlive : styles.beDead}`} />
                                <span className="mono" style={{ fontSize: 10, letterSpacing: 1, color: backendOk ? '#00ff77' : '#ff5555' }}>
                                    BACKEND {backendOk === null ? '...' : backendOk ? 'ONLINE' : 'OFFLINE'}
                                </span>
                            </>
                        ) : (
                            <Activity size={16} color={backendOk ? '#00ff77' : '#ff5555'} />
                        )}
                    </div>
                    <button className={styles.logoutBtn} onClick={logout} title="Sign out" style={{ justifyContent: sidebarOpen ? 'flex-start' : 'center', border: sidebarOpen ? undefined : 'none', background: sidebarOpen ? undefined : 'none' }}>
                        <LogOut size={16} />
                        {sidebarOpen && <span style={{ marginLeft: 8 }}>Sign Out</span>}
                    </button>
                </div>
            </aside>

            {/* ── MAIN ── */}
            <div className={styles.main}>
                {/* TOPBAR */}
                <header className={styles.topbar}>
                    <button className={styles.menuBtn} onClick={() => setSide(!sidebarOpen)} aria-label="Toggle sidebar">
                        {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
                    </button>
                    <div className={styles.breadcrumb}>
                        <span className="mono" style={{ color: '#2a5a70', fontSize: 11 }}>DRISHTI</span>
                        <span className="mono" style={{ color: '#1a3a50', fontSize: 11 }}> / </span>
                        <span className="mono" style={{ color: '#00f5ff', fontSize: 11, letterSpacing: 1 }}>
                            {NAV.find(n => n.href === pathname)?.label?.toUpperCase() || 'DASHBOARD'}
                        </span>
                    </div>
                    <div className={styles.topbarRight}>
                        <div className={`${styles.userChip} glass`}>
                            <div className={styles.userAvatar}>{user.name[0].toUpperCase()}</div>
                            <span style={{ fontSize: 13, fontWeight: 500, color: '#c8d8e8' }}>{user.name}</span>
                        </div>
                    </div>
                </header>

                {/* PAGE CONTENT */}
                <div className={styles.content}>{children}</div>
            </div>
        </div>
    );
}
