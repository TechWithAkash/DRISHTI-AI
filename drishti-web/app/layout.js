import './globals.css';

export const metadata = {
  title: 'DRISHTI v2 — AI Deepfake Detection Platform',
  description: 'Enterprise-grade deepfake and synthetic media detection. Real-time analysis of images, audio, video, and text using 8-layer AI forensics.',
  keywords: 'deepfake detection, AI forensics, synthetic media, cybersecurity',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="theme-color" content="#070c16" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
      </head>
      <body>{children}</body>
    </html>
  );
}
