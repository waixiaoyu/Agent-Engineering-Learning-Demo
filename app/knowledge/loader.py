from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class GuideDocument:
    id: str
    title: str
    equipment: str
    source_path: str
    content: str


FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def load_guides(root: str | Path | None = None) -> list[GuideDocument]:
    base_dir = Path(root) if root else _default_guide_dir()
    if not base_dir.exists():
        return []

    documents: list[GuideDocument] = []
    for path in sorted(base_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(text)
        title = metadata.get("title") or _first_heading(body) or path.stem
        documents.append(
            GuideDocument(
                id=metadata.get("id", path.stem),
                title=title,
                equipment=metadata.get("equipment", "unknown"),
                source_path=str(path),
                content=body.strip(),
            )
        )
    return documents


def _default_guide_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "knowledge" / "guides"


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')

    body = text[match.end() :]
    return metadata, body


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None

