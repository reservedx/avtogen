import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchApiJson } from "../../lib/api";
import {
  addManualSourceAction,
  collectSourcesAction,
  extractResearchNotesAction,
  generateBriefAction,
  generateDraftAction,
} from "./actions";

type TopicWorkspace = {
  topic: {
    id: string;
    working_title: string;
    target_query: string;
    audience: string;
    status: string;
    cannibalization_hash: string | null;
  };
  sources: Array<{
    id: string;
    source_type: string;
    title: string;
    url: string;
    reliability_score: number | null;
    ingestion_status: string;
  }>;
  research_notes: Array<{
    id: string;
    fact_type: string;
    content: string;
    confidence_score: number;
    citation_data: { url?: string; title?: string } | null;
  }>;
  briefs: Array<{
    id: string;
    version: number;
    model_name: string;
    brief_json: {
      primary_keyword?: string;
      search_intent?: string;
      required_sections?: string[];
      faq_questions?: string[];
    };
    created_at: string;
  }>;
  articles: Array<{
    id: string;
    title: string;
    status: string;
    slug: string;
    quality_score: number | null;
    risk_score: number | null;
  }>;
};

type CannibalizationReport = {
  flagged: boolean;
  max_score: number;
  matches: Array<{
    entity_id: string | null;
    entity_type: string;
    title: string | null;
    slug: string | null;
    similarity_score: number;
    slug_overlap: boolean;
  }>;
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
    planned: "Запланировано",
    manual: "Ручной источник",
    youtube: "YouTube",
    ingested: "Загружено",
  };
  return labels[status] ?? status;
}

function noteTone(factType: string): string {
  if (factType === "red_flag") {
    return "danger";
  }
  if (factType === "guidance") {
    return "warn";
  }
  return "success";
}

function factTypeLabel(factType: string): string {
  const labels: Record<string, string> = {
    red_flag: "Красный флаг",
    guidance: "Рекомендация",
    fact: "Факт",
    symptom: "Симптом",
  };
  return labels[factType] ?? factType;
}

