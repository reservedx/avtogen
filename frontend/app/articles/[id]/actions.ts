"use server";

import { revalidatePath } from "next/cache";

import { postApiJson } from "../../lib/api";

function refreshArticlePaths(articleId: string): void {
  revalidatePath("/");
  revalidatePath(`/articles/${articleId}`);
}

export async function runQualityCheckAction(articleId: string): Promise<void> {
  await postApiJson(`/articles/${articleId}/run-quality-check`);
  refreshArticlePaths(articleId);
}

export async function submitForReviewAction(articleId: string): Promise<void> {
  await postApiJson(`/articles/${articleId}/submit-for-review`);
  refreshArticlePaths(articleId);
}

export async function approveArticleAction(articleId: string, formData: FormData): Promise<void> {
  const reviewerName = String(formData.get("reviewer_name") || "Editor");
  const notes = String(formData.get("notes") || "");
  await postApiJson(`/articles/${articleId}/approve`, {
    reviewer_name: reviewerName,
    notes,
  });
  refreshArticlePaths(articleId);
}

export async function rejectArticleAction(articleId: string, formData: FormData): Promise<void> {
  const reviewerName = String(formData.get("reviewer_name") || "Editor");
  const notes = String(formData.get("notes") || "");
  await postApiJson(`/articles/${articleId}/reject`, {
    reviewer_name: reviewerName,
    notes,
  });
  refreshArticlePaths(articleId);
}

export async function publishArticleAction(articleId: string): Promise<void> {
  await postApiJson(`/articles/${articleId}/publish`);
  refreshArticlePaths(articleId);
}

export async function regenerateSectionAction(articleId: string, formData: FormData): Promise<void> {
  const sectionHeading = String(formData.get("section_heading") || "FAQ");
  const instructions = String(formData.get("instructions") || "");
  await postApiJson(`/articles/${articleId}/regenerate-section`, {
    section_heading: sectionHeading,
    instructions,
  });
  refreshArticlePaths(articleId);
}
