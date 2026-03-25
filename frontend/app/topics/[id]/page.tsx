import Link from "next/link";
import { notFound } from "next/navigation";

import { fetchApiJson } from "../../lib/api";
import {
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

function noteTone(factType: string): string {
  if (factType === "red_flag") {
    return "danger";
  }
  if (factType === "guidance") {
    return "warn";
  }
  return "success";
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
          <p className="eyebrow">Topic Workspace</p>
          <h1>{workspace.topic.working_title}</h1>
          <p className="hero-text">
            <Link href="/">Back to dashboard</Link>
            {" / "}
            {workspace.topic.target_query}
          </p>
        </div>
        <div className="hero-status">
          <div className={`badge ${tone(workspace.topic.status)}`}>{workspace.topic.status}</div>
          <div className="status-stack">
            <span>Research coverage</span>
            <strong>{workspace.sources.length} sources / {workspace.research_notes.length} notes</strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Topic Controls</p>
                <h2>Move from research to draft</h2>
              </div>
            </div>
            <div className="action-grid">
              <form action={collectSourcesAction.bind(null, id)}>
                <button className="action-button" type="submit">Collect Sources</button>
              </form>
              <form action={extractResearchNotesAction.bind(null, id)}>
                <button className="action-button" type="submit">Refresh Notes</button>
              </form>
              <form action={generateBriefAction.bind(null, id)}>
                <button className="action-button" type="submit">Generate Brief</button>
              </form>
            </div>
            <div className="top-gap">
              <form action={generateDraftAction.bind(null, id)}>
                <button className="action-button accent-button" type="submit">Generate Draft Article</button>
              </form>
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Research Notes</p>
                <h2>Structured facts for brief and QA</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.research_notes.length ? (
                workspace.research_notes.map((note) => (
                  <article className="queue-item" key={note.id}>
                    <div className="queue-header">
                      <strong>{note.fact_type}</strong>
                      <div className={`badge ${noteTone(note.fact_type)}`}>{Math.round(note.confidence_score * 100)}%</div>
                    </div>
                    <p>{note.content}</p>
                    <p className="muted">{note.citation_data?.title ?? note.citation_data?.url ?? "No citation metadata"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">No research notes extracted yet.</p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Sources</p>
                <h2>Ingested references</h2>
              </div>
            </div>
            <div className="stack">
              {workspace.sources.map((source) => (
                <article className="queue-item" key={source.id}>
                  <div className="queue-header">
                    <strong>{source.title}</strong>
                    <div className={`badge ${tone(source.ingestion_status)}`}>{source.source_type}</div>
                  </div>
                  <p className="muted">{source.url}</p>
                  <p>Reliability: {source.reliability_score ?? "unknown"}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Article Outputs</p>
                <h2>Drafts linked to this topic</h2>
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
                      <div className={`badge ${tone(article.status)}`}>{article.status}</div>
                    </div>
                    <p className="muted">{article.slug}</p>
                    <p>Quality {article.quality_score ?? "n/a"} / Risk {article.risk_score ?? "n/a"}</p>
                  </article>
                ))
              ) : (
                <p className="muted">No article drafts linked yet.</p>
              )}
            </div>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Brief Snapshot</p>
            <h2>Latest article brief</h2>
            {latestBrief ? (
              <>
                <div className="settings-list">
                  <div>
                    <dt>Version</dt>
                    <dd>{latestBrief.version}</dd>
                  </div>
                  <div>
                    <dt>Primary keyword</dt>
                    <dd>{latestBrief.brief_json.primary_keyword ?? workspace.topic.target_query}</dd>
                  </div>
                  <div>
                    <dt>Search intent</dt>
                    <dd>{latestBrief.brief_json.search_intent ?? "informational"}</dd>
                  </div>
                  <div>
                    <dt>Model</dt>
                    <dd>{latestBrief.model_name}</dd>
                  </div>
                </div>
                <div className="top-gap">
                  <p className="panel-label">Required sections</p>
                  <div className="stack">
                    {(latestBrief.brief_json.required_sections ?? []).map((section) => (
                      <div className="mini-chip" key={section}>{section}</div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="muted">No brief generated yet.</p>
            )}
          </article>

          <article className="panel">
            <p className="panel-label">Cannibalization Watch</p>
            <h2>Similarity to existing content</h2>
            <div className="settings-list">
              <div>
                <dt>Flagged</dt>
                <dd>{cannibalization?.flagged ? "Review needed" : "No strong conflict"}</dd>
              </div>
              <div>
                <dt>Max score</dt>
                <dd>{cannibalization?.max_score ?? 0}</dd>
              </div>
              <div>
                <dt>Topic hash</dt>
                <dd>{workspace.topic.cannibalization_hash ?? "Not calculated"}</dd>
              </div>
            </div>
            <div className="top-gap">
              <p className="panel-label">Closest matches</p>
              <div className="stack">
                {cannibalization?.matches.length ? (
                  cannibalization.matches.map((match) => (
                    <article className="queue-item" key={`${match.entity_type}-${match.entity_id}`}>
                      <div className="queue-header">
                        <strong>{match.title ?? "Untitled"}</strong>
                        <div className={`badge ${match.slug_overlap ? "danger" : "warn"}`}>{match.similarity_score}</div>
                      </div>
                      <p className="muted">{match.entity_type}</p>
                      <p className="muted">{match.slug ?? "No slug"}</p>
                    </article>
                  ))
                ) : (
                  <p className="muted">No similar topics or published articles found.</p>
                )}
              </div>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
