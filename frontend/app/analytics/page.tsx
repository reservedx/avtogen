import { fetchApiJson } from "../lib/api";

type CountBucket = {
  key: string;
  count: number;
};

type AnalyticsSummary = {
  article_status_counts: CountBucket[];
  source_type_counts: CountBucket[];
  failed_task_counts: CountBucket[];
  average_quality_score: number | null;
  average_risk_score: number | null;
};

type Metrics = {
  clusters_count: number;
  topics_count: number;
  articles_count: number;
  published_articles_count: number;
  quality_reports_count: number;
  task_runs_count: number;
};

type TaskRun = {
  id: string;
  task_type: string;
  entity_type: string;
  status: string;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "Черновик",
    in_review: "На ревью",
    approved: "Одобрено",
    published: "Опубликовано",
    rejected: "Отклонено",
    needs_revision: "Нужна доработка",
    failed: "Ошибка",
    completed: "Выполнено",
  };
  return labels[status] ?? status;
}

export default async function AnalyticsPage() {
  const [analytics, metrics, taskRuns] = await Promise.all([
    fetchApiJson<AnalyticsSummary>("/analytics/summary"),
    fetchApiJson<Metrics>("/metrics"),
    fetchApiJson<TaskRun[]>("/task-runs"),
  ]);

  const latestFailures = (taskRuns ?? []).filter((task) => task.status === "failed").slice(0, 8);

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Analytics</p>
          <h1>Операционная аналитика</h1>
          <p className="hero-text">
            Этот экран показывает реальную картину по системе: сколько тем и статей в работе, как распределяются статусы,
            какие источники доминируют и где чаще всего ломается pipeline.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge success">System overview</div>
          <div className="status-stack">
            <span>Последних task runs</span>
            <strong>{metrics?.task_runs_count ?? 0}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Тем</span>
          <strong>{metrics?.topics_count ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Статей</span>
          <strong>{metrics?.articles_count ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Опубликовано</span>
          <strong>{metrics?.published_articles_count ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Среднее качество</span>
          <strong>{analytics?.average_quality_score ?? "n/a"}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Статусы статей</p>
                <h2>Где сейчас находится контент</h2>
              </div>
            </div>
            <div className="stack">
              {(analytics?.article_status_counts ?? []).length ? (
                analytics?.article_status_counts.map((item) => (
                  <article className="queue-item" key={item.key}>
                    <div className="queue-header">
                      <strong>{statusLabel(item.key)}</strong>
                      <div className="badge">{item.count}</div>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted">Статистика по статусам пока недоступна.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Источники</p>
                <h2>Состав research pipeline</h2>
              </div>
            </div>
            <div className="stack">
              {(analytics?.source_type_counts ?? []).length ? (
                analytics?.source_type_counts.map((item) => (
                  <article className="queue-item" key={item.key}>
                    <div className="queue-header">
                      <strong>{item.key}</strong>
                      <div className="badge">{item.count}</div>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted">Статистика по источникам пока недоступна.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Упавшие шаги</p>
                <h2>Где pipeline теряет устойчивость</h2>
              </div>
            </div>
            <div className="stack">
              {(analytics?.failed_task_counts ?? []).length ? (
                analytics?.failed_task_counts.map((item) => (
                  <article className="queue-item" key={item.key}>
                    <div className="queue-header">
                      <strong>{item.key}</strong>
                      <div className="badge danger">{item.count}</div>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted">Сейчас нет падений по task types.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Риск-профиль</p>
            <h2>Средние значения</h2>
            <div className="settings-list">
              <div>
                <dt>Average quality</dt>
                <dd>{analytics?.average_quality_score ?? "n/a"}</dd>
              </div>
              <div>
                <dt>Average risk</dt>
                <dd>{analytics?.average_risk_score ?? "n/a"}</dd>
              </div>
              <div>
                <dt>Quality reports</dt>
                <dd>{metrics?.quality_reports_count ?? "n/a"}</dd>
              </div>
              <div>
                <dt>Clusters</dt>
                <dd>{metrics?.clusters_count ?? "n/a"}</dd>
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Последние ошибки</p>
            <h2>Task runs с проблемами</h2>
            <div className="stack">
              {latestFailures.length ? (
                latestFailures.map((task) => (
                  <article className="queue-item" key={task.id}>
                    <div className="queue-header">
                      <strong>{task.task_type}</strong>
                      <div className="badge danger">failed</div>
                    </div>
                    <p className="muted">{task.error_message ?? "Текст ошибки отсутствует"}</p>
                    <p className="muted">{new Date(task.started_at).toLocaleString("ru-RU")}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Свежих падений нет.</p>
              )}
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
