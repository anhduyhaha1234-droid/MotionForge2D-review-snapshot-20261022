import type { Metadata } from "next";
import { Geist_Mono, Inter, Outfit } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const outfit = Outfit({ variable: "--font-outfit", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MotionForge 2D",
  description: "Không gian sản xuất hoạt hình 2D, thay thế nhân vật và xuất video 4K.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi" className={`${inter.variable} ${outfit.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full bg-[var(--surface-950)] text-[var(--text-primary)] font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
