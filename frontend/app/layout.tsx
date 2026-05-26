import type { Metadata } from "next";
import { DM_Serif_Display, DM_Sans, DM_Mono } from "next/font/google";
import "./globals.css";

const dmSerif = DM_Serif_Display({ weight: ["400"], subsets: ["latin"], variable: "--font-display" });
const dmSans  = DM_Sans({ subsets: ["latin"], variable: "--font-body" });
const dmMono  = DM_Mono({ weight: ["400","500"], subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "RAG Agent",
  description: "Self-correcting RAG chatbot powered by Gemini Flash 2.5 + LangGraph",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${dmSerif.variable} ${dmSans.variable} ${dmMono.variable}`}>
      <body className="bg-paper font-body text-ink antialiased">{children}</body>
    </html>
  );
}
