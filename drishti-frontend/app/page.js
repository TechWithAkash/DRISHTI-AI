'use client';
import Link from 'next/link';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  Image as ImageIcon, Mic, FileText, Video, Network, Shield,
  Play, Zap, ArrowRight, Activity, Crosshair, Cpu, Eye, Lock
} from 'lucide-react';
import { useEffect, useState } from 'react';
import styles from './page.module.css';

const FEATURES = [
  { icon: <ImageIcon size={28} color="#00e5ff" />, tag: 'IMAGE', title: 'Image Forensics', desc: 'Custom PyTorch EfficientNet-B4 + ELA heatmaps, GAN artifact detection.' },
  { icon: <Mic size={28} color="#00e5ff" />, tag: 'AUDIO', title: 'Voice Analysis', desc: 'Detect cloned voices with ZCR/pitch forensics & temporal shift detection.' },
  { icon: <FileText size={28} color="#00e5ff" />, tag: 'TEXT', title: 'AI Text Detection', desc: 'RoBERTa based sentence-level structural anomaly analysis.' },
  { icon: <Video size={28} color="#00e5ff" />, tag: 'VIDEO', title: 'Video Deepfake', desc: 'Frame-by-frame spatio-temporal detection using custom convolutional networks.' },
  { icon: <Network size={28} color="#00e5ff" />, tag: 'GRAPH', title: 'Neo4j Intelligence', desc: 'Cross-references scans and builds relational threat maps instantly.' },
  { icon: <Shield size={28} color="#00e5ff" />, tag: 'EXTENSION', title: 'Live Verification', desc: 'A Chrome Extension for persistent real-time Deepfake blocking.' },
];

const LAYERS = [
  { num: '01', delay: 0.1, label: 'Custom Pytorch Engine', detail: 'Trained locally on 100k+ hybrid AI/Real datasets' },
  { num: '02', delay: 0.2, label: 'Spatio-Temporal Sampling', detail: 'Interpolated frame consistency check' },
  { num: '03', delay: 0.3, label: 'Neo4j Graph Inference', detail: 'Adversarial actor threat mapping' },
  { num: '04', delay: 0.4, label: 'Llama 3 RAG Explainer', detail: 'Instant non-technical forensic explanations' },
];

