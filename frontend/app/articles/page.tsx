import Link from "next/link";

import {
  bulkApproveAction,
  bulkGenerateImagesAction,
  bulkPublishAction,
  bulkSubmitForReviewAction,
  runBulkQualityCheckAction,
} from "../actions";
import { fetchApiJson } from "../lib/api";

type Article = {
  id: string;
  topic_id: string;
  title: string;
  slug: string;
  status: string;
  quality_score: number | null;
  risk_score: number | null;
  cms_post_id: string | null;
  published_url: string | null;
};

type ArticleBucket = {
  title: string;
  statuses: string[];
  description: string;
};

function statusTone(status: string): string {
  if (status === "published" || status === "approved") {
    return "success";
  }
  if (status === "rejected" || status === "needs_revision") {
    return "danger";
  }
  return "warn";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "Черновик",
    in_review: "На ревью",
    approved: "Одобрено",
    published: "Опубликовано",
    rejected: "Отклонено",
    needs_revision: "Нужна доработка",
  };
  return labels[status] ?? status;
}

function scoreLabel(value: number | null, kind: "quality" | "risk"): string {
  if (value === null) {
    return kind === "quality" ? "QA ещё не запускался" : "Риск ещё не определён";
  }
  return `${kind === "quality" ? "Качество" : "Риск"}: ${value}/100`;
}

function applyFilters(articles: Article[], status: string, query: string): Article[] {
  const normalizedQuery = query.trim().toLowerCase();
  return articles.filter((article) => {
    const statusMatch = status === "all" || article.status === status;
    const queryMatch =
      !normalizedQuery ||
      article.title.toLowerCase().includes(normalizedQuery) ||
      article.slug.toLowerCase().includes(normalizedQuery);
    return statusMatch && queryMatch;
  });
}

const buckets: ArticleBucket[] = [
  {
    title: "Черновики",
    statuses: ["draft", "needs_revision"],
    description: "Статьи, которые ещё редактируются, перегенерируются или ждут нового QA.",
  },
  {
    title: "На ревью",
    statuses: ["in_review"],
    description: "Материалы, которые редактор должен проверить перед одобрением.",
  },
  {
    title: "Готовы к публикации",
    statuses: ["approved"],
    description: "Статьи прошли ревью, но ещё не отправлены в WordPress.",
  },
  {
    title: "Опубликованные",
    statuses: ["published"],
    description: "Материалы уже синхронизированы с CMS.",
  },
];

