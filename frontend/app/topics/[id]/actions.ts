"use server";

import { revalidatePath } from "next/cache";

import { postApiJson } from "../../lib/api";

function refreshTopicPaths(topicId: string): void {
  revalidatePath("/");
  revalidatePath(`/topics/${topicId}`);
}

export async function collectSourcesAction(topicId: string): Promise<void> {
  await postApiJson(`/topics/${topicId}/collect-sources`);
  refreshTopicPaths(topicId);
}

export async function extractResearchNotesAction(topicId: string): Promise<void> {
  await postApiJson(`/topics/${topicId}/extract-research-notes`);
  refreshTopicPaths(topicId);
}

export async function generateBriefAction(topicId: string): Promise<void> {
  await postApiJson(`/topics/${topicId}/generate-brief`);
  refreshTopicPaths(topicId);
}

export async function generateDraftAction(topicId: string): Promise<void> {
  await postApiJson(`/topics/${topicId}/generate-draft`);
  refreshTopicPaths(topicId);
}

export async function addManualSourceAction(topicId: string, formData: FormData): Promise<void> {
  const title = String(formData.get("title") ?? "").trim();
  const url = String(formData.get("url") ?? "").trim();
  const author = String(formData.get("author") ?? "").trim();
  const rawContent = String(formData.get("raw_content") ?? "").trim();
  const reliabilityScoreValue = String(formData.get("reliability_score") ?? "").trim();

  if (!title || !url || !rawContent) {
    return;
  }

  const reliabilityScore = Number.parseFloat(reliabilityScoreValue || "0.8");

  await postApiJson(`/topics/${topicId}/sources/manual`, {
    title,
    url,
    author: author || null,
    raw_content: rawContent,
    reliability_score: Number.isFinite(reliabilityScore) ? reliabilityScore : 0.8,
  });
  refreshTopicPaths(topicId);
}
