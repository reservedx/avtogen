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
