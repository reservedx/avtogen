import type { ReactNode } from "react";
import Link from "next/link";

import "./globals.css";

export const metadata = {
  title: "Avtogen Control Center",
  description: "Редакторский центр для AI-платформы публикации статей о женском здоровье",
};

const navigationItems = [
  { href: "/", label: "Панель управления", hint: "Очереди, метрики и fast lane" },
  { href: "/topics", label: "Темы и research", hint: "Импорт тем и сбор research" },
  { href: "/articles", label: "Статьи и ревью", hint: "Редактура, QA и публикация" },
  { href: "/images", label: "Модерация изображений", hint: "Ручная проверка перед CMS" },
  { href: "/analytics", label: "Аналитика", hint: "Сводка по pipeline и ошибкам" },
  { href: "/jobs", label: "Задачи", hint: "Мониторинг task runs и статусов" },
  { href: "/system", label: "Система", hint: "Readiness, роли и глобальное состояние" },
  { href: "/settings", label: "Настройки", hint: "Глобальные runtime-параметры" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <div className="app-shell">
          <aside className="app-sidebar">
            <Link className="brand-card" href="/">
              <span className="brand-mark">A</span>
              <div>
                <strong>Avtogen</strong>
                <p>Control Center</p>
              </div>
            </Link>

            <nav className="sidebar-nav">
              {navigationItems.map((item) => (
                <Link className="nav-card" href={item.href} key={item.href}>
                  <strong>{item.label}</strong>
                  <span>{item.hint}</span>
                </Link>
              ))}
            </nav>

            <div className="sidebar-footer">
              <p className="panel-label">Режим</p>
              <strong>Editorial AI Ops</strong>
              <p>Быстрый поток текста с обязательной ручной модерацией изображений.</p>
            </div>
          </aside>

          <div className="app-main">
            <header className="topbar">
              <div>
                <p className="panel-label">Платформа</p>
                <h1 className="topbar-title">Avtogen</h1>
              </div>
              <div className="topbar-actions">
                <div className="badge success">AI workflow</div>
                <div className="badge warn">Image review required</div>
              </div>
            </header>

            <div className="app-content">{children}</div>
          </div>
        </div>
      </body>
    </html>
  );
}
