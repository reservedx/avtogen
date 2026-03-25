import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchApiJson } from "../../lib/api";
import {
  approveArticleAction,
  approveImageAction,
  publishArticleAction,
  regenerateImageAction,
  regenerateSectionAction,
  rejectArticleAction,
  rejectImageAction,
  runQualityCheckAction,
  saveManualVersionAction,
  submitForReviewAction,
} from "./actions";

type IssueItem = {
  code?: string;
  message?: string;
};

type ArticleWorkspace = {
  article: {
    id: string;
    title: string;
    slug: string;
    status: string;
    quality_score: number | null;
    risk_score: number | null;
    cms_post_id: string | null;
    published_url: string | null;
  };
  current_version: {
    id: string;
    version: number;
    word_count: number;
    content_markdown: string;
    excerpt: string | null;
    meta_title: string;
    meta_description: string;
  } | null;
  versions: Array<{
    id: string;
    version: number;
    word_count: number;
    created_at: string;
    created_by: string;
    generation_context: Record<string, unknown>;
    content_markdown: string;
  }>;
  images: Array<{
    id: string;
    alt_text: string;
    storage_url: string | null;
    local_path: string | null;
    is_featured: boolean;
    moderation_status: string;
    moderation_notes: string | null;
  }>;
  latest_quality_report: {
    quality_score: number;
    risk_score: number;
    report_json: {
      overall_status?: string;
      blockers?: IssueItem[];
      warnings?: IssueItem[];
    };
  } | null;
  publishing_job: {
    status: string;
    updated_at: string;
  } | null;
  editorial_reviews: Array<{
    id: string;
    reviewer_name: string;
    decision: string;
    notes: string | null;
    created_at: string;
  }>;
  topic: {
    id: string;
    working_title: string;
    target_query: string;
    audience: string;
    status: string;
  } | null;
  sources: Array<{
    id: string;
    source_type: string;
    title: string;
    url: string;
    reliability_score: number | null;
  }>;
  research_notes: Array<{
    id: string;
    fact_type: string;
    content: string;
    confidence_score: number;
    citation_data: { url?: string; title?: string } | null;
  }>;
  brief: {
    id: string;
    version: number;
    brief_json: {
      primary_keyword?: string;
      search_intent?: string;
      required_sections?: string[];
      faq_questions?: string[];
      medical_safety_notes?: string[];
    };
  } | null;
};

function tone(status: string): string {
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
    published: "Опубликовано",
    approved: "Одобрено",
    rejected: "Отклонено",
    needs_revision: "Нужна доработка",
    in_review: "На ревью",
    draft: "Черновик",
    pending: "В ожидании",
    running: "В работе",
    completed: "Завершено",
    failed: "Ошибка",
  };
  return labels[status] ?? status;
}

function issueLabel(item: IssueItem): string {
  return item.message ?? item.code ?? "Проблема";
}

function imageModerationLabel(status: string): string {
  const labels: Record<string, string> = {
    generated: "Сгенерировано",
    approved: "Одобрено",
    rejected: "Отклонено",
    needs_regeneration: "Нужна перегенерация",
  };
  return labels[status] ?? status;
}

