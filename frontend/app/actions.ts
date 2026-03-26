"use server";

import { revalidatePath } from "next/cache";

import { postApiJson } from "./lib/api";

async function runBulkAction(articleIds: string[], action: string): Promise<void> {
  if (!articleIds.length) {
    return;
  }
  await postApiJson("/articles/bulk-action", {
    article_ids: articleIds,
    action,
  });
  revalidatePath("/");
}

export async function runBulkQualityCheckAction(articleIds: string[]): Promise<void> {
  await runBulkAction(articleIds, "run_quality_check");
}

export async function bulkGenerateImagesAction(articleIds: string[]): Promise<void> {
  await runBulkAction(articleIds, "generate_images");
}

export async function bulkSubmitForReviewAction(articleIds: string[]): Promise<void> {
  await runBulkAction(articleIds, "submit_for_review");
}

export async function bulkApproveAction(articleIds: string[]): Promise<void> {
  if (!articleIds.length) {
    return;
  }
  await postApiJson("/articles/bulk-action", {
    article_ids: articleIds,
    action: "approve",
    reviewer_name: "Editor",
    notes: "Bulk approval from dashboard",
  });
  revalidatePath("/");
}

export async function bulkPublishAction(articleIds: string[]): Promise<void> {
  await runBulkAction(articleIds, "publish");
}

async function bulkModerateImages(imageIds: string[], action: "approve" | "reject" | "regenerate"): Promise<void> {
  if (!imageIds.length) {
    return;
  }
  await postApiJson("/images/bulk-moderate", {
    image_ids: imageIds,
    action,
    moderator_name: "Editor",
    notes:
      action === "approve"
        ? "Bulk image approval from dashboard"
        : action === "regenerate"
          ? "Bulk regeneration requested from dashboard"
          : "Bulk image rejection from dashboard",
  });
  revalidatePath("/");
}

export async function bulkApproveImagesAction(imageIds: string[]): Promise<void> {
  await bulkModerateImages(imageIds, "approve");
}

export async function bulkRegenerateImagesAction(imageIds: string[]): Promise<void> {
  await bulkModerateImages(imageIds, "regenerate");
}

export async function createDemoProjectAction(): Promise<void> {
  await postApiJson("/demo/bootstrap", {
    topic_query: "frequent urination with cystitis",
    audience: "general audience",
    cluster_name: `Local Demo Cluster ${new Date().toISOString()}`,
  });
  revalidatePath("/");
}

export async function runBulkFastLaneTopicsAction(topicIds: string[]): Promise<void> {
  if (!topicIds.length) {
    return;
  }
  await postApiJson("/topics/bulk-fast-lane", {
    topic_ids: topicIds,
  });
  revalidatePath("/");
}

export async function bulkCreateTopicsAction(formData: FormData): Promise<void> {
  const clusterName = String(formData.get("cluster_name") || "Bulk Imported Topics").trim();
  const audience = String(formData.get("audience") || "general audience").trim();
  const rawTopics = String(formData.get("topic_queries") || "").trim();
  if (!rawTopics) {
    return;
  }
  const topicQueries = rawTopics
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (!topicQueries.length) {
    return;
  }
  await postApiJson("/topics/bulk-create", {
    cluster_name: clusterName,
    audience: audience || "general audience",
    topic_queries: topicQueries,
  });
  revalidatePath("/");
}

function checkboxValue(formData: FormData, key: string): boolean {
  return String(formData.get(key) || "") === "on";
}

export async function saveRuntimeSettingsAction(formData: FormData): Promise<void> {
  await postApiJson("/settings/runtime", {
    auto_publish_enabled: checkboxValue(formData, "auto_publish_enabled"),
    fast_publish_enabled: checkboxValue(formData, "fast_publish_enabled"),
    auto_approve_low_risk: checkboxValue(formData, "auto_approve_low_risk"),
    auto_publish_low_risk: checkboxValue(formData, "auto_publish_low_risk"),
    use_stub_generation: checkboxValue(formData, "use_stub_generation"),
    min_quality_score: Number(formData.get("min_quality_score") || 78),
    max_risk_score_for_auto_publish: Number(formData.get("max_risk_score_for_auto_publish") || 20),
    fast_lane_min_quality_score: Number(formData.get("fast_lane_min_quality_score") || 68),
    fast_lane_max_risk_score: Number(formData.get("fast_lane_max_risk_score") || 12),
    required_source_count: Number(formData.get("required_source_count") || 2),
    similarity_threshold: Number(formData.get("similarity_threshold") || 0.86),
    default_medical_disclaimer: String(formData.get("default_medical_disclaimer") || "").trim(),
  });
  revalidatePath("/");
  revalidatePath("/settings");
}
