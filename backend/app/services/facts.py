from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import ResearchNote, Source


class ResearchNoteExtractor:
    SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
    WHITESPACE_RE = re.compile(r"\s+")
    NON_WORD_RE = re.compile(r"[^a-z0-9а-яё]+", re.IGNORECASE)

    def extract_for_topic(self, db: Session, topic_id: UUID, sources: Iterable[Source]) -> list[ResearchNote]:
        rows = self.extract_rows(list(sources))
        db.query(ResearchNote).filter(ResearchNote.topic_id == topic_id).delete(synchronize_session=False)
        notes: list[ResearchNote] = []
        for row in rows:
            note = ResearchNote(topic_id=topic_id, **row)
            db.add(note)
            notes.append(note)
        db.flush()
        return notes

    def extract_rows(self, sources: list[Source | dict]) -> list[dict]:
        notes: list[dict] = []
        seen: set[str] = set()
        for source in sources:
            for candidate in self._extract_from_source(source):
                signature = self._signature(candidate["fact_type"], candidate["content"])
                if signature in seen:
                    continue
                seen.add(signature)
                notes.append(candidate)
        return notes

    def _extract_from_source(self, source: Source | dict) -> list[dict]:
        text = self._source_field(source, "cleaned_content") or self._source_field(source, "raw_content") or ""
        if not text:
            return []
        reliability_score = float(self._source_field(source, "reliability_score", 0.6) or 0.6)
        rows: list[dict] = []
        for sentence in self._split_sentences(text):
            fact_type = self._classify_fact_type(sentence)
            if not fact_type:
                continue
            rows.append(
                {
                    "source_id": self._source_field(source, "id"),
                    "fact_type": fact_type,
                    "content": sentence,
                    "confidence_score": self._confidence_for(fact_type, reliability_score),
                    "citation_data": {
                        "url": self._source_field(source, "url"),
                        "title": self._source_field(source, "title"),
                        "source_type": self._source_field(source, "source_type", "other"),
                        "published_at": self._serialize_datetime(self._source_field(source, "published_at")),
                    },
                }
            )
            if len(rows) >= 6:
                break
        return rows

    def _split_sentences(self, text: str) -> list[str]:
        normalized = self.WHITESPACE_RE.sub(" ", text.strip())
        sentences = []
        for sentence in self.SENTENCE_SPLIT_RE.split(normalized):
            trimmed = sentence.strip(" -")
            if 45 <= len(trimmed) <= 260:
                sentences.append(trimmed)
        return sentences

    def _classify_fact_type(self, sentence: str) -> str | None:
        text = sentence.lower()
        if any(term in text for term in ["call your doctor", "seek medical", "urgent", "fever", "blood in urine", "pregnan", "severe pain"]):
            return "red_flag"
        if any(term in text for term in ["cause", "caused by", "because", "inflammation", "irritation", "infection"]):
            return "cause"
        if any(term in text for term in ["symptom", "sign", "urge to urinate", "frequent urination", "burning", "painful urination"]):
            return "symptom"
        if any(term in text for term in ["avoid", "do not", "should not", "when to see", "when to seek"]):
            return "guidance"
        return None

    def _confidence_for(self, fact_type: str, reliability_score: float) -> float:
        boosts = {"red_flag": 0.12, "symptom": 0.08, "cause": 0.06, "guidance": 0.04}
        return min(0.98, round(reliability_score + boosts.get(fact_type, 0.0), 2))

    def _signature(self, fact_type: str, content: str) -> str:
        normalized = self.NON_WORD_RE.sub(" ", content.lower())
        normalized = self.WHITESPACE_RE.sub(" ", normalized).strip()
        return f"{fact_type}:{normalized}"

    def _source_field(self, source: Source | dict, name: str, default=None):
        if isinstance(source, dict):
            return source.get(name, default)
        return getattr(source, name, default)

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()
