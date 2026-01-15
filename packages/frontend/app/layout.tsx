import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ConvexClientProvider } from "./providers/ConvexClientProvider";
import { Header } from "@/components/layout/Header";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "LineupIQ - Fantasy Football Predictions",
  description: "AI-powered fantasy football matchup predictions and lineup optimization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={jetbrainsMono.variable}>
      <body className="font-sans antialiased">
        <ConvexClientProvider>
          <Header />
          {children}
        </ConvexClientProvider>
      </body>
    </html>
  );
}
