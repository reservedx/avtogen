from __future__ import annotations

import re


class ArticleSectionRegenerator:
    def regenerate(self, markdown_content: str, section_heading: str, instructions: str | None = None) -> str:
        normalized_heading = self._normalize_heading(section_heading)
        replacement = self._replacement_block(normalized_heading, instructions)
        pattern = re.compile(
            rf"(?ms)^({re.escape(normalized_heading)}\s*\n)(.*?)(?=^##\s|\Z)"
        )
        if pattern.search(markdown_content):
            return pattern.sub(lambda match: f"{match.group(1)}{replacement}", markdown_content, count=1)
        suffix = f"\n\n{normalized_heading}\n{replacement}"
        return markdown_content.rstrip() + suffix

    def _normalize_heading(self, section_heading: str) -> str:
        stripped = section_heading.strip()
        if stripped.startswith("#"):
            return stripped
        return f"## {stripped}"

    def _replacement_block(self, section_heading: str, instructions: str | None) -> str:
        instruction_text = f" Editor guidance: {instructions.strip()}" if instructions else ""
        title = section_heading.removeprefix("## ").strip()
        return (
            f"This section was regenerated for editorial refinement.{instruction_text}\n\n"
            f"It now focuses on {title.lower()} with clearer structure, safer wording, and stronger readability.\n"
        )
