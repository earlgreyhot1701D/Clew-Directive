import type { Metadata } from 'next';
import Script from 'next/script';
import './globals.css';

export const metadata: Metadata = {
  title: 'Clew Directive — AI Learning Navigator',
  description:
    'Free, personalized AI learning paths. No accounts. No personal data collected. Take the Vibe Check, get your Learning Path.',
  // WCAG: language declaration
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // WCAG 2.1: lang attribute for screen readers
    <html lang="en">
      <body>
        <Script
          defer
          src="https://cloud.umami.is/script.js"
          data-website-id="f00cdd65-9dc7-458f-815a-1a48f0d847ed"
          strategy="afterInteractive"
        />
        {children}
      </body>
    </html>
  );
}