export default async function TopicWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [workspace, cannibalization] = await Promise.all([
    fetchApiJson<TopicWorkspace>(`/topics/${id}/workspace`),
    fetchApiJson<CannibalizationReport>(`/topics/${id}/cannibalization-check`),
  ]);

  if (!workspace) {
    notFound();
  }

  const latestBrief = workspace.briefs[0] ?? null;

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Рабочая область темы</p>
          <h1>{workspace.topic.working_title}</h1>
          <p className="hero-text">
            <Link href="/">Назад к дашборду</Link>
            {" / "}
            {workspace.topic.target_query}
          </p>
        </div>
        <div className="hero-status">
          <div className={`badge ${tone(workspace.topic.status)}`}>{statusLabel(workspace.topic.status)}</div>
          <div className="status-stack">
            <span>Исследовательское покрытие</span>
            <strong>
              {workspace.sources.length} источников / {workspace.research_notes.length} заметок
            </strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Управление темой</p>
                <h2>Путь от исследования к черновику</h2>
              </div>
            </div>
            <div className="action-grid">
              <form action={collectSourcesAction.bind(null, id)}>
                <button className="action-button" type="submit">
                  Собрать источники
                </button>
              </form>
              <form action={extractResearchNotesAction.bind(null, id)}>
                <button className="action-button" type="submit">
                  Обновить заметки
                </button>
              </form>
              <form action={generateBriefAction.bind(null, id)}>
                <button className="action-button" type="submit">
                  Сгенерировать ТЗ
                </button>
              </form>
            </div>
            <div className="top-gap">
              <form action={generateDraftAction.bind(null, id)}>
                <button className="action-button accent-button" type="submit">
                  Сгенерировать черновик статьи
                </button>
              </form>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Research Notes</p>
                <h2>Структурированные факты для brief и QA</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.research_notes.length ? (
                workspace.research_notes.map((note) => (
                  <article className="queue-item" key={note.id}>
                    <div className="queue-header">
                      <strong>{factTypeLabel(note.fact_type)}</strong>
                      <div className={`badge ${noteTone(note.fact_type)}`}>
                        {Math.round(note.confidence_score * 100)}%
                      </div>
                    </div>
                    <p>{note.content}</p>
                    <p className="muted">
                      {note.citation_data?.title ?? note.citation_data?.url ?? "Источник для заметки не указан"}
                    </p>
                  </article>
                ))
              ) : (
                <p className="muted">Исследовательские заметки пока не извлечены.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Источники</p>
                <h2>Материалы, на которых строится статья</h2>
              </div>
            </div>
            <form className="action-form topic-manual-source-form" action={addManualSourceAction.bind(null, id)}>
              <h3>Добавить источник вручную</h3>
              <input name="title" placeholder="Название статьи, гайда или документа" />
              <input name="url" placeholder="https://example.com/source" />
              <input name="author" placeholder="Автор или организация" />
              <input name="reliability_score" placeholder="0.8" defaultValue="0.8" />
              <textarea
                name="raw_content"
                placeholder="Вставь сюда краткое содержание источника, важный фрагмент или очищенные заметки."
                rows={5}
              />
              <button className="action-button" type="submit">
                Добавить источник
              </button>
            </form>
            <div className="stack">
              {workspace.sources.length ? (
                workspace.sources.map((source) => (
                  <article className="queue-item" key={source.id}>
                    <div className="queue-header">
                      <strong>{source.title}</strong>
                      <div className={`badge ${tone(source.ingestion_status)}`}>{statusLabel(source.source_type)}</div>
                    </div>
                    <p className="muted">{source.url}</p>
                    <p>Надёжность: {source.reliability_score ?? "неизвестно"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Источники пока не загружены.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Результаты</p>
                <h2>Статьи, связанные с этой темой</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.articles.length ? (
                workspace.articles.map((article) => (
                  <article className="queue-item" key={article.id}>
                    <div className="queue-header">
                      <strong>
                        <Link href={`/articles/${article.id}`}>{article.title}</Link>
                      </strong>
                      <div className={`badge ${tone(article.status)}`}>{statusLabel(article.status)}</div>
                    </div>
                    <p className="muted">{article.slug}</p>
                    <p>
                      Качество {article.quality_score ?? "n/a"} / Риск {article.risk_score ?? "n/a"}
                    </p>
                  </article>
                ))
              ) : (
                <p className="muted">С этой темой пока не связано ни одной статьи.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Снимок ТЗ</p>
            <h2>Последняя версия brief</h2>
            {latestBrief ? (
              <>
                <div className="settings-list">
                  <div>
                    <dt>Версия</dt>
                    <dd>{latestBrief.version}</dd>
                  </div>
                  <div>
                    <dt>Основной ключ</dt>
                    <dd>{latestBrief.brief_json.primary_keyword ?? workspace.topic.target_query}</dd>
                  </div>
                  <div>
                    <dt>Интент</dt>
                    <dd>{latestBrief.brief_json.search_intent ?? "informational"}</dd>
                  </div>
                  <div>
                    <dt>Модель</dt>
                    <dd>{latestBrief.model_name}</dd>
                  </div>
                </div>
                <div className="top-gap">
                  <p className="panel-label">Обязательные разделы</p>
                  <div className="stack">
                    {(latestBrief.brief_json.required_sections ?? []).map((section) => (
                      <div className="mini-chip" key={section}>
                        {section}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="muted">ТЗ для этой темы пока не создано.</p>
            )}
          </article>

          <article className="panel">
            <p className="panel-label">Контроль каннибализации</p>
            <h2>Похожесть на уже существующий контент</h2>
            <div className="settings-list">
              <div>
                <dt>Флаг</dt>
                <dd>{cannibalization?.flagged ? "Нужно ревью" : "Сильного конфликта не найдено"}</dd>
              </div>
              <div>
                <dt>Максимальный score</dt>
                <dd>{cannibalization?.max_score ?? 0}</dd>
              </div>
              <div>
                <dt>Хэш темы</dt>
                <dd>{workspace.topic.cannibalization_hash ?? "Не рассчитан"}</dd>
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Ближайшие совпадения</p>
              <div className="stack">
                {cannibalization?.matches.length ? (
                  cannibalization.matches.map((match) => (
                    <article className="queue-item" key={`${match.entity_type}-${match.entity_id}`}>
                      <div className="queue-header">
                        <strong>{match.title ?? "Без названия"}</strong>
                        <div className={`badge ${match.slug_overlap ? "danger" : "warn"}`}>{match.similarity_score}</div>
                      </div>
                      <p className="muted">{match.entity_type}</p>
                      <p className="muted">{match.slug ?? "Slug отсутствует"}</p>
                    </article>
                  ))
                ) : (
                  <p className="muted">Похожие темы или опубликованные статьи не найдены.</p>
                )}
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
