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