export default function CrazyLandingPage() {
  const [mounted, setMounted] = useState(false);
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, -300]);

  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;

  return (
    <main className={styles.main}>

      {/* ── BACKGROUND FX ── */}
      <div className={styles.ambientBackground}>
        <div className={styles.glowOrbId1} />
        <div className={styles.glowOrbId2} />
        <div className={styles.gridOverlay} />
      </div>

      {/* ── NAV ── */}
      <motion.nav
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={styles.nav}
      >
        <div className={styles.navLogoContainer}>
          <Eye size={24} color="#00f5ff" />
          <span className={`${styles.navLogo} mono`}>DRISHTI v2</span>
        </div>
        <div className={styles.navLinks}>
          <a href="#features" className={styles.navLinkItem}>Intel</a>
          <a href="#architecture" className={styles.navLinkItem}>Core</a>
          <Link href="/login" className={styles.navLaunchBtn}>
            <span className={styles.launchBtnBg}></span>
            <span className={styles.launchBtnContent}>
              <Cpu size={14} className={styles.spinIcon} /> DEPLOY SCANNER
            </span>
          </Link>
        </div>
      </motion.nav>

      {/* ── HERO ── */}
      <section className={styles.heroSection}>
        <motion.div
          className={styles.heroContent}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ y }}
        >
          <div className={styles.heroBadge}>
            <span className={styles.liveDot} />
            <span className="mono">ACTIVE FORENSIC ENGINE</span>
          </div>

          <h1 className={`${styles.heroTitle} mono`}>
            <span className={styles.glitchText} data-text="DRISHTI">DRISHTI</span>
          </h1>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className={styles.heroSubTitle}
          >
            Terminal-Grade Multimodal Deepfake Defense
          </motion.h2>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className={styles.heroDesc}
          >
            A high-performance neural architecture designed to instantly tear through synthetic media signatures across Images, Audio, Video, and Text.
          </motion.p>

          <motion.div
            className={styles.heroActions}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, type: 'spring' }}
          >
            <Link href="/login" className={styles.cyberBtnPrimary}>
              <Zap size={18} /> ENTER DASHBOARD
              <div className={styles.btnScannerLine} />
            </Link>
            <Link href="/login?demo=true" className={styles.cyberBtnGhost}>
              <Play size={18} fill="currentColor" /> INITIATE DEMO
            </Link>
          </motion.div>
        </motion.div>

        {/* Hero Visual Radar */}
        <motion.div
          className={styles.heroVisual}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, delay: 0.5 }}
        >
          <div className={styles.holoRadarContainer}>
            <div className={styles.radarRing1} />
            <div className={styles.radarRing2} />
            <div className={styles.radarRing3} />
            <div className={styles.radarSweep} />
            <div className={styles.crosshairCenter}>
              <Crosshair size={32} color="#00e5ff" strokeWidth={1} />
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── METRICS BAR ── */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className={styles.metricsTicker}
      >
        <div className={styles.tickerItem}>
          <span className={styles.tickerValue}>99.6%</span>
          <span className={styles.tickerLabel}>DETECTION ACCURACY</span>
        </div>
        <div className={styles.tickerDivider} />
        <div className={styles.tickerItem}>
          <span className={styles.tickerValue}>0.4s</span>
          <span className={styles.tickerLabel}>INFERENCE TIME</span>
        </div>
        <div className={styles.tickerDivider} />
        <div className={styles.tickerItem}>
          <span className={styles.tickerValue}>6</span>
          <span className={styles.tickerLabel}>PROTECTION VECTORS</span>
        </div>
      </motion.div>

      {/* ── FEATURES GRID ── */}
      <section id="features" className={styles.featuresSection}>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className={styles.sectionHeader}
        >
          <h2 className={styles.sectionTitle}>THREAT VECTORS</h2>
          <div className={styles.sectionTitleUnderline} />
        </motion.div>

        <div className={styles.featuresGrid}>
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.tag}
              className={styles.featureCardWrap}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              whileHover={{ scale: 1.02 }}
            >
              <div className={styles.featureCardBorder}></div>
              <div className={styles.featureCard}>
                <div className={styles.cardGlowHover} />
                <div className={styles.featureIconWrap}>{f.icon}</div>
                <div className={`${styles.featureTag} mono`}>{f.tag}</div>
                <h3 className={styles.featureTitle}>{f.title}</h3>
                <p className={styles.featureDesc}>{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── ARCHITECTURE / PIPELINE ── */}
      <section id="architecture" className={styles.archSection}>
        <div className={styles.archContainer}>
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className={styles.archTextCol}
          >
            <h2 className={styles.archTitle}>Neural Analysis Pipeline</h2>
            <p className={styles.archDesc}>
              Drishti v2 abandons shallow heuristic flags for a deep, localized Multi-Layer Perceptron architecture. Data doesn't just pass through an API; it is shredded, analyzed at the tensor level, and verified across our internal Neo4j graph cluster.
            </p>

            <div className={styles.archList}>
              {LAYERS.map((layer) => (
                <motion.div
                  key={layer.num}
                  className={styles.archRow}
                  initial={{ opacity: 0, x: -30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: layer.delay }}
                >
                  <div className={styles.archDetailWrap}>
                    <div className={styles.archRowIcon}><Lock size={14} /></div>
                    <div>
                      <h4 className={styles.archRowLabel}>{layer.label}</h4>
                      <p className={styles.archRowDetail}>{layer.detail}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className={styles.archVisualCol}
          >
            <div className={styles.hologramCube}>
              <div className={styles.cubeFace1}></div>
              <div className={styles.cubeFace2}></div>
              <div className={styles.cubeFace3}></div>
              <div className={styles.cubeCore}>
                <Activity className={styles.cubeCoreIcon} size={40} color="#00e5ff" />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── PRE-FOOTER CTA ── */}
      <section className={styles.finalCta}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className={styles.ctaBox}
        >
          <h2 className={styles.ctaTitle}>INITIALIZE SUBSYSTEM</h2>
          <p className={styles.ctaSub}>Establish a secure dashboard instance to begin forensic scanning.</p>
          <Link href="/login" className={styles.cyberBtnPrimary} style={{ padding: '16px 40px', fontSize: 16 }}>
            <Shield size={20} /> AUTHORIZE ACCESS
          </Link>
        </motion.div>
      </section>

      {/* ── FOOTER ── */}
      <footer className={styles.footer}>
        <div className={styles.footerLine} />
        <p className="mono">DRISHTI SYSTEM v2.0 // DEEPFAKE COUNTERMEASURES // STATUS: <span style={{ color: '#00ffaa' }}>ONLINE</span></p>
      </footer>
    </main>
  );
}
