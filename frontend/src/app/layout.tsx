import "./globals.css";
import { IBM_Plex_Mono } from "next/font/google";

const mono = IBM_Plex_Mono({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const metadata = {
  title: "Parser",
  description: "AI-powered concept-code inference",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={mono.className}>
        <div className="pb-hero">
          <div className="pb-container pb-hero-card">
            <div className="flex items-start gap-4">

              <div>
                <div className="pb-hero-title">Parser</div>
                <div className="pb-hero-subtitle">Find Concept-Codes in Text</div>
                <p className="pb-hero-desc">
                  Paste text (20,000+ words is fine), run inference, and get matched codes with confidence,
                  concepts, and an audit trail.
                </p>
                <div className="pb-actions">
                  <a href="/find-codes" className="pb-btn pb-btn-primary">
                    Start Parsing
                  </a>
                  <a href="#results" className="pb-btn pb-btn-outline">
                    Jump to Results
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="pb-divider">
          <div className="pb-container py-10">{children}</div>
        </div>
      </body>
    </html>
  );
}
