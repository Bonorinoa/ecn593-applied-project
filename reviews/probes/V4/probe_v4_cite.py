"""V4 citation probe. Crossref lookup for every refs.bib entry that has a DOI.

Writes nothing under the repo except this script's sibling log, which the caller redirects.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIB = (ROOT / "thesis" / "refs.bib").read_text()


def unescape(s: str) -> str:
    s = s.replace("\\&", "&").replace("\\%", "%")
    s = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip().strip(",")
    return s


def norm(s: str) -> str:
    s = unescape(s).lower()
    s = s.replace("--", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def entries(text: str) -> list[dict]:
    chunks = re.split(r"\n(?=@)", text)
    out = []
    for ch in chunks:
        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)", ch)
        if not m:
            continue
        fields = {}
        for fm in re.finditer(r"(?m)^\s*([a-zA-Z]+)\s*=\s*[\{\"](.+?)[\}\"]\s*,?\s*$", ch):
            fields[fm.group(1).lower()] = unescape(fm.group(2))
        # multiline title/author
        for key in ("title", "author", "year", "doi", "journal", "booktitle"):
            mm = re.search(rf"(?is){key}\s*=\s*\{{(.*?)\}}", ch)
            if mm:
                fields[key] = unescape(mm.group(1))
            else:
                mm = re.search(rf'(?is){key}\s*=\s*"(.*?)"', ch)
                if mm:
                    fields[key] = unescape(mm.group(1))
        out.append({"type": m.group(1), "key": m.group(2), **fields})
    return out


def crossref(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.request.quote(doi, safe="/")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ecn593-v4-verifier/1.0 (mailto:augusto.gonzalez-bonorino@asu.edu)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())["message"]


def family(author_field: str) -> str:
    # "Last, First and Last, First" or "First Last and ..."
    first = re.split(r"\s+and\s+", author_field, flags=re.I)[0]
    if "," in first:
        return norm(first.split(",")[0])
    parts = first.split()
    return norm(parts[-1]) if parts else ""


def main() -> None:
    rows = entries(BIB)
    print(f"n_entries={len(rows)}")
    checked = 0
    mismatches = 0
    no_doi = []
    for e in rows:
        doi = e.get("doi", "").strip()
        if not doi:
            no_doi.append(e["key"])
            print(f"NO_DOI key={e['key']} type={e['type']} year={e.get('year')} title={e.get('title','')[:80]}")
            continue
        checked += 1
        try:
            msg = crossref(doi)
        except Exception as exc:
            mismatches += 1
            print(f"LOOKUP_FAIL key={e['key']} doi={doi} err={type(exc).__name__}: {exc}")
            continue
        cr_title = " ".join(msg.get("title") or [])
        cr_year = None
        for box in ("published-print", "published-online", "issued"):
            parts = (msg.get(box) or {}).get("date-parts") or []
            if parts and parts[0]:
                cr_year = str(parts[0][0])
                break
        cr_authors = msg.get("author") or []
        cr_family = norm(cr_authors[0].get("family", "")) if cr_authors else ""
        bib_family = family(e.get("author", ""))
        bib_year = e.get("year", "")
        title_ok = norm(e.get("title", "")) == norm(cr_title) or norm(e.get("title", "")) in norm(cr_title) or norm(cr_title) in norm(e.get("title", ""))
        year_ok = bib_year == cr_year
        author_ok = bib_family == cr_family or (bib_family and bib_family in cr_family) or (cr_family and cr_family in bib_family)
        status = "OK" if title_ok and year_ok and author_ok else "MISMATCH"
        if status != "OK":
            mismatches += 1
        print(
            f"{status} key={e['key']} doi={doi} bib_year={bib_year} cr_year={cr_year} "
            f"bib_author={bib_family} cr_author={cr_family} title_ok={title_ok}"
        )
        if status != "OK":
            print(f"  bib_title={e.get('title')}")
            print(f"  cr_title={cr_title}")
    print(f"checked={checked} mismatches={mismatches} no_doi={no_doi}")


if __name__ == "__main__":
    main()
