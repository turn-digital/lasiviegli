# Ģenerē lejupielādējamos Markdown failus darbam ar AI rīkiem (Claude, Gemini u.c.).
#
#   uv run scripts/generate_ai_files.py [ceļš/uz/cvk_sv2026.db]
#
# Izveido:
#   public/ai/NN-<slug>.md                     — katra saraksta programma (program.text_md)
#   public/ai/visas-programmas-saeima2026.md   — visas programmas vienā failā
#   public/ai/visas-programmas-saeima2026.zip  — visi faili vienā arhīvā
#   src/data/ai_files.json                     — failu saraksts lejupielādes lapai (/ai/)

import json
import re
import sqlite3
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO.parent / "cvk_sv2026.db"

AI_DIR = REPO / "public" / "ai"
DATA_DIR = REPO / "src" / "data"

COMBINED_NAME = "visas-programmas-saeima2026.md"
ZIP_NAME = "visas-programmas-saeima2026.zip"


def shift_headings(md: str, target_min: int) -> str:
    """Nobīda visus virsrakstus tā, lai augstākais līmenis kļūst target_min.
    Faila virsrakstu (H1) un sadaļu virsrakstus dod ģenerators, tāpēc
    programmas teksta virsrakstiem jāsākas līmeni zemāk."""
    levels = [len(m) for m in re.findall(r"^(#{1,6}) ", md, flags=re.M)]
    if not levels:
        return md
    delta = target_min - min(levels)
    if delta == 0:
        return md

    def repl(m: re.Match) -> str:
        level = min(6, max(1, len(m.group(1)) + delta))
        return "#" * level + " "

    return re.sub(r"^(#{1,6}) ", repl, md, flags=re.M)


def party_header(r: sqlite3.Row) -> str:
    return (
        f"- Vēlēšanas: 15. Saeimas vēlēšanas, 2026. gads\n"
        f"- Kandidātu saraksts Nr. {r['list_number']}: {r['name']}\n"
        f"- Avots: Centrālā vēlēšanu komisija, {r['source_url']}\n"
        f"- Piezīme: teksta saturs nav mainīts, formatējums pārveidots Markdown."
    )


def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT p.list_number, p.name, p.slug, pr.text_md, pr.source_url
           FROM party p JOIN program pr ON pr.party_id = p.id
           ORDER BY p.list_number"""
    ).fetchall()

    missing = [r["slug"] for r in rows if not r["text_md"]]
    if missing:
        sys.exit(f"Trūkst text_md partijām: {missing}")

    AI_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    files = []
    combined_sections = []
    for r in rows:
        filename = f"{r['list_number']:02d}-{r['slug']}.md"

        single = (
            f"# Priekšvēlēšanu programma: {r['name']}\n\n"
            f"{party_header(r)}\n\n---\n\n"
            f"{shift_headings(r['text_md'].strip(), 2)}\n"
        )
        (AI_DIR / filename).write_text(single, encoding="utf-8", newline="\n")

        combined_sections.append(
            f"## Nr. {r['list_number']}. {r['name']}\n\n"
            f"{party_header(r)}\n\n"
            f"{shift_headings(r['text_md'].strip(), 3)}\n"
        )

        files.append(
            {
                "n": r["list_number"],
                "name": r["name"],
                "file": filename,
                "kb": max(1, round(len(single.encode("utf-8")) / 1024)),
            }
        )

    toc = "\n".join(f"{r['list_number']}. {r['name']}" for r in rows)
    combined = (
        "# 15. Saeimas vēlēšanu (2026) priekšvēlēšanu programmas — visi 14 kandidātu saraksti\n\n"
        "- Avots: Centrālā vēlēšanu komisija, https://dati.cvk.lv/SV2026/kandidatu-saraksti/\n"
        "- Saturs: visu 14 kandidātu sarakstu pilnās priekšvēlēšanu programmas oriģinālā\n"
        "- Struktūra: katrs saraksts sākas ar virsrakstu \"## Nr. <numurs>. <nosaukums>\"\n"
        "- Piezīme: teksta saturs nav mainīts, formatējums pārveidots Markdown.\n\n"
        "## Saturs\n\n"
        f"{toc}\n\n---\n\n"
        + "\n---\n\n".join(combined_sections)
    )
    (AI_DIR / COMBINED_NAME).write_text(combined, encoding="utf-8", newline="\n")

    zip_path = AI_DIR / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(AI_DIR / f["file"], f["file"])
        zf.write(AI_DIR / COMBINED_NAME, COMBINED_NAME)

    data = {
        "files": files,
        "combined": {
            "file": COMBINED_NAME,
            "kb": max(1, round(len(combined.encode("utf-8")) / 1024)),
        },
        "zip": {
            "file": ZIP_NAME,
            "kb": max(1, round(zip_path.stat().st_size / 1024)),
        },
    }
    (DATA_DIR / "ai_files.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )

    print(f"OK: {len(files)} faili + {COMBINED_NAME} + {ZIP_NAME} -> public/ai/")


if __name__ == "__main__":
    main()
