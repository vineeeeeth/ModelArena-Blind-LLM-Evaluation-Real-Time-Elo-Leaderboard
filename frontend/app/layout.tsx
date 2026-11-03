import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Navbar } from "@/components/navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ModelArena – Blind LLM Comparison Platform",
  description: "Crowdsourced, blind LLM evaluations with online Elo & Bradley-Terry leaderboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary`}>
        <Providers>
          <div className="relative flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <footer className="border-t border-border/40 py-6 text-center text-xs text-muted-foreground">
              <div className="container mx-auto px-4">
                ModelArena – Open LLM Benchmarking Platform. Evaluated through blind pairwise user votes.
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}

