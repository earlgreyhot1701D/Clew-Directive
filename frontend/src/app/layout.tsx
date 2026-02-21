import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Clew Directive — AI Learning Navigator',
  description:
    'Free, personalized AI learning paths. No accounts, no tracking. Take the Vibe Check, get your Learning Path.',
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
      <body>{children}</body>
    </html>
  );
}
