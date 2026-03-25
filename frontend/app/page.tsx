import Link from "next/link";

import {
  bulkApproveAction,
  bulkPublishAction,
  bulkSubmitForReviewAction,
  createDemoProjectAction,
  runBulkQualityCheckAction,
} from "./actions";
import { getDashboardData } from "./lib/dashboard";

function statusTone(status: string): string {
  if (status === "published" || status === "completed" || status === "approved") {
    return "success";
  }
  if (status === "needs_revision" || status === "failed") {
    return "danger";
  }
  return "warn";
}

function scoreLabel(value: number | null, kind: "quality" | "risk"): string {
  if (value === null) {
    return kind === "quality" ? "No QA yet" : "Risk unknown";
  }
  return `${kind === "quality" ? "Quality" : "Risk"} ${value}/100`;
}

export default async function HomePage() {
  const data = await getDashboardData();
  const reviewQueue = data.articles.filter((article) => article.status !== "published").slice(0, 4);
  const published = data.articles.filter((article) => article.status === "published").slice(0, 3);
  const failedJobs = data.taskRuns.filter((task) => task.status === "failed").slice(0, 4);
  const leadArticle = reviewQueue[0] ?? data.articles[0];
  const reviewQueueIds = reviewQueue.map((article) => article.id);
  const approvedArticleIds = data.articles.filter((article) => article.status === "approved").map((article) => article.id);

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Editorial Control Center</p>
          <h1>Review-first publishing for sensitive women&apos;s health content.</h1>
          <p className="hero-text">
            The admin surfaces risky drafts, quality signals, storage mode, and publishing readiness in one place.
            It is designed for YMYL workflows where draft quality and human review matter more than raw output volume.
          </p>
          <form action={createDemoProjectAction} className="hero-action">
            <button className="action-button accent-button hero-button" type="submit">Create Demo Project</button>
          </form>
        </div>
        <div className="hero-status">
          <div className={`badge ${data.apiOnline ? "success" : "warn"}`}>
            {data.apiOnline ? "API online" : "Fallback preview"}
          </div>
          <div className="status-stack">
            <span>{data.settings.app_name}</span>
            <strong>{data.settings.app_env}</strong>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <article className="metric-card accent">
          <span>Topics in queue</span>
          <strong>{data.metrics.topics_count}</strong>
        </article>
        <article className="metric-card">
          <span>Articles tracked</span>
          <strong>{data.metrics.articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Published</span>
          <strong>{data.metrics.published_articles_count}</strong>
        </article>
        <article className="metric-card">
          <span>Task runs</span>
          <strong>{data.metrics.task_runs_count}</strong>
        </article>
      </section>

      <section className="metrics-grid">
        <article className="metric-card">
          <span>Avg quality</span>
          <strong>{data.analytics.average_quality_score ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Avg risk</span>
          <strong>{data.analytics.average_risk_score ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Main source mix</span>
          <strong>{data.analytics.source_type_counts[0]?.key ?? "n/a"}</strong>
        </article>
        <article className="metric-card">
          <span>Top failed task</span>
          <strong>{data.analytics.failed_task_counts[0]?.key ?? "none"}</strong>
        </article>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel spotlight">
            <div className="panel-head">
              <div>
                <p className="panel-label">Lead Article</p>
                <h2>{leadArticle?.title ?? "No articles yet"}</h2>
              </div>
              {leadArticle ? <div className={`badge ${statusTone(leadArticle.status)}`}>{leadArticle.status}</div> : null}
            </div>
            {leadArticle ? (
              <div className="spotlight-grid">
                <div className="story-card">
                  <span className="kicker">Readiness</span>
                  <p>{scoreLabel(leadArticle.quality_score, "quality")}</p>
                  <p>{scoreLabel(leadArticle.risk_score, "risk")}</p>
                  <p className="muted">
                    {data.leadWorkspace?.current_version
                      ? `Version ${data.leadWorkspace.current_version.version}, ${data.leadWorkspace.current_version.word_count} words`
                      : "No version metadata yet"}
                  </p>
                  <p className="muted">Slug: {leadArticle.slug}</p>
                </div>
                <div className="story-card">
                  <span className="kicker">Publishing</span>
                  <p>{leadArticle.cms_post_id ? `Remote post #${leadArticle.cms_post_id}` : "Not synced to CMS"}</p>
                  <p className="muted">
                    {data.leadWorkspace
                      ? `${data.leadWorkspace.images.length} images, ${data.leadWorkspace.editorial_reviews.length} reviews, job ${data.leadWorkspace.publishing_job?.status ?? "pending"}`
                      : "Workspace details unavailable"}
                  </p>
                  <p className="muted">
                    {leadArticle.published_url ? leadArticle.published_url : "Waiting for approval and publish step."}
                  </p>
                </div>
              </div>
            ) : (
              <p className="muted">Create a topic in the API or use the demo button above to populate the queue.</p>
            )}
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Review Queue</p>
                <h2>Articles needing editor attention</h2>
              </div>
            </div>
            <div className="action-columns top-gap">
              <form action={runBulkQualityCheckAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">Run QA On Queue</button>
              </form>
              <form action={bulkSubmitForReviewAction.bind(null, reviewQueueIds)}>
                <button className="action-button accent-button" type="submit">Submit Queue For Review</button>
              </form>
            </div>
            <div className="action-columns top-gap">
              <form action={bulkApproveAction.bind(null, reviewQueueIds)}>
                <button className="action-button" type="submit">Approve Queue</button>
              </form>
              <form action={bulkPublishAction.bind(null, approvedArticleIds)}>
                <button className="action-button accent-button" type="submit">Publish Approved</button>
              </form>
            </div>
            <div className="stack">
              {reviewQueue.map((article) => (
                <article className="queue-item" key={article.id}>
                  <div className="queue-header">
                    <strong>
                      <Link href={`/articles/${article.id}`}>{article.title}</Link>
                    </strong>
                    <div className={`badge ${statusTone(article.status)}`}>{article.status}</div>
                  </div>
                  <p>{scoreLabel(article.quality_score, "quality")}</p>
                  <p>{scoreLabel(article.risk_score, "risk")}</p>
                  <span className="muted">{article.slug}</span>
                </article>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Published</p>
                <h2>Recently published or CMS-linked</h2>
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
                      <p className="muted">{article.published_url ?? "Published without URL"}</p>
                    </div>
                    <div className="published-meta">
                      <span>{article.cms_post_id ? `WP #${article.cms_post_id}` : "Awaiting sync"}</span>
                    </div>
                  </article>
                ))
              ) : (
                <p className="muted">Published articles will appear here after WordPress sync.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel settings-panel">
            <p className="panel-label">Runtime Settings</p>
            <h2>Environment snapshot</h2>
            <dl className="settings-list">
              <div>
                <dt>Storage backend</dt>
                <dd>{data.settings.asset_storage_backend}</dd>
              </div>
              <div>
                <dt>Assets path</dt>
                <dd>{data.settings.asset_storage_dir}</dd>
              </div>
              <div>
                <dt>S3 bucket</dt>
                <dd>{data.settings.s3_bucket}</dd>
              </div>
              <div>
                <dt>OpenAI mode</dt>
                <dd>{data.settings.openai_enabled ? "Live" : "Stub / disabled"}</dd>
              </div>
              <div>
                <dt>Auto publish</dt>
                <dd>{data.settings.auto_publish_enabled ? "Enabled" : "Review first"}</dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd>{data.settings.database_is_sqlite ? "SQLite dev mode" : "External database"}</dd>
              </div>
            </dl>
          </article>

          <article className="panel">
            <p className="panel-label">Task Watch</p>
            <h2>Failed or risky runs</h2>
            <div className="stack">
              {failedJobs.length ? (
                failedJobs.map((task) => (
                  <article className="task-row" key={task.id}>
                    <div className="queue-header">
                      <strong>{task.task_type}</strong>
                      <div className={`badge ${statusTone(task.status)}`}>{task.status}</div>
                    </div>
                    <p className="muted">{task.error_message ?? "No error text"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">No failed jobs right now.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Analytics</p>
            <h2>Status and source mix</h2>
            <div className="stack">
              {data.analytics.article_status_counts.map((item) => (
                <article className="task-row" key={item.key}>
                  <div className="queue-header">
                    <strong>{item.key}</strong>
                    <div className="badge">{item.count}</div>
                  </div>
                </article>
              ))}
              {data.analytics.source_type_counts.map((item) => (
                <article className="task-row" key={`source-${item.key}`}>
                  <div className="queue-header">
                    <strong>{item.key} sources</strong>
                    <div className="badge">{item.count}</div>
                  </div>
                </article>
              ))}
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Topic Intake</p>
            <h2>Cluster-ready topics</h2>
            <div className="stack">
              {data.topics.slice(0, 4).map((topic) => (
                <article className="topic-row" key={topic.id}>
                  <strong>
                    <Link href={`/topics/${topic.id}`}>{topic.working_title}</Link>
                  </strong>
                  <span className="muted">{topic.target_query}</span>
                  <div className={`badge ${statusTone(topic.status)}`}>{topic.status}</div>
                </article>
              ))}
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
