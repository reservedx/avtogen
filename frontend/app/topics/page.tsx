import Link from "next/link";

import { bulkCreateTopicsAction, runBulkFastLaneTopicsAction } from "../actions";
import { fetchApiJson } from "../lib/api";

type Topic = {
  id: string;
  working_title: string;
  audience: string;
  status: string;
  target_query: string;
};

function statusTone(status: string): string {
  if (status === "published" || status === "approved" || status === "completed") {
    return "success";
  }
  if (status === "needs_revision" || status === "failed" || status === "rejected") {
    return "danger";
  }
  return "warn";
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    planned: "Запланировано",
    draft: "Черновик",
    in_review: "На ревью",
    approved: "Одобрено",
    published: "Опубликовано",
    needs_revision: "Нужна доработка",
  };
  return labels[status] ?? status;
}

export default async function TopicsPage() {
  const topics = (await fetchApiJson<Topic[]>("/topics")) ?? [];
  const topicQueueIds = topics.filter((topic) => topic.status !== "published").slice(0, 40).map((topic) => topic.id);
  const plannedCount = topics.filter((topic) => topic.status === "planned").length;
  const activeCount = topics.filter((topic) => ["draft", "in_review", "approved", "needs_revision"].includes(topic.status)).length;
  const publishedCount = topics.filter((topic) => topic.status === "published").length;

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Topic Ops</p>
          <h1>Темы и research</h1>
          <p className="hero-text">
            Здесь начинается поток контента: импортируешь пачку тем, запускаешь fast lane, затем переходишь в конкретную тему,
            чтобы смотреть источники, research notes, brief и связанные статьи.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge success">Cluster workflow</div>
          <div className="status-stack">
            <span>Всего тем</span>
            <strong>{topics.length}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Запланировано</span>
          <strong>{plannedCount}</strong>
        </article>
        <article className="metric-card">
          <span>В работе</span>
          <strong>{activeCount}</strong>
        </article>
        <article className="metric-card">
          <span>Опубликовано</span>
          <strong>{publishedCount}</strong>
        </article>
        <article className="metric-card">
          <span>Готово для fast lane</span>
          <strong>{topicQueueIds.length}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Массовый запуск</p>
                <h2>Импорт тем и fast lane</h2>
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
            <div className="top-gap">
              <form action={runBulkFastLaneTopicsAction.bind(null, topicQueueIds)}>
                <button className="action-button accent-button" type="submit">
                  Запустить fast lane по видимой очереди
                </button>
              </form>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Список тем</p>
                <h2>Текущий контентный backlog</h2>
              </div>
            </div>
            <div className="stack">
              {topics.length ? (
                topics.map((topic) => (
                  <article className="queue-item" key={topic.id}>
                    <div className="queue-header">
                      <strong>
                        <Link href={`/topics/${topic.id}`}>{topic.working_title}</Link>
                      </strong>
                      <div className={`badge ${statusTone(topic.status)}`}>{statusLabel(topic.status)}</div>
                    </div>
                    <p className="muted">{topic.target_query}</p>
                    <p className="muted">Аудитория: {topic.audience}</p>
                  </article>
                ))
              ) : (
                <p className="muted">Темы пока не загружены. Начни с импорта списка выше.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Как работать</p>
            <h2>Поток по темам</h2>
            <div className="stack">
              <div className="mini-chip">Сначала загрузи список тем по кластерам.</div>
              <div className="mini-chip">Потом прогони их через fast lane, чтобы быстро собрать research и draft.</div>
              <div className="mini-chip">Если тема важная или спорная, открой её карточку и доработай вручную.</div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Связанные разделы</p>
            <h2>Операционные экраны</h2>
            <div className="stack">
              <article className="topic-row">
                <strong>
                  <Link href="/articles">Очередь статей</Link>
                </strong>
                <span className="muted">QA, review, approval и publish</span>
              </article>
              <article className="topic-row">
                <strong>
                  <Link href="/images">Модерация изображений</Link>
                </strong>
                <span className="muted">Ручная визуальная проверка перед CMS</span>
              </article>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
