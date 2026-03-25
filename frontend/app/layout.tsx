import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "Avtogen Control Center",
  description: "Редакторский центр для AI-платформы публикации статей о женском здоровье",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
