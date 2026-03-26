import Link from "next/link";

import { bulkApproveImagesAction, bulkRegenerateImagesAction } from "../actions";
import { fetchApiJson } from "../lib/api";

type ImageReviewItem = {
  id: string;
  article_id: string;
  article_title: string;
  article_slug: string;
  alt_text: string;
  storage_url: string | null;
  local_path: string | null;
  is_featured: boolean;
  moderation_status: string;
  moderation_notes: string | null;
  created_at: string;
};

function statusTone(status: string): string {
  if (status === "approved") {
    return "success";
  }
  if (status === "rejected") {
    return "danger";
  }
  return "warn";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    generated: "Сгенерировано",
    approved: "Одобрено",
    rejected: "Отклонено",
    needs_regeneration: "Нужна перегенерация",
  };
  return labels[status] ?? status;
}

export default async function ImageReviewPage() {
  const queue = (await fetchApiJson<ImageReviewItem[]>("/images/review-queue")) ?? [];
  const imageIds = queue.map((item) => item.id);
  const featuredCount = queue.filter((item) => item.is_featured).length;
  const regularCount = queue.length - featuredCount;

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Image Review Queue</p>
          <h1>Модерация изображений</h1>
          <p className="hero-text">
            Здесь собраны все изображения, которые ещё не получили редакторское одобрение.
            Пока эта очередь не разобрана, статьи не смогут уйти в WordPress.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge warn">Manual review only</div>
          <div className="status-stack">
            <span>Текущая очередь</span>
            <strong>{queue.length} изображений</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Всего на ревью</span>
          <strong>{queue.length}</strong>
        </article>
        <article className="metric-card">
          <span>Обложки</span>
          <strong>{featuredCount}</strong>
        </article>
        <article className="metric-card">
          <span>Встроенные</span>
          <strong>{regularCount}</strong>
        </article>
        <article className="metric-card">
          <span>Статей затронуто</span>
          <strong>{new Set(queue.map((item) => item.article_id)).size}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Пакетные действия</p>
                <h2>Разобрать текущую очередь</h2>
              </div>
            </div>
            <div className="action-columns">
              <form action={bulkApproveImagesAction.bind(null, imageIds)}>
                <button className="action-button accent-button" type="submit">
                  Одобрить всю очередь
                </button>
              </form>
              <form action={bulkRegenerateImagesAction.bind(null, imageIds)}>
                <button className="action-button danger-button" type="submit">
                  Перегенерировать всю очередь
                </button>
              </form>
            </div>
            <p className="muted top-gap">
              Если хочешь точечную модерацию, открой нужную статью и используй approve/reject/regenerate прямо в карточке изображения.
            </p>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Очередь</p>
                <h2>Изображения, ожидающие решения</h2>
              </div>
            </div>
            <div className="stack">
              {queue.length ? (
                queue.map((image) => (
                  <article className="queue-item" key={image.id}>
                    <div className="queue-header">
                      <strong>
                        <Link href={`/articles/${image.article_id}`}>{image.article_title}</Link>
                      </strong>
                      <div className={`badge ${statusTone(image.moderation_status)}`}>{statusLabel(image.moderation_status)}</div>
                    </div>
                    <p>{image.is_featured ? "Обложка" : "Встроенное изображение"}</p>
                    <p className="muted">{image.alt_text}</p>
                    <p className="muted">{image.storage_url ?? image.local_path ?? "Путь к файлу отсутствует"}</p>
                    <p className="muted">{image.moderation_notes ?? "Комментариев модератора пока нет."}</p>
                    <p className="muted">Slug статьи: {image.article_slug}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Очередь изображений пуста. Все визуалы уже одобрены.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Правило публикации</p>
            <h2>Почему эта очередь важна</h2>
            <div className="stack">
              <div className="mini-chip">Статья не публикуется, пока обязательные изображения не одобрены.</div>
              <div className="mini-chip">Перегенерация возвращает изображение в статус ожидания.</div>
              <div className="mini-chip">Модерация всегда остаётся ручной, даже в fast lane.</div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Навигация</p>
            <h2>Быстрые переходы</h2>
            <div className="stack">
              <article className="topic-row">
                <strong>
                  <Link href="/">Вернуться на дашборд</Link>
                </strong>
                <span className="muted">Общий поток статей, fast lane и bulk-операции</span>
              </article>
              <article className="topic-row">
                <strong>
                  <Link href="/#article-queue">Открыть очередь статей</Link>
                </strong>
                <span className="muted">Статусы draft, review, approved и publish</span>
              </article>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
