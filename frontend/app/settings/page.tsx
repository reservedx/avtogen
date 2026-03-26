import { saveRuntimeSettingsAction } from "../actions";
import { fetchApiJson } from "../lib/api";

type SettingsSummary = {
  app_name: string;
  app_env: string;
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

function boolText(value: boolean): string {
  return value ? "Да" : "Нет";
}

export default async function SettingsPage() {
  const settings = await fetchApiJson<SettingsSummary>("/settings");

  if (!settings) {
    return (
      <main className="page-shell">
        <section className="hero compact">
          <div className="hero-copy">
            <p className="eyebrow">Runtime Settings</p>
            <h1>Настройки недоступны</h1>
            <p className="hero-text">Backend не ответил на запрос настроек. Проверь API и попробуй снова.</p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="hero compact">
        <div className="hero-copy">
          <p className="eyebrow">Runtime Settings</p>
          <h1>Глобальные настройки</h1>
          <p className="hero-text">
            Здесь можно менять ключевые параметры fast-publish режима, quality gate и базовые правила публикации без ручного редактирования `.env`.
          </p>
        </div>
        <div className="hero-status">
          <div className="badge success">Live runtime control</div>
          <div className="status-stack">
            <span>Persisted overrides</span>
            <strong>{settings.runtime_override_keys.length}</strong>
          </div>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="column-main">
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="panel-label">Управление режимом</p>
                <h2>Флаги и пороги pipeline</h2>
              </div>
            </div>
            <form className="action-form" action={saveRuntimeSettingsAction}>
              <label className="toggle-row"><input defaultChecked={settings.auto_publish_enabled} name="auto_publish_enabled" type="checkbox" /> <span>Разрешить auto-publish</span></label>
              <label className="toggle-row"><input defaultChecked={settings.fast_publish_enabled} name="fast_publish_enabled" type="checkbox" /> <span>Включить fast-publish mode</span></label>
              <label className="toggle-row"><input defaultChecked={settings.auto_approve_low_risk} name="auto_approve_low_risk" type="checkbox" /> <span>Автоодобрение low-risk статей</span></label>
              <label className="toggle-row"><input defaultChecked={settings.auto_publish_low_risk} name="auto_publish_low_risk" type="checkbox" /> <span>Автопубликация low-risk статей</span></label>
              <label className="toggle-row"><input defaultChecked={settings.use_stub_generation} name="use_stub_generation" type="checkbox" /> <span>Stub generation вместо real OpenAI</span></label>

              <div className="settings-grid">
                <label>
                  <span>Min quality score</span>
                  <input defaultValue={settings.min_quality_score} name="min_quality_score" step="1" type="number" />
                </label>
                <label>
                  <span>Max risk score</span>
                  <input defaultValue={settings.max_risk_score_for_auto_publish} name="max_risk_score_for_auto_publish" step="1" type="number" />
                </label>
                <label>
                  <span>Fast lane min quality</span>
                  <input defaultValue={settings.fast_lane_min_quality_score} name="fast_lane_min_quality_score" step="1" type="number" />
                </label>
                <label>
                  <span>Fast lane max risk</span>
                  <input defaultValue={settings.fast_lane_max_risk_score} name="fast_lane_max_risk_score" step="1" type="number" />
                </label>
                <label>
                  <span>Required source count</span>
                  <input defaultValue={settings.required_source_count} name="required_source_count" step="1" type="number" />
                </label>
                <label>
                  <span>Similarity threshold</span>
                  <input defaultValue={settings.similarity_threshold} name="similarity_threshold" step="0.01" type="number" />
                </label>
              </div>

              <label>
                <span>Medical disclaimer</span>
                <textarea
                  defaultValue={settings.default_medical_disclaimer}
                  name="default_medical_disclaimer"
                  rows={4}
                />
              </label>

              <button className="action-button accent-button" type="submit">
                Сохранить runtime settings
              </button>
            </form>
          </article>
        </div>

        <div className="column-side">
          <article className="panel">
            <p className="panel-label">Текущая конфигурация</p>
            <h2>Снимок runtime</h2>
            <div className="settings-list">
              <div>
                <dt>APP_ENV</dt>
                <dd>{settings.app_env}</dd>
              </div>
              <div>
                <dt>OpenAI active</dt>
                <dd>{boolText(settings.openai_enabled)}</dd>
              </div>
              <div>
                <dt>Storage backend</dt>
                <dd>{settings.asset_storage_backend}</dd>
              </div>
              <div>
                <dt>Database mode</dt>
                <dd>{settings.database_is_sqlite ? "SQLite" : settings.database_url}</dd>
              </div>
              <div>
                <dt>Brief model</dt>
                <dd>{settings.openai_brief_model}</dd>
              </div>
              <div>
                <dt>Draft model</dt>
                <dd>{settings.openai_draft_model}</dd>
              </div>
              <div>
                <dt>Image model</dt>
                <dd>{settings.openai_image_model}</dd>
              </div>
            </div>
          </article>

          <article className="panel">
            <p className="panel-label">Активные правила</p>
            <h2>Что сейчас включено</h2>
            <div className="stack">
              <div className="mini-chip">Auto-publish: {boolText(settings.auto_publish_enabled)}</div>
              <div className="mini-chip">Fast publish: {boolText(settings.fast_publish_enabled)}</div>
              <div className="mini-chip">Auto-approve low risk: {boolText(settings.auto_approve_low_risk)}</div>
              <div className="mini-chip">Auto-publish low risk: {boolText(settings.auto_publish_low_risk)}</div>
              <div className="mini-chip">Stub mode: {boolText(settings.use_stub_generation)}</div>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
