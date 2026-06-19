import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ClaimVision",
  description: "AI-Powered Damage Claim Verification & Evidence Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-neutral-950 text-neutral-50">
        <nav className="border-b border-neutral-800 bg-neutral-900/50 sticky top-0 z-50 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-6">
              <a href="/" className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">ClaimVision</a>
              <div className="flex gap-4 ml-8">
                <a href="/" className="text-sm font-medium text-neutral-400 hover:text-white transition-colors">Batch Dashboard</a>
                <a href="/try-your-own" className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors">Try Your Own Claim ✨</a>
              </div>
            </div>
          </div>
        </nav>
        <main className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
