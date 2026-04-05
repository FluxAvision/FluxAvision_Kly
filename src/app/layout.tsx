import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FluxAvision - 客流统计系统",
  description: "FluxAvision智能客流统计与分析管理系统，实时客流数据展示与设备管理。",
  keywords: ["FluxAvision", "客流统计", "客流分析", "AI", "视频监控"],
  authors: [{ name: "FluxAvision Team" }],
  icons: {
    icon: "/logo.png",
  },
  openGraph: {
    title: "FluxAvision - 客流统计系统",
    description: "智能客流统计与分析管理系统",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
