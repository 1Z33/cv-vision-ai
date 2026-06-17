"""
Fix DB - Ajoute les colonnes manquantes dans la table analyses

Usage:
  python fix_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def get_db_path() -> Path:
    # La DB est généralement à la racine backend/app/ ou derrière un script.
    # On essaie plusieurs chemins “probables”.
    candidates = [
        Path("./cv_vision_ai.db"),
        Path("./cv_vision-ai.db"),
        Path("./app/cv_vision_ai.db"),
        Path("./app/cv_vision_ai.db"),
        Path("../cv_vision_ai.db"),
        Path("../cv_vision_ai.db"),
        Path("../cv-vision-ai.db"),
        Path("../cv_vision_ai.db"),
    ]

    for c in candidates:
        p = (Path(__file__).resolve().parent / c).resolve() if not c.is_absolute() else c
        if p.exists():
            return p

    # fallback: nom attendu dans le script donné au user
    return (Path(__file__).resolve().parent / "cv_vision_ai.db").resolve()


def column_names(cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table});")
    rows = cursor.fetchall()
    return {r[1] for r in rows}


def ensure_column(cursor, table: str, name: str, ddl: str) -> bool:
    cols = column_names(cursor, table)
    if name in cols:
        print(f"✓ Colonne '{name}' existe déjà dans '{table}'")
        return True
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl};")
    print(f"✅ Ajout de la colonne '{name}' dans '{table}'")
    return True


def main() -> int:
    db_path = get_db_path()
    print(f"DB path: {db_path}")
    print(f"DB exists: {db_path.exists()}")

    if not db_path.exists():
        print("❌ Base de données non trouvée. Elle sera créée au prochain démarrage du serveur.")
        return 0

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analyses';")
    if cursor.fetchone() is None:
        print("❌ Table 'analyses' introuvable. Aucune correction possible.")
        conn.close()
        return 0

    print("\nColonnes actuelles dans 'analyses':")
    for col in cursor.execute("PRAGMA table_info(analyses);").fetchall():
        print(f"  - {col[1]} ({col[2]})")

    ensure_column(cursor, "analyses", "used_gemini", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(cursor, "analyses", "model_compliance_breakdown", "TEXT")
    ensure_column(cursor, "analyses", "model_compliance_score", "INTEGER")

    cols = column_names(cursor, "analyses")
    if "updated_at" not in cols:
        # SQLite ne permet pas toujours les DEFAULT non-constantes via ALTER TABLE.
        # On ajoute une colonne simple; la valeur sera gérée côté application si besoin.
        ensure_column(cursor, "analyses", "updated_at", "DATETIME")


    conn.commit()

    print("\nColonnes après modification:")
    for col in cursor.execute("PRAGMA table_info(analyses);").fetchall():
        print(f"  - {col[1]} ({col[2]})")

    conn.close()
    print("\n🎉 Base de données corrigée. Redémarre uvicorn puis réessaie l'upload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
