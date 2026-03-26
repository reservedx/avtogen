import Link from "next/link";

import { fetchApiJson } from "../lib/api";

type TaskRun = {
  id: string;
  task_type: string;
  entity_type: string;
  entity_id: string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
};

function statusTone(status: string): string {
  if (status === "completed") {
    return "success";
  }
  if (status === "failed") {
    return "danger";
  }
  return "warn";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    completed: "Выполнено",
    failed: "Ошибка",
    running: "В работе",
    pending: "В ожидании",
  };
  return labels[status] ?? status;
}

function taskTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    article_pipeline: "Генерация статьи",
    publish_article: "Публикация",
    collect_sources: "Сбор источников",
    quality_check: "Quality check",
  };
  return labels[value] ?? value;
}

function applyFilters(tasks: TaskRun[], status: string, taskType: string, query: string): TaskRun[] {
  const normalizedQuery = query.trim().toLowerCase();
  return tasks.filter((task) => {
    const statusMatch = status === "all" || task.status === status;
    const typeMatch = taskType === "all" || task.task_type === taskType;
    const queryMatch =
      !normalizedQuery ||
      task.task_type.toLowerCase().includes(normalizedQuery) ||
      task.entity_type.toLowerCase().includes(normalizedQuery) ||
      task.entity_id.toLowerCase().includes(normalizedQuery) ||
      (task.error_message ?? "").toLowerCase().includes(normalizedQuery);
    return statusMatch && typeMatch && queryMatch;
  });
}

export default async function JobsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = (await searchParams) ?? {};
  const currentStatus = typeof params.status === "string" ? params.status : "all";
  const currentType = typeof params.type === "string" ? params.type : "all";
  const currentQuery = typeof params.q === "string" ? params.q : "";

  const tasks = (await fetchApiJson<TaskRun[]>("/task-runs")) ?? [];
  const filteredTasks = applyFilters(tasks, currentStatus, currentType, currentQuery);
  const failedTasks = filteredTasks.filter((task) => task.status === "failed");
  const runningTasks = filteredTasks.filter((task) => task.status === "running");
  const uniqueTaskTypes = Array.from(new Set(tasks.map((task) => task.task_type))).sort();

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Pipeline Jobs</p>
          <h1>Мониторинг задач</h1>
          <p className="hero-text">
            Здесь видно, как работает конвейер по шагам: какие задачи проходят успешно, какие зависают и где чаще всего случаются ошибки.
            Этот экран нужен для операционного контроля над pipeline, а не только над контентом.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge success">Task orchestration</div>
          <div className="status-stack">
            <span>Найдено по фильтру</span>
            <strong>{filteredTasks.length}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Все задачи</span>
          <strong>{filteredTasks.length}</strong>
        </article>
        <article className="metric-card">
          <span>Успешные</span>
          <strong>{filteredTasks.filter((task) => task.status === "completed").length}</strong>
        </article>
        <article className="metric-card">
          <span>В работе</span>
          <strong>{runningTasks.length}</strong>
        </article>
        <article className="metric-card">
          <span>Ошибки</span>
          <strong>{failedTasks.length}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Глобальные фильтры</p>
                <h2>Поиск по task runs</h2>
              </div>
            </div>
            <form action="/jobs" className="filter-bar" method="get">
              <input defaultValue={currentQuery} name="q" placeholder="Поиск по task type, entity или ошибке" />
              <select defaultValue={currentStatus} name="status">
                <option value="all">Все статусы</option>
                <option value="completed">Выполнено</option>
                <option value="running">В работе</option>
                <option value="failed">Ошибка</option>
                <option value="pending">В ожидании</option>
              </select>
              <select defaultValue={currentType} name="type">
                <option value="all">Все типы задач</option>
                {uniqueTaskTypes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
              <button className="action-button" type="submit">
                Применить
              </button>
            </form>
            <div className="filter-pills">
              <Link className="mini-chip" href="/jobs">
                Сбросить фильтры
              </Link>
              <div className="mini-chip">Статус: {currentStatus === "all" ? "все" : statusLabel(currentStatus)}</div>
              <div className="mini-chip">Тип: {currentType === "all" ? "все" : currentType}</div>
              <div className="mini-chip">Запрос: {currentQuery || "без поиска"}</div>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Лента задач</p>
                <h2>Последние task runs</h2>
              </div>
            </div>
            <div className="stack">
              {filteredTasks.length ? (
                filteredTasks.map((task) => (
                  <article className="queue-item" key={task.id}>
                    <div className="queue-header">
                      <strong>{taskTypeLabel(task.task_type)}</strong>
                      <div className={`badge ${statusTone(task.status)}`}>{statusLabel(task.status)}</div>
                    </div>
                    <p className="muted">
                      {task.task_type} • {task.entity_type} • {task.entity_id}
                    </p>
                    <p className="muted">
                      Старт: {new Date(task.started_at).toLocaleString("ru-RU")}
                      {task.finished_at ? ` • Финиш: ${new Date(task.finished_at).toLocaleString("ru-RU")}` : ""}
                    </p>
                    <p className="muted">{task.error_message ?? "Задача завершилась без ошибки."}</p>
                  </article>
                ))
              ) : (
                <p className="muted">По текущему фильтру задачи не найдены.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Проблемные задачи</p>
            <h2>Что требует внимания</h2>
            <div className="stack">
              {failedTasks.length ? (
                failedTasks.slice(0, 8).map((task) => (
                  <article className="queue-item" key={task.id}>
                    <div className="queue-header">
                      <strong>{taskTypeLabel(task.task_type)}</strong>
                      <div className="badge danger">Ошибка</div>
                    </div>
                    <p className="muted">{task.error_message ?? "Текст ошибки отсутствует"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Сейчас проблемных задач по выбранному фильтру нет.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Навигация</p>
            <h2>Связанные разделы</h2>
            <div className="stack">
              <article className="topic-row">
                <strong>
                  <Link href="/analytics">Открыть аналитику</Link>
                </strong>
                <span className="muted">Сводка по статусам, источникам и средним показателям</span>
              </article>
              <article className="topic-row">
                <strong>
                  <Link href="/">Вернуться на dashboard</Link>
                </strong>
                <span className="muted">Очереди контента, fast lane и bulk-операции</span>
              </article>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
