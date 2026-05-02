import unicodedata
from pathlib import Path

DOC_DIR = Path(__file__).resolve().parents[2] / 'doc'

_DOCS_CACHE: str | None = None


def _normalize(text: str) -> str:
    # Arabic PDFs often store text in Presentation Forms (FE70-FEFF).
    # NFKC maps them back to Basic Arabic (0600-06FF) so keyword search works.
    return unicodedata.normalize('NFKC', text)


def _load_pdf_text(path: Path) -> str:
    # Try pymupdf first (better Arabic encoding support), fall back to pypdf.
    try:
        import fitz
        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        return _normalize('\n'.join(p for p in pages if p.strip()))
    except Exception:
        pass
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or '' for page in reader.pages]
        return _normalize('\n'.join(p for p in pages if p.strip()))
    except Exception:
        return ''


def get_docs_text() -> str:
    global _DOCS_CACHE
    if _DOCS_CACHE is None:
        parts = []
        for pdf in sorted(DOC_DIR.glob('*.pdf')):
            text = _load_pdf_text(pdf)
            if text:
                parts.append(f'[{pdf.name}]\n{text}')
        for txt in sorted(DOC_DIR.glob('*.txt')):
            try:
                text = _normalize(txt.read_text(encoding='utf-8'))
                if text.strip():
                    parts.append(f'[{txt.name}]\n{text}')
            except Exception:
                pass
        _DOCS_CACHE = '\n\n---\n\n'.join(parts) if parts else ''
    return _DOCS_CACHE


def _query_tokens(query: str) -> list[str]:
    q = _normalize(query)
    tokens = [t.strip() for t in q.split() if len(t.strip()) > 1]
    extras = [t[2:] for t in tokens if t.startswith('ال') and len(t) > 3]
    return list(dict.fromkeys(tokens + extras))


def search_in_docs(query: str, max_results: int = 10, context_lines: int = 6) -> list[dict]:
    text = get_docs_text()
    if not text or not query.strip():
        return []

    tokens = _query_tokens(query)
    if not tokens:
        return []

    lines = text.split('\n')
    results: list[dict] = []
    seen: set[int] = set()

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(tok.lower() in line_lower for tok in tokens):
            start = max(0, i - 2)
            end = min(len(lines), i + context_lines + 1)
            if start in seen:
                continue
            seen.update(range(start, end))
            snippet = '\n'.join(lines[start:end]).strip()
            if snippet:
                results.append({'body': snippet, 'source': 'university_docs'})
            if len(results) >= max_results:
                break

    return results
