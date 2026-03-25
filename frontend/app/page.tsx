const reviewQueue = [
  {
    title: "Frequent urination with cystitis",
    status: "in_review",
    risk: "manual review required",
    notes: "Treatment-adjacent language detected, verify red flags and citations.",
  },
  {
    title: "Burning during urination",
    status: "needs_revision",
    risk: "quality warnings",
    notes: "Weak FAQ coverage and missing internal links.",
  },
];

const stats = [
  { label: "Drafts this week", value: "24" },
  { label: "Blocked by QA", value: "7" },
  { label: "Awaiting review", value: "11" },
  { label: "Published", value: "13" },
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="badge">Editorial Control Center</p>
        <h1>Women's health content workflow with review-first publishing.</h1>
        <p>The MVP admin keeps risky YMYL content visible, versioned, and gated by research coverage, quality checks, and editorial approval before CMS sync.</p>
      </section>
      <div className="grid">
        <aside className="card">
          <h2>Pipeline Snapshot</h2>
          {stats.map((item) => (
            <div className="stat" key={item.label}>
              <strong>{item.value}</strong>
              <span>{item.label}</span>
            </div>
          ))}
        </aside>
        <section className="card">
          <h2>Review Queue</h2>
          {reviewQueue.map((item) => (
            <article className="queue-item" key={item.title}>
              <div className={item.status === "needs_revision" ? "badge warn" : "badge danger"}>{item.status}</div>
              <strong>{item.title}</strong>
              <span>{item.risk}</span>
              <p>{item.notes}</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