export default async function ArticleQueuePage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = (await searchParams) ?? {};
  const currentStatus = typeof params.status === "string" ? params.status : "all";
  const currentQuery = typeof params.q === "string" ? params.q : "";

  const articles = (await fetchApiJson<Article[]>("/articles")) ?? [];
  const filteredArticles = applyFilters(articles, currentStatus, currentQuery);

  const reviewQueueIds = filteredArticles
    .filter((article) => article.status !== "published")
    .slice(0, 20)
    .map((article) => article.id);
  const approvedIds = filteredArticles.filter((article) => article.status === "approved").map((article) => article.id);

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Article Queue</p>
          <h1>Очередь статей</h1>
          <p className="hero-text">
            Отдельный экран для управления статусами статей. Здесь можно быстро запускать QA, отправлять материалы на ревью,
            одобрять и публиковать их без постоянного возврата на общий дашборд.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge success">Editorial workflow</div>
          <div className="status-stack">
            <span>Найдено по фильтру</span>
            <strong>{filteredArticles.length}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Черновики и доработка</span>
          <strong>{filteredArticles.filter((item) => ["draft", "needs_revision"].includes(item.status)).length}</strong>
        </article>
        <article className="metric-card">
          <span>На ревью</span>
          <strong>{filteredArticles.filter((item) => item.status === "in_review").length}</strong>
        </article>
        <article className="metric-card">
          <span>Одобрено</span>
          <strong>{filteredArticles.filter((item) => item.status === "approved").length}</strong>
        </article>
        <article className="metric-card">
          <span>Опубликовано</span>
          <strong>{filteredArticles.filter((item) => item.status === "published").length}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Глобальные фильтры</p>
                <h2>Поиск по очереди статей</h2>
              </div>
            </div>
            <form className="filter-bar" action="/articles" method="get">
              <input defaultValue={currentQuery} name="q" placeholder="Поиск по заголовку или slug" />
              <select defaultValue={currentStatus} name="status">
                <option value="all">Все статусы</option>
                <option value="draft">Черновик</option>
                <option value="needs_revision">Нужна доработка</option>
                <option value="in_review">На ревью</option>
                <option value="approved">Одобрено</option>
                <option value="published">Опубликовано</option>
              </select>
              <button className="action-button" type="submit">
                Применить
              </button>
            </form>
            <div className="filter-pills">
              <Link className="mini-chip" href="/articles">
                Сбросить фильтры
              </Link>
              <div className="mini-chip">Статус: {currentStatus === "all" ? "все" : statusLabel(currentStatus)}</div>
              <div className="mini-chip">Запрос: {currentQuery || "без поиска"}</div>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Пакетные действия</p>
                <h2>Быстрые операции по отфильтрованной очереди</h2>
              </div>
            </div>
            <div className="action-columns">
              <form action={runBulkQualityCheckAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Запустить QA
                </button>
              </form>
              <form action={bulkSubmitForReviewAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Отправить на ревью
                </button>
              </form>
            </div>
            <div className="action-columns top-gap">
              <form action={bulkGenerateImagesAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Сгенерировать изображения
                </button>
              </form>
              <form action={bulkApproveAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Одобрить статьи
                </button>
              </form>
            </div>
            <div className="action-columns top-gap">
              <form action={bulkPublishAction.bind(null, approvedIds)}>
                <button className="action-button accent-button" type="submit">
                  Опубликовать одобренные
                </button>
              </form>
            </div>
          </article>

          {buckets.map((bucket) => {
            const rows = filteredArticles.filter((article) => bucket.statuses.includes(article.status));
            return (
              <article className="panel" key={bucket.title}>
                <div className="panel-head">
                  <div>
                    <p className="panel-label">Сегмент</p>
                    <h2>{bucket.title}</h2>
                  </div>
                  <div className="badge">{rows.length}</div>
                </div>
                <p className="muted">{bucket.description}</p>
                <div className="stack top-gap">
                  {rows.length ? (
                    rows.map((article) => (
                      <article className="queue-item" key={article.id}>
                        <div className="queue-header">
                          <strong>
                            <Link href={`/articles/${article.id}`}>{article.title}</Link>
                          </strong>
                          <div className={`badge ${statusTone(article.status)}`}>{statusLabel(article.status)}</div>
                        </div>
                        <p>{scoreLabel(article.quality_score, "quality")}</p>
                        <p>{scoreLabel(article.risk_score, "risk")}</p>
                        <p className="muted">{article.slug}</p>
                        <p className="muted">
                          {article.published_url ?? (article.cms_post_id ? `CMS post #${article.cms_post_id}` : "Ещё не синхронизировано с CMS")}
                        </p>
                      </article>
                    ))
                  ) : (
                    <p className="muted">В этом сегменте нет статей для текущего фильтра.</p>
                  )}
                </div>
              </article>
            );
          })}
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Порядок работы</p>
            <h2>Как использовать очередь</h2>
            <div className="stack">
              <div className="mini-chip">Сначала прогони QA по новым или изменённым черновикам.</div>
              <div className="mini-chip">Потом отправь материалы на ревью и одобряй только готовые версии.</div>
              <div className="mini-chip">Публикация сработает только если у статьи уже одобрены изображения.</div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Навигация</p>
            <h2>Связанные экраны</h2>
            <div className="stack">
              <article className="topic-row">
                <strong>
                  <Link href="/">Открыть dashboard</Link>
                </strong>
                <span className="muted">Общие метрики, fast lane и импорт тем</span>
              </article>
              <article className="topic-row">
                <strong>
                  <Link href="/images">Открыть image review</Link>
                </strong>
                <span className="muted">Очередь картинок, блокирующих публикацию</span>
              </article>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
