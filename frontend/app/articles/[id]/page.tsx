import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchApiJson } from "../../lib/api";
import { approveArticleAction, publishArticleAction, regenerateSectionAction, rejectArticleAction, runQualityCheckAction, submitForReviewAction } from "./actions";

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
    version: number;
    word_count: number;
    content_markdown: string;
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
  }>;
  images: Array<{
    id: string;
    alt_text: string;
    storage_url: string | null;
    local_path: string | null;
    is_featured: boolean;
  }>;
  latest_quality_report: {
    quality_score: number;
    risk_score: number;
    report_json: {
      overall_status?: string;
      blockers?: string[];
      warnings?: string[];
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

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Article Workspace</p>
          <h1>{workspace.article.title}</h1>
          <p className="hero-text">
            <Link href="/">Back to dashboard</Link>
            {" / "}
            {workspace.article.slug}
          </p>
        </div>
        <div className="hero-status">
          <div className={`badge ${tone(workspace.article.status)}`}>{workspace.article.status}</div>
          <div className="status-stack">
            <span>Current version</span>
            <strong>{workspace.current_version ? `v${workspace.current_version.version}` : "No version"}</strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Controls</p>
                <h2>Editorial actions</h2>
              </div>
            </div>
            <div className="action-grid">
              <form action={runQualityCheckAction.bind(null, id)}>
                <button className="action-button" type="submit">Run QA</button>
              </form>
              <form action={submitForReviewAction.bind(null, id)}>
                <button className="action-button" type="submit">Submit For Review</button>
              </form>
              <form action={publishArticleAction.bind(null, id)}>
                <button className="action-button accent-button" type="submit">Publish</button>
              </form>
            </div>
            <div className="action-columns">
              <form className="action-form" action={approveArticleAction.bind(null, id)}>
                <h3>Approve</h3>
                <input name="reviewer_name" placeholder="Reviewer name" defaultValue="Editor" />
                <textarea name="notes" placeholder="Approval notes" rows={4} />
                <button className="action-button" type="submit">Approve Article</button>
              </form>
              <form className="action-form" action={rejectArticleAction.bind(null, id)}>
                <h3>Reject</h3>
                <input name="reviewer_name" placeholder="Reviewer name" defaultValue="Editor" />
                <textarea name="notes" placeholder="Rejection notes" rows={4} />
                <button className="action-button danger-button" type="submit">Reject Article</button>
              </form>
            </div>
            <form className="action-form" action={regenerateSectionAction.bind(null, id)}>
              <h3>Regenerate Section</h3>
              <input name="section_heading" placeholder="FAQ" defaultValue="FAQ" />
              <textarea
                name="instructions"
                placeholder="Explain what should change in this section"
                rows={4}
              />
              <button className="action-button" type="submit">Create New Version</button>
            </form>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Current Draft</p>
                <h2>Markdown preview</h2>
              </div>
            </div>
            <div className="draft-meta">
              <span>{workspace.current_version ? `${workspace.current_version.word_count} words` : "No word count"}</span>
              <span>{workspace.current_version?.meta_title ?? "No meta title"}</span>
            </div>
            <pre className="markdown-preview">
              {workspace.current_version?.content_markdown ?? "No content available"}
            </pre>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">History</p>
                <h2>Versions and reviews</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.versions.map((version) => (
                <article className="queue-item" key={version.id}>
                  <div className="queue-header">
                    <strong>Version {version.version}</strong>
                    <div className="badge">{version.created_by}</div>
                  </div>
                  <p>{version.word_count} words</p>
                  <p className="muted">{new Date(version.created_at).toLocaleString()}</p>
                </article>
              ))}
            </div>
            <div className="stack top-gap">
              {workspace.editorial_reviews.map((review) => (
                <article className="queue-item" key={review.id}>
                  <div className="queue-header">
                    <strong>{review.reviewer_name}</strong>
                    <div className={`badge ${tone(review.decision)}`}>{review.decision}</div>
                  </div>
                  <p>{review.notes ?? "No notes"}</p>
                  <p className="muted">{new Date(review.created_at).toLocaleString()}</p>
                </article>
              ))}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Quality Gate</p>
            <h2>Latest report</h2>
            <div className="settings-list">
              <div>
                <dt>Quality score</dt>
                <dd>{workspace.latest_quality_report?.quality_score ?? "Not run"}</dd>
              </div>
              <div>
                <dt>Risk score</dt>
                <dd>{workspace.latest_quality_report?.risk_score ?? "Not run"}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{workspace.latest_quality_report?.report_json.overall_status ?? "Unknown"}</dd>
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Blockers</p>
              <div className="stack">
                {blockers.length ? blockers.map((item) => <div className="mini-chip danger-chip" key={item}>{item}</div>) : <p className="muted">No blockers</p>}
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Warnings</p>
              <div className="stack">
                {warnings.length ? warnings.map((item) => <div className="mini-chip warn-chip" key={item}>{item}</div>) : <p className="muted">No warnings</p>}
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Assets</p>
            <h2>Images and publishing</h2>
            <div className="stack">
              {workspace.images.map((image) => (
                <article className="topic-row" key={image.id}>
                  <strong>{image.is_featured ? "Featured image" : "Inline image"}</strong>
                  <span className="muted">{image.alt_text}</span>
                  <span className="muted">{image.storage_url ?? image.local_path ?? "No file path"}</span>
                </article>
              ))}
            </div>
            <div className="top-gap">
              <p className="panel-label">Publishing job</p>
              <p>{workspace.publishing_job?.status ?? "No publishing job yet"}</p>
              <p className="muted">
                {workspace.article.published_url ?? `CMS post ${workspace.article.cms_post_id ?? "not assigned"}`}
              </p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
