import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "政企标书助手 - Bidding Assistant",
  description: "广西区政企招投标智能防废标辅助系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        <header className="border-b bg-white shadow-sm sticky top-0 z-10">
          <div className="container mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="text-xl font-bold text-primary flex items-center gap-2">
              <span className="bg-primary text-white p-1 rounded-md">BA</span>
              标书助手 (Bidding Assistant)
            </Link>
            <nav className="flex items-center gap-6 text-sm font-medium">
              <Link href="/" className="hover:text-primary transition-colors">解析中心</Link>
              <Link href="/history" className="hover:text-primary transition-colors">历史项目</Link>
              <Link href="/settings" className="hover:text-primary transition-colors">AI 引擎配置</Link>
            </nav>
          </div>
        </header>
        <main className="p-4 md:p-8">
          {children}
        </main>
        <Toaster richColors position="top-center" />
      </body>
    </html>
  );
}
