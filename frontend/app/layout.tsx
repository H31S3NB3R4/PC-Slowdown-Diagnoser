import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PC Diagnostic Report — System Performance Analysis",
  description: "Minimal diagnostic report detailing PC hardware bottlenecks and prioritized solutions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-[#FAFAF9] text-[#1A1A1A] min-h-screen flex flex-col antialiased selection:bg-[#4A6FA5]/20 selection:text-[#1A1A1A]">
        {children}
      </body>
    </html>
  );
}
