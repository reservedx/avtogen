import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Women Health Content Admin",
  description: "Editorial queue for AI-assisted women's health content",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
