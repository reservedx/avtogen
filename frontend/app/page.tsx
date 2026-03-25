import Link from "next/link";

import {
  bulkCreateTopicsAction,
  bulkApproveAction,
  bulkGenerateImagesAction,
  bulkPublishAction,
  bulkSubmitForReviewAction,
  createDemoProjectAction,
  runBulkFastLaneTopicsAction,
  runBulkQualityCheckAction,
} from "./actions";
import { getDashboardData } from "./lib/dashboard";

function statusTone(status: string): string {
  if (status === "published" || status === "completed" || status === "approved" || status === "ready") {
    return "success";
  }
  if (status === "needs_revision" || status === "failed" || status === "rejected") {
    return "danger";
  }
  return "warn";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    published: "Опубликовано",
    completed: "Выполнено",
    approved: "Одобрено",
    ready: "Готово",
    warning: "Внимание",
    needs_revision: "Нужна доработка",
    failed: "Ошибка",
    in_review: "На ревью",
    rejected: "Отклонено",
    draft: "Черновик",
    running: "В работе",
    pending: "В ожидании",
    planned: "Запланировано",
    generated: "Сгенерировано",
    needs_regeneration: "Нужна перегенерация",
  };
  return labels[status] ?? status;
}

function scoreLabel(value: number | null, kind: "quality" | "risk"): string {
  if (value === null) {
    return kind === "quality" ? "QA ещё не запускался" : "Риск ещё не определён";
  }
  return `${kind === "quality" ? "Качество" : "Риск"}: ${value}/100`;
}