export default async function ArticleWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const workspace = await fetchApiJson<ArticleWorkspace>(`/articles/${id}/workspace`);

  if (!workspace) {
    notFound();
  }

  const blockers = workspace.latest_quality_report?.report_json.blockers ?? [];
  const warnings = workspace.latest_quality_report?.report_json.warnings ?? [];
  const previousVersion = workspace.versions.find((version) => version.id !== workspace.current_version?.id);
  const imagesApproved =
    workspace.images.length > 0 &&
    workspace.images.some((image) => image.is_featured) &&
    workspace.images.every((image) => image.moderation_status === "approved");

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Рабочая область статьи</p>
          <h1>{workspace.article.title}</h1>
          <p className="hero-text">
            <Link href="/">Назад к дашборду</Link>
            {" / "}
            {workspace.article.slug}
          </p>
        </div>
        <div className="hero-status">
          <div className={`badge ${tone(workspace.article.status)}`}>{statusLabel(workspace.article.status)}</div>
          <div className="status-stack">
            <span>Текущая версия</span>
            <strong>{workspace.current_version ? `v${workspace.current_version.version}` : "Версия ещё не создана"}</strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Управление</p>
                <h2>Редакторские действия</h2>
              </div>
            </div>
            <div className="action-grid">
              <form action={runQualityCheckAction.bind(null, id)}>
                <button className="action-button" type="submit">
                  Запустить QA
                </button>
              </form>
              <form action={submitForReviewAction.bind(null, id)}>
                <button className="action-button" type="submit">
                  Отправить на ревью
                </button>
              </form>
              <form action={publishArticleAction.bind(null, id)}>
                <button className="action-button accent-button" disabled={!imagesApproved} type="submit">
                  Опубликовать
                </button>
              </form>
            </div>
            <div className="top-gap">
              <p className="panel-label">Публикация</p>
              <p className="muted">
                {!imagesApproved
                  ? "Публикация заблокирована, пока все изображения не будут одобрены редактором."
                  : "Все обязательные изображения одобрены и статья может быть отправлена в CMS."}
              </p>
            </div>
            <div className="action-columns">
              <form className="action-form" action={approveArticleAction.bind(null, id)}>
                <h3>Одобрить статью</h3>
                <input name="reviewer_name" placeholder="Имя редактора" defaultValue="Editor" />
                <textarea name="notes" placeholder="Комментарий к одобрению" rows={4} />
                <button className="action-button" type="submit">
                  Одобрить
                </button>
              </form>
              <form className="action-form" action={rejectArticleAction.bind(null, id)}>
                <h3>Отклонить статью</h3>
                <input name="reviewer_name" placeholder="Имя редактора" defaultValue="Editor" />
                <textarea name="notes" placeholder="Причина отклонения" rows={4} />
                <button className="action-button danger-button" type="submit">
                  Отклонить
                </button>
              </form>
            </div>
            <form className="action-form" action={regenerateSectionAction.bind(null, id)}>
              <h3>Перегенерировать раздел</h3>
              <input name="section_heading" placeholder="FAQ" defaultValue="FAQ" />
              <textarea
                name="instructions"
                placeholder="Опиши, что нужно изменить в выбранном разделе"
                rows={4}
              />
              <button className="action-button" type="submit">
                Создать новую версию
              </button>
            </form>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Текущий черновик</p>
                <h2>Предпросмотр Markdown</h2>
              </div>
            </div>
            <div className="draft-meta">
              <span>{workspace.current_version ? `${workspace.current_version.word_count} слов` : "Нет данных по длине"}</span>
              <span>{workspace.current_version?.meta_title ?? "Meta title пока не заполнен"}</span>
            </div>
            <pre className="markdown-preview">
              {workspace.current_version?.content_markdown ?? "Контент пока отсутствует"}
            </pre>
            {workspace.current_version ? (
              <div className="version-diff-grid">
                <article className="diff-card">
                  <p className="panel-label">Текущая версия</p>
                  <h3>v{workspace.current_version.version}</h3>
                  <p className="muted">{workspace.current_version.word_count} слов</p>
                  <div className="content-snippet">
                    {workspace.current_version.content_markdown.slice(0, 700)}
                  </div>
                </article>
                <article className="diff-card">
                  <p className="panel-label">Предыдущая версия</p>
                  <h3>{previousVersion ? `v${previousVersion.version}` : "Пока нет предыдущей версии"}</h3>
                  <p className="muted">
                    {previousVersion ? `${previousVersion.word_count} слов` : "Сравнение появится после следующего изменения."}
                  </p>
                  <div className="content-snippet">
                    {previousVersion?.content_markdown
                      ? previousVersion.content_markdown.slice(0, 700)
                      : "История изменений пока не накопилась."}
                  </div>
                </article>
              </div>
            ) : null}
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Ручная правка</p>
                <h2>Сохранить новую версию от редактора</h2>
              </div>
            </div>
            <form className="action-form" action={saveManualVersionAction.bind(null, id)}>
              <input name="title" placeholder="Заголовок статьи" defaultValue={workspace.article.title} />
              <input name="slug" placeholder="slug" defaultValue={workspace.article.slug} />
              <input name="editor_name" placeholder="Имя редактора" defaultValue="Editor" />
              <input
                name="meta_title"
                placeholder="Meta title"
                defaultValue={workspace.current_version?.meta_title ?? ""}
              />
              <textarea
                name="meta_description"
                placeholder="Meta description"
                rows={3}
                defaultValue={workspace.current_version?.meta_description ?? ""}
              />
              <textarea
                name="excerpt"
                placeholder="Краткое описание"
                rows={3}
                defaultValue={workspace.current_version?.excerpt ?? ""}
              />
              <textarea name="change_note" placeholder="Что изменено в этой версии" rows={2} />
              <textarea
                name="content_markdown"
                placeholder="Markdown статьи"
                rows={20}
                defaultValue={workspace.current_version?.content_markdown ?? ""}
              />
              <button className="action-button accent-button" type="submit">
                Сохранить ручную версию
              </button>
            </form>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">История</p>
                <h2>Версии и ревью</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.versions.map((version) => (
                <article className="queue-item" key={version.id}>
                  <div className="queue-header">
                    <strong>Версия {version.version}</strong>
                    <div className="badge">{version.created_by}</div>
                  </div>
                  <p>{version.word_count} слов</p>
                  <p className="muted">{new Date(version.created_at).toLocaleString("ru-RU")}</p>
                  <p className="muted">{JSON.stringify(version.generation_context)}</p>
                </article>
              ))}
            </div>
            <div className="stack top-gap">
              {workspace.editorial_reviews.map((review) => (
                <article className="queue-item" key={review.id}>
                  <div className="queue-header">
                    <strong>{review.reviewer_name}</strong>
                    <div className={`badge ${tone(review.decision)}`}>{statusLabel(review.decision)}</div>
                  </div>
                  <p>{review.notes ?? "Без комментариев"}</p>
                  <p className="muted">{new Date(review.created_at).toLocaleString("ru-RU")}</p>
                </article>
              ))}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Quality Gate</p>
            <h2>Последний отчёт</h2>
            <div className="settings-list">
              <div>
                <dt>Оценка качества</dt>
                <dd>{workspace.latest_quality_report?.quality_score ?? "Не запускалось"}</dd>
              </div>
              <div>
                <dt>Оценка риска</dt>
                <dd>{workspace.latest_quality_report?.risk_score ?? "Не запускалось"}</dd>
              </div>
              <div>
                <dt>Статус</dt>
                <dd>{workspace.latest_quality_report?.report_json.overall_status ?? "Неизвестно"}</dd>
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Блокеры</p>
              <div className="stack">
                {blockers.length ? (
                  blockers.map((item) => (
                    <div className="mini-chip danger-chip" key={issueLabel(item)}>
                      {issueLabel(item)}
                    </div>
                  ))
                ) : (
                  <p className="muted">Блокеров нет</p>
                )}
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Предупреждения</p>
              <div className="stack">
                {warnings.length ? (
                  warnings.map((item) => (
                    <div className="mini-chip warn-chip" key={issueLabel(item)}>
                      {issueLabel(item)}
                    </div>
                  ))
                ) : (
                  <p className="muted">Предупреждений нет</p>
                )}
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Контекст темы</p>
            <h2>{workspace.topic?.working_title ?? "Тема не найдена"}</h2>
            <div className="settings-list">
              <div>
                <dt>Запрос</dt>
                <dd>{workspace.topic?.target_query ?? "—"}</dd>
              </div>
              <div>
                <dt>Аудитория</dt>
                <dd>{workspace.topic?.audience ?? "—"}</dd>
              </div>
              <div>
                <dt>Статус темы</dt>
                <dd>{workspace.topic?.status ? statusLabel(workspace.topic.status) : "—"}</dd>
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">ТЗ</p>
            <h2>{workspace.brief ? `Версия ${workspace.brief.version}` : "ТЗ пока не создано"}</h2>
            {workspace.brief ? (
              <>
                <div className="settings-list">
                  <div>
                    <dt>Основной ключ</dt>
                    <dd>{workspace.brief.brief_json.primary_keyword ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>Интент</dt>
                    <dd>{workspace.brief.brief_json.search_intent ?? "—"}</dd>
                  </div>
                </div>
                <div className="top-gap">
                  <p className="panel-label">Обязательные разделы</p>
                  <div className="stack">
                    {(workspace.brief.brief_json.required_sections ?? []).slice(0, 8).map((section) => (
                      <div className="mini-chip" key={section}>
                        {section}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="top-gap">
                  <p className="panel-label">Медицинские заметки</p>
                  <div className="stack">
                    {(workspace.brief.brief_json.medical_safety_notes ?? []).slice(0, 4).map((note) => (
                      <div className="mini-chip warn-chip" key={note}>
                        {note}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="muted">ТЗ для этой статьи пока не создано.</p>
            )}
          </article>

          <article className="panel">
            <p className="panel-label">Исходные материалы</p>
            <h2>Источники по теме</h2>
            <div className="stack">
              {workspace.sources.length ? (
                workspace.sources.map((source) => (
                  <article className="topic-row" key={source.id}>
                    <strong>{source.title}</strong>
                    <span className="muted">{source.source_type}</span>
                    <span className="muted">{source.url}</span>
                    <span className="muted">Надёжность: {source.reliability_score ?? "неизвестно"}</span>
                  </article>
                ))
              ) : (
                <p className="muted">Источников пока нет.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Research Notes</p>
            <h2>Факты и сигналы</h2>
            <div className="stack">
              {workspace.research_notes.length ? (
                workspace.research_notes.slice(0, 8).map((note) => (
                  <article className="queue-item" key={note.id}>
                    <div className="queue-header">
                      <strong>{note.fact_type}</strong>
                      <div className="badge">{Math.round(note.confidence_score * 100)}%</div>
                    </div>
                    <p>{note.content}</p>
                    <p className="muted">
                      {note.citation_data?.title ?? note.citation_data?.url ?? "Источник не указан"}
                    </p>
                  </article>
                ))
              ) : (
                <p className="muted">Research notes пока отсутствуют.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Изображения</p>
            <h2>Модерация перед публикацией</h2>
            <div className="stack">
              {workspace.images.length ? (
                workspace.images.map((image) => (
                  <article className="queue-item" key={image.id}>
                    <div className="queue-header">
                      <strong>{image.is_featured ? "Обложка" : "Встроенное изображение"}</strong>
                      <div className={`badge ${tone(image.moderation_status)}`}>{imageModerationLabel(image.moderation_status)}</div>
                    </div>
                    <p>{image.alt_text}</p>
                    <p className="muted">{image.storage_url ?? image.local_path ?? "Путь к файлу отсутствует"}</p>
                    <p className="muted">{image.moderation_notes ?? "Комментариев по модерации пока нет."}</p>
                    <div className="action-columns">
                      <form className="action-form" action={approveImageAction.bind(null, id, image.id)}>
                        <h3>Одобрить изображение</h3>
                        <input name="moderator_name" placeholder="Имя редактора" defaultValue="Editor" />
                        <textarea name="notes" placeholder="Почему изображение подходит" rows={3} />
                        <button className="action-button" type="submit">
                          Одобрить
                        </button>
                      </form>
                      <form className="action-form" action={rejectImageAction.bind(null, id, image.id)}>
                        <h3>Отклонить изображение</h3>
                        <input name="moderator_name" placeholder="Имя редактора" defaultValue="Editor" />
                        <textarea name="notes" placeholder="Что в изображении не так" rows={3} />
                        <button className="action-button danger-button" type="submit">
                          Отклонить
                        </button>
                      </form>
                    </div>
                    <form className="action-form top-gap" action={regenerateImageAction.bind(null, id, image.id)}>
                      <h3>Перегенерировать</h3>
                      <input name="moderator_name" placeholder="Имя редактора" defaultValue="Editor" />
                      <textarea
                        name="notes"
                        placeholder="Как именно нужно изменить изображение при новой генерации"
                        rows={3}
                      />
                      <button className="action-button" type="submit">
                        Отправить на перегенерацию
                      </button>
                    </form>
                  </article>
                ))
              ) : (
                <p className="muted">Изображения ещё не созданы.</p>
              )}
            </div>
            <div className="top-gap">
              <p className="panel-label">Задача публикации</p>
              <p>{workspace.publishing_job?.status ? statusLabel(workspace.publishing_job.status) : "Задача публикации ещё не создавалась"}</p>
              <p className="muted">
                {workspace.article.published_url ?? `Пост в CMS: ${workspace.article.cms_post_id ?? "ещё не назначен"}`}
              </p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
