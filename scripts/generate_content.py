# Ģenerē lapas saturu no CVK 2026 partiju programmu datubāzes.
#
#   uv run scripts/generate_content.py [ceļš/uz/cvk_sv2026.db]
#
# Izveido:
#   src/content/easy/<slug>.md  — programma vieglajā valodā (program.text_easy_md_corrected)
#   src/content/orig/<slug>.md  — oriģināls (program.text_md; virsraksti pazemināti, ja ir H1)
#   src/data/parties.json       — dati sākumlapas kartītēm un partiju lapu galvenēm

import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO.parent / "cvk_sv2026.db"

EASY_DIR = REPO / "src" / "content" / "easy"
ORIG_DIR = REPO / "src" / "content" / "orig"
DATA_DIR = REPO / "src" / "data"


def yaml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def strip_leading_h1(md: str) -> str:
    """Noņem pirmo H1 rindu — lapas virsrakstu dod lapas šablons."""
    lines = md.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def demote_h1(md: str) -> str:
    """Ja tekstā ir H1 virsraksti, pazemina visus virsrakstus par vienu līmeni,
    lai lapā paliktu tikai viens H1 (lapas virsraksts)."""
    if not re.search(r"^# ", md, flags=re.M):
        return md
    return re.sub(r"^(#{1,5}) ", r"#\1 ", md, flags=re.M)


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT p.list_number, p.name, p.slug, p.candidate_count,
                  pr.text_easy_md_corrected AS easy, pr.text_md AS orig,
                  pr.word_count, pr.source_url
           FROM party p JOIN program pr ON pr.party_id = p.id
           ORDER BY p.list_number"""
    ).fetchall()

    missing = [r["slug"] for r in rows if not r["easy"] or not r["orig"]]
    if missing:
        sys.exit(f"Trūkst teksta kolonnu partijām: {missing}")

    EASY_DIR.mkdir(parents=True, exist_ok=True)
    ORIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    parties = []
    for r in rows:
        easy = strip_leading_h1(r["easy"])
        orig = demote_h1(r["orig"].strip())
        title = yaml_quote(r["name"])

        (EASY_DIR / f"{r['slug']}.md").write_text(
            f"---\ntitle: {title}\n---\n\n{easy}\n",
            encoding="utf-8", newline="\n",
        )
        (ORIG_DIR / f"{r['slug']}.md").write_text(
            f"---\ntitle: {title}\n---\n\n{orig}\n",
            encoding="utf-8", newline="\n",
        )

        parties.append(
            {
                "n": r["list_number"],
                "name": r["name"],
                "slug": r["slug"],
                "candidates": r["candidate_count"],
                "words": r["word_count"],
                "minutes": max(3, round(len(easy.split()) / 170)),
                "sourceUrl": r["source_url"],
            }
        )

    (DATA_DIR / "parties.json").write_text(
        json.dumps(parties, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )

    print(f"OK: {len(parties)} partijas -> easy/, orig/, parties.json")


if __name__ == "__main__":
    main()
