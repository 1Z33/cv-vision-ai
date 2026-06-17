import sqlite3
import os

def migrate():
    db_path = "cv_vision_ai.db"
    if not os.path.exists(db_path):
        print(f"Base de données introuvable à l'emplacement : {os.path.abspath(db_path)}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer les colonnes existantes
    cursor.execute("PRAGMA table_info(analyses)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    # Colonnes à ajouter impérativement
    required = [
        ("used_gemini", "BOOLEAN DEFAULT 0"),
        ("model_compliance_score", "INTEGER"),
        ("model_compliance_breakdown", "JSON"),
        ("updated_at", "DATETIME")
    ]
    
    for col_name, col_type in required:
        if col_name not in existing_cols:
            print(f"Ajout de la colonne : {col_name}")
            cursor.execute(f"ALTER TABLE analyses ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migration manuelle terminée avec succès.")

if __name__ == "__main__":
    migrate()