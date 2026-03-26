import { fetchApiJson } from "../lib/api";

type SettingsSummary = {
  app_name: string;
  app_env: string;
  api_prefix: string;
  database_url: string;
  database_is_sqlite: boolean;
  asset_storage_backend: string;
  asset_storage_dir: string;
  s3_bucket: string;
  openai_enabled: boolean;
  auto_publish_enabled: boolean;
  fast_publish_enabled: boolean;
  auto_approve_low_risk: boolean;
  auto_publish_low_risk: boolean;
  use_stub_generation: boolean;
  openai_brief_model: string;
  openai_draft_model: string;
  openai_image_model: string;
  min_quality_score: number;
  max_risk_score_for_auto_publish: number;
  fast_lane_min_quality_score: number;
  fast_lane_max_risk_score: number;
  required_source_count: number;
  similarity_threshold: number;
  default_medical_disclaimer: string;
  runtime_override_keys: string[];
};

type Metrics = {
  clusters_count: number;
  topics_count: number;
  articles_count: number;
  published_articles_count: number;
  quality_reports_count: number;
  task_runs_count: number;
};

type ReadinessItem = {
  code: string;
  label: string;
  status: string;
  detail: string;
};

type Readiness = {
  overall_status: string;
  summary: string;
  items: ReadinessItem[];
};

type AuthSession = {
  role: string;
  auth_enabled: boolean;
  allowed_capabilities: string[];
};

type SystemOverview = {
  settings: SettingsSummary;
  metrics: Metrics;
  readiness: Readiness;
  session: AuthSession;
};

function boolText(value: boolean): string {
  return value ? "Да" : "Нет";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    ready: "Готово",
    warning: "Внимание",
    failed: "Ошибка",
    pending: "Ожидание",
  };
  return labels[status] ?? status;
}

function statusTone(status: string): string {
  if (status === "ready") {
    return "success";
  }
  if (status === "failed") {
    return "danger";
  }
  return "warn";
}

export default async function SystemPage() {
  const overview = await fetchApiJson<SystemOverview>("/system/overview");

  if (!overview) {
    return (
      <main className="page-shell">
        <section className="hero compact">
          <div className="hero-copy">
            <p className="eyebrow">Система</p>
            <h1>Системный экран недоступен</h1>
            <p className="hero-text">Backend не ответил на агрегированный запрос состояния платформы.</p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Система</p>
          <h1>Обзор состояния платформы</h1>
          <p className="hero-text">
            Единый экран для проверки режима запуска, readiness, текущей роли доступа и базовых метрик
            платформы без переходов между несколькими разделами.
          </p>
        </div>
        <div className="hero-status">
          <div className={`badge ${statusTone(overview.readiness.overall_status)}`}>
            {statusLabel(overview.readiness.overall_status)}
          </div>
          <div className="status-stack">
            <span>Runtime overrides</span>
            <strong>{overview.settings.runtime_override_keys.length}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Тем в системе</span>
          <strong>{overview.metrics.topics_count}</strong>
        </article>
        <article className="metric-card">
          <span>Статей</span>
          <strong>{overview.metrics.articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Опубликовано</span>
          <strong>{overview.metrics.published_articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Task runs</span>
          <strong>{overview.metrics.task_runs_count}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Readiness</p>
                <h2>Готовность к запуску</h2>
              </div>
            </div>
            <p className="muted">{overview.readiness.summary}</p>
            <div className="stack top-gap">
              {overview.readiness.items.map((item) => (
                <article className="queue-item" key={item.code}>
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
            <div className="panel-head">
              <div>
                <p className="panel-label">Runtime</p>
                <h2>Ключевые режимы платформы</h2>
              </div>
            </div>
            <div className="settings-list">
              <div>
                <dt>APP_ENV</dt>
                <dd>{overview.settings.app_env}</dd>
              </div>
              <div>
                <dt>API prefix</dt>
                <dd>{overview.settings.api_prefix}</dd>
              </div>
              <div>
                <dt>OpenAI active</dt>
                <dd>{boolText(overview.settings.openai_enabled)}</dd>
              </div>
              <div>
                <dt>Fast publish</dt>
                <dd>{boolText(overview.settings.fast_publish_enabled)}</dd>
              </div>
              <div>
                <dt>Auto approve low risk</dt>
                <dd>{boolText(overview.settings.auto_approve_low_risk)}</dd>
              </div>
              <div>
                <dt>Auto publish</dt>
                <dd>{boolText(overview.settings.auto_publish_enabled)}</dd>
              </div>
              <div>
                <dt>Stub generation</dt>
                <dd>{boolText(overview.settings.use_stub_generation)}</dd>
              </div>
              <div>
                <dt>Storage backend</dt>
                <dd>{overview.settings.asset_storage_backend}</dd>
              </div>
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Доступ</p>
            <h2>Текущая роль</h2>
            <div className="settings-list">
              <div>
                <dt>Auth enabled</dt>
                <dd>{boolText(overview.session.auth_enabled)}</dd>
              </div>
              <div>
                <dt>Role</dt>
                <dd>{overview.session.role}</dd>
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Capabilities</p>
              <div className="stack">
                {overview.session.allowed_capabilities.map((item) => (
                  <div className="mini-chip" key={item}>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Инфраструктура</p>
            <h2>Хранилище и база</h2>
            <div className="settings-list">
              <div>
                <dt>Database</dt>
                <dd>{overview.settings.database_is_sqlite ? "SQLite" : overview.settings.database_url}</dd>
              </div>
              <div>
                <dt>Assets path</dt>
                <dd>{overview.settings.asset_storage_dir}</dd>
              </div>
              <div>
                <dt>S3 bucket</dt>
                <dd>{overview.settings.s3_bucket}</dd>
              </div>
              <div>
                <dt>Brief model</dt>
                <dd>{overview.settings.openai_brief_model}</dd>
              </div>
              <div>
                <dt>Draft model</dt>
                <dd>{overview.settings.openai_draft_model}</dd>
              </div>
              <div>
                <dt>Image model</dt>
                <dd>{overview.settings.openai_image_model}</dd>
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Политика качества</p>
            <h2>Пороговые значения</h2>
            <div className="settings-list">
              <div>
                <dt>Min quality</dt>
                <dd>{overview.settings.min_quality_score}</dd>
              </div>
              <div>
                <dt>Max risk</dt>
                <dd>{overview.settings.max_risk_score_for_auto_publish}</dd>
              </div>
              <div>
                <dt>Fast lane min quality</dt>
                <dd>{overview.settings.fast_lane_min_quality_score}</dd>
              </div>
              <div>
                <dt>Fast lane max risk</dt>
                <dd>{overview.settings.fast_lane_max_risk_score}</dd>
              </div>
              <div>
                <dt>Required sources</dt>
                <dd>{overview.settings.required_source_count}</dd>
              </div>
              <div>
                <dt>Similarity threshold</dt>
                <dd>{overview.settings.similarity_threshold}</dd>
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
