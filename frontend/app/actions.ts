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

export async function createDemoProjectAction(): Promise<void> {
  await postApiJson("/demo/bootstrap", {
    topic_query: "frequent urination with cystitis",
    audience: "general audience",
    cluster_name: `Local Demo Cluster ${new Date().toISOString()}`,
  });
  revalidatePath("/");
}
