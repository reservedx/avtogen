import re


class TranscriptCleaner:
    pattern = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")

    def clean(self, raw_text: str) -> str:
        text = self.pattern.sub("", raw_text)
        text = re.sub(r"\s+", " ", text).strip()
        chunks = []
        seen = set()
        for piece in text.split("."):
            piece = piece.strip()
            if not piece or piece.lower() in seen:
                continue
            seen.add(piece.lower())
            chunks.append(piece)
        return ". ".join(chunks)
