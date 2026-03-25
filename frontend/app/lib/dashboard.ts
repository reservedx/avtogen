import { fetchApiJson } from "./api";

type Metrics = {
  clusters_count: number;
  topics_count: number;
  articles_count: number;
  published_articles_count: number;
  quality_reports_count: number;
  task_runs_count: number;
};

type Settings = {
  app_name: string;
  app_env: string;
  database_is_sqlite: boolean;
  asset_storage_backend: string;
  asset_storage_dir: string;
  s3_bucket: string;
  openai_enabled: boolean;
  use_stub_generation: boolean;
  auto_publish_enabled: boolean;
};

type Topic = {
  id: string;
  working_title: string;
  audience: string;
  status: string;
  target_query: string;
};

type Article = {
  id: string;
  topic_id: string;
  title: string;
  slug: string;
  status: string;
  quality_score: number | null;
  risk_score: number | null;
  cms_post_id: string | null;
  published_url: string | null;
};

type ArticleWorkspace = {
  current_version: {
    version: number;
    word_count: number;
  } | null;
  images: Array<{ id: string }>;
  editorial_reviews: Array<{ id: string; decision: string }>;
  publishing_job: { status: string } | null;
};

type TaskRun = {
  id: string;
  task_type: string;
  entity_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
};

export type DashboardData = {
  metrics: Metrics;
  settings: Settings;
  topics: Topic[];
  articles: Article[];
  leadWorkspace: ArticleWorkspace | null;
  taskRuns: TaskRun[];
  apiOnline: boolean;
};

function fallbackData(): DashboardData {
  return {
    apiOnline: false,
    metrics: {
      clusters_count: 4,
      topics_count: 19,
      articles_count: 12,
      published_articles_count: 5,
      quality_reports_count: 8,
      task_runs_count: 23,
    },
    settings: {
      app_name: "Women Health Content Platform",
      app_env: "local",
      database_is_sqlite: true,
      asset_storage_backend: "local",
      asset_storage_dir: "./data/generated_assets",
      s3_bucket: "article-assets",
      openai_enabled: false,
      use_stub_generation: true,
      auto_publish_enabled: false,
    },
    topics: [
      {
        id: "mock-topic-1",
        working_title: "Frequent urination with cystitis",
        audience: "general audience",
        status: "in_review",
        target_query: "frequent urination with cystitis",
      },
      {
        id: "mock-topic-2",
        working_title: "Burning during urination",
        audience: "general audience",
        status: "needs_revision",
        target_query: "burning during urination",
      },
    ],
    articles: [
      {
        id: "mock-article-1",
        topic_id: "mock-topic-1",
        title: "Frequent urination with cystitis",
        slug: "frequent-urination-with-cystitis",
        status: "in_review",
        quality_score: 81,
        risk_score: 34,
        cms_post_id: null,
        published_url: null,
      },
      {
        id: "mock-article-2",
        topic_id: "mock-topic-2",
        title: "Burning during urination",
        slug: "burning-during-urination",
        status: "needs_revision",
        quality_score: 72,
        risk_score: 29,
        cms_post_id: null,
        published_url: null,
      },
      {
        id: "mock-article-3",
        topic_id: "mock-topic-3",
        title: "Night urination overview",
        slug: "night-urination-overview",
        status: "published",
        quality_score: 89,
        risk_score: 12,
        cms_post_id: "401",
        published_url: "https://example.com/night-urination-overview",
      },
    ],
    leadWorkspace: {
      current_version: { version: 3, word_count: 1985 },
      images: [{ id: "img-1" }, { id: "img-2" }, { id: "img-3" }],
      editorial_reviews: [{ id: "rev-1", decision: "approved" }],
      publishing_job: { status: "queued" },
    },
    taskRuns: [
      {
        id: "task-1",
        task_type: "article_pipeline",
        entity_type: "topic_query",
        status: "completed",
        started_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
        error_message: null,
      },
      {
        id: "task-2",
        task_type: "publish_article",
        entity_type: "article",
        status: "failed",
        started_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
        error_message: "WordPress media timeout",
      },
    ],
  };
}

export async function getDashboardData(): Promise<DashboardData> {
  const [articles, metrics, settings, topics, taskRuns] = await Promise.all([
    fetchApiJson<Article[]>("/articles"),
    fetchApiJson<Metrics>("/metrics"),
    fetchApiJson<Settings>("/settings"),
    fetchApiJson<Topic[]>("/topics"),
    fetchApiJson<TaskRun[]>("/task-runs"),
  ]);

  if (!metrics || !settings) {
    return fallbackData();
  }

  const articleRows = articles && articles.length ? articles : deriveArticlesFromTopics(topics ?? []);
  const leadWorkspace = articleRows[0]
    ? await fetchApiJson<ArticleWorkspace>(`/articles/${articleRows[0].id}/workspace`)
    : null;

  return {
    apiOnline: true,
    metrics,
    settings,
    topics: topics ?? [],
    articles: articleRows,
    leadWorkspace,
    taskRuns: taskRuns ?? [],
  };
}

function deriveArticlesFromTopics(topics: Topic[]): Article[] {
  return topics.slice(0, 6).map((topic, index) => ({
    id: `topic-derived-${topic.id}`,
    topic_id: topic.id,
    title: topic.working_title,
    slug: topic.target_query.toLowerCase().replaceAll(" ", "-"),
    status: topic.status,
    quality_score: index % 2 === 0 ? 84 - index * 2 : 73 + index,
    risk_score: index % 2 === 0 ? 18 + index * 4 : 31 - index,
    cms_post_id: topic.status === "published" ? String(500 + index) : null,
    published_url: topic.status === "published" ? `https://example.com/${topic.id}` : null,
  }));
}