export default async function HomePage() {
  const data = await getDashboardData();
  const reviewQueue = data.articles.filter((article) => article.status !== "published").slice(0, 6);
  const published = data.articles.filter((article) => article.status === "published").slice(0, 4);
  const failedJobs = data.taskRuns.filter((task) => task.status === "failed").slice(0, 5);
  const pendingImages = data.imageReviewQueue.slice(0, 8);
  const leadArticle = reviewQueue[0] ?? data.articles[0];
  const reviewQueueIds = reviewQueue.map((article) => article.id);
  const approvedArticleIds = data.articles.filter((article) => article.status === "approved").map((article) => article.id);
  const topicQueueIds = data.topics.filter((topic) => topic.status !== "published").slice(0, 20).map((topic) => topic.id);

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Редакторский центр</p>
          <h1>Avtogen</h1>
          <p className="hero-text">
            Платформа собирает темы, прогоняет их по fast lane, создаёт черновики и готовит публикацию.
            Текст может идти по ускоренному маршруту, но изображения всегда требуют ручного одобрения перед отправкой в CMS.
          </p>
          <form action={createDemoProjectAction} className="hero-action">
            <button className="action-button accent-button hero-button" type="submit">
              Создать демо-проект
            </button>
          </form>
        </div>
        <div className="hero-status">
          <div className={`badge ${data.apiOnline ? "success" : "warn"}`}>
            {data.apiOnline ? "API онлайн" : "Режим превью"}
          </div>
          <div className="status-stack">
            <span>{data.settings.app_name}</span>
            <strong>{data.settings.app_env}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Тем в очереди</span>
          <strong>{data.metrics.topics_count}</strong>
        </article>
        <article className="metric-card">
          <span>Статей в системе</span>
          <strong>{data.metrics.articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Опубликовано</span>
          <strong>{data.metrics.published_articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Картинок на ревью</span>
          <strong>{data.imageReviewQueue.length}</strong>
        </article>
      </section>

      <section className="metrics-grid">
        <article className="metric-card">
          <span>Среднее качество</span>
          <strong>{data.analytics.average_quality_score ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Средний риск</span>
          <strong>{data.analytics.average_risk_score ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Главный тип источников</span>
          <strong>{data.analytics.source_type_counts[0]?.key ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Упавшие задачи</span>
          <strong>{failedJobs.length}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel spotlight">
            <div className="panel-head">
              <div>
                <p className="panel-label">Главная статья</p>
                <h2>{leadArticle?.title ?? "Пока нет статей"}</h2>
              </div>
              {leadArticle ? <div className={`badge ${statusTone(leadArticle.status)}`}>{statusLabel(leadArticle.status)}</div> : null}
            </div>
            {leadArticle ? (
              <div className="spotlight-grid">
                <div className="story-card">
                  <span className="kicker">Готовность</span>
                  <p>{scoreLabel(leadArticle.quality_score, "quality")}</p>
                  <p>{scoreLabel(leadArticle.risk_score, "risk")}</p>
                  <p className="muted">
                    {data.leadWorkspace?.current_version
                      ? `Версия ${data.leadWorkspace.current_version.version}, ${data.leadWorkspace.current_version.word_count} слов`
                      : "Версия ещё не сформирована"}
                  </p>
                </div>
                <div className="story-card">
                  <span className="kicker">Публикация</span>
                  <p>{leadArticle.cms_post_id ? `Пост в CMS #${leadArticle.cms_post_id}` : "Ещё не синхронизировано с CMS"}</p>
                  <p className="muted">
                    {data.leadWorkspace
                      ? `${data.leadWorkspace.images.length} изображений, ${data.leadWorkspace.editorial_reviews.length} ревью`
                      : "Детали рабочего пространства недоступны"}
                  </p>
                  <p className="muted">{leadArticle.published_url ?? "Ожидает QA, одобрения и публикации."}</p>
                </div>
              </div>
            ) : (
              <p className="muted">Создай демо-проект или импортируй темы списком, чтобы наполнить очередь.</p>
            )}
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Очередь статей</p>
                <h2>Материалы, требующие внимания</h2>
              </div>
            </div>
            <div className="action-columns top-gap">
              <form action={runBulkQualityCheckAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Запустить QA по очереди
                </button>
              </form>
              <form action={bulkSubmitForReviewAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">
                  Отправить очередь на ревью
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
                  Одобрить очередь
                </button>
              </form>
            </div>
            <div className="action-columns top-gap">
              <form action={bulkPublishAction.bind(null, approvedArticleIds)}>
                <button className="action-button accent-button" type="submit">
                  Опубликовать одобренные
                </button>
              </form>
            </div>
            <div className="stack">
              {reviewQueue.length ? (
                reviewQueue.map((article) => (
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
                  </article>
                ))
              ) : (
                <p className="muted">Очередь статей пока пуста.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Очередь изображений</p>
                <h2>Обязательная ручная модерация</h2>
              </div>
            </div>
            <p className="muted">
              Эти изображения не дадут статье уйти в публикацию, пока редактор не одобрит их или не отправит на перегенерацию.
            </p>
            <div className="stack top-gap">
              {pendingImages.length ? (
                pendingImages.map((image) => (
                  <article className="queue-item" key={image.id}>
                    <div className="queue-header">
                      <strong>
                        <Link href={`/articles/${image.article_id}`}>{image.article_title}</Link>
                      </strong>
                      <div className={`badge ${statusTone(image.moderation_status)}`}>{statusLabel(image.moderation_status)}</div>
                    </div>
                    <p>{image.is_featured ? "Обложка" : "Встроенное изображение"}</p>
                    <p className="muted">{image.alt_text}</p>
                    <p className="muted">{image.moderation_notes ?? "Комментариев по модерации пока нет."}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Все изображения уже разобраны редактором.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Fast Lane</p>
                <h2>Массовый прогон тем</h2>
              </div>
            </div>
            <p className="muted">
              Быстрый режим собирает источники, создаёт brief и draft, запускает QA и двигает low-risk темы дальше по конвейеру.
            </p>
            <div className="top-gap">
              <form action={runBulkFastLaneTopicsAction.bind(null, topicQueueIds)}>
                <button className="action-button accent-button" type="submit">
                  Запустить fast lane по очереди тем
                </button>
              </form>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Импорт тем</p>
                <h2>Добавить пачку тем списком</h2>
              </div>
            </div>
            <form className="action-form" action={bulkCreateTopicsAction}>
              <input name="cluster_name" placeholder="Название кластера" defaultValue="Bulk Imported Topics" />
              <input name="audience" placeholder="Аудитория" defaultValue="general audience" />
              <textarea
                name="topic_queries"
                placeholder={"Вставь темы по одной в строке\nчастое мочеиспускание без боли\nжжение при мочеиспускании у женщин\nниктурия у женщин"}
                rows={8}
              />
              <button className="action-button" type="submit">
                Импортировать темы
              </button>
            </form>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Опубликованные</p>
                <h2>Недавно синхронизированные статьи</h2>
              </div>
            </div>
            <div className="stack">
              {published.length ? (
                published.map((article) => (
                  <article className="published-row" key={article.id}>
                    <div>
                      <strong>
                        <Link href={`/articles/${article.id}`}>{article.title}</Link>
                      </strong>
                      <p className="muted">{article.published_url ?? "Опубликовано без URL"}</p>
                    </div>
                    <div className="published-meta">
                      <span>{article.cms_post_id ? `WP #${article.cms_post_id}` : "Ожидает синхронизации"}</span>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted">Опубликованные статьи появятся здесь после отправки в WordPress.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel settings-panel">
            <p className="panel-label">Настройки среды</p>
            <h2>Текущий runtime</h2>
            <dl className="settings-list">
              <div>
                <dt>Хранилище</dt>
                <dd>{data.settings.asset_storage_backend}</dd>
              </div>
              <div>
                <dt>Путь к ассетам</dt>
                <dd>{data.settings.asset_storage_dir}</dd>
              </div>
              <div>
                <dt>S3 bucket</dt>
                <dd>{data.settings.s3_bucket}</dd>
              </div>
              <div>
                <dt>Режим OpenAI</dt>
                <dd>{data.settings.openai_enabled ? "Боевой" : "Stub / отключено"}</dd>
              </div>
              <div>
                <dt>Автопубликация</dt>
                <dd>{data.settings.auto_publish_enabled ? "Включена" : "Выключена"}</dd>
              </div>
              <div>
                <dt>Fast publish</dt>
                <dd>{data.settings.fast_publish_enabled ? "Включен" : "Выключен"}</dd>
              </div>
              <div>
                <dt>Автоапрув low-risk</dt>
                <dd>{data.settings.auto_approve_low_risk ? "Да" : "Нет"}</dd>
              </div>
              <div>
                <dt>База данных</dt>
                <dd>{data.settings.database_is_sqlite ? "SQLite dev-режим" : "Внешняя база данных"}</dd>
              </div>
            </dl>
          </article>

          <article className="panel">
            <p className="panel-label">Готовность к запуску</p>
            <h2>{data.readiness.overall_status === "ready" ? "Прототип готов к запуску" : "Нужно проверить ещё несколько пунктов"}</h2>
            <p className="muted">{data.readiness.summary}</p>
            <div className="stack top-gap">
              {data.readiness.items.map((item) => (
                <article className="task-row" key={item.code}>
                  <div className="queue-header">
                    <strong>{item.label}</strong>
                    <div className={`badge ${statusTone(item.status)}`}>{statusLabel(item.status)}</div>
                  </div>
                  <p className="muted">{item.detail}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Мониторинг задач</p>
            <h2>Ошибки и рисковые запуски</h2>
            <div className="stack">
              {failedJobs.length ? (
                failedJobs.map((task) => (
                  <article className="task-row" key={task.id}>
                    <div className="queue-header">
                      <strong>{task.task_type}</strong>
                      <div className={`badge ${statusTone(task.status)}`}>{statusLabel(task.status)}</div>
                    </div>
                    <p className="muted">{task.error_message ?? "Текст ошибки отсутствует"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Сейчас нет упавших задач.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Аналитика</p>
            <h2>Статусы и состав источников</h2>
            <div className="stack">
              {data.analytics.article_status_counts.map((item) => (
                <article className="task-row" key={item.key}>
                  <div className="queue-header">
                    <strong>{statusLabel(item.key)}</strong>
                    <div className="badge">{item.count}</div>
                  </div>
                </article>
              ))}
              {data.analytics.source_type_counts.map((item) => (
                <article className="task-row" key={`source-${item.key}`}>
                  <div className="queue-header">
                    <strong>{item.key} источников</strong>
                    <div className="badge">{item.count}</div>
                  </div>
                </article>
              ))}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Темы</p>
            <h2>Текущая очередь кластеров</h2>
            <div className="stack">
              {data.topics.slice(0, 6).map((topic) => (
                <article className="topic-row" key={topic.id}>
                  <strong>
                    <Link href={`/topics/${topic.id}`}>{topic.working_title}</Link>
                  </strong>
                  <span className="muted">{topic.target_query}</span>
                  <div className={`badge ${statusTone(topic.status)}`}>{statusLabel(topic.status)}</div>
                </article>
              ))}
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
