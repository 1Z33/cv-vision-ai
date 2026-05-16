"""
Test fiable de la connexion DB avec la config du projet
"""

import asyncio
import sys
import os

# Ajoute le dossier parent au path pour importer app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_config_loading():
    """Test 1 : La config se charge-t-elle ?"""
    print("=" * 50)
    print("TEST 1 : Chargement de la configuration")
    print("=" * 50)
    
    try:
        from app.core.config import settings
        print(f"✅ Config chargée")
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
        print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"   DEBUG: {settings.DEBUG}")
        return settings
    except Exception as e:
        print(f"❌ Erreur config: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_engine_creation(settings):
    """Test 2 : L'engine SQLAlchemy se crée-t-il ?"""
    print("\n" + "=" * 50)
    print("TEST 2 : Création de l'engine")
    print("=" * 50)
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG
        )
        print("✅ Engine créé")
        
        # Test connexion
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"✅ Connexion OK - SELECT 1 = {value}")
        
        await engine.dispose()
        print("✅ Engine fermé proprement")
        return True
        
    except Exception as e:
        print(f"❌ Erreur engine: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_session_factory(settings):
    """Test 3 : La session factory fonctionne-t-elle ?"""
    print("\n" + "=" * 50)
    print("TEST 3 : Session factory")
    print("=" * 50)
    
    try:
        from app.db.session import AsyncSessionLocal, get_db
        
        print("✅ AsyncSessionLocal importé")
        
        # Test création session
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 'test_session' as msg"))
            row = result.fetchone()
            print(f"✅ Session OK - {row.msg}")
        
        # Test get_db (generator)
        print("✅ get_db importé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur session: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_models_creation(settings):
    """Test 4 : Création des tables (Alembic/SQLAlchemy)"""
    print("\n" + "=" * 50)
    print("TEST 4 : Création des tables")
    print("=" * 50)
    
    try:
        # IMPORT IMPORTANT : On doit importer les modèles pour qu'ils soient enregistrés dans Base.metadata
        from app.db.base import Base
        from app.models.user import User
        from app.models.cv import CV
        from app.models.analysis import Analysis
        from app.models.interview import InterviewSession, InterviewQA
        from app.models.job import Job
        from app.models.match import Match
        
        from app.db.session import async_engine
        
        print("✅ Base et engine importés")
        
        # Créer toutes les tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables créées avec succès")
        
        # Vérifier via une requête directe car l'inspector sync peut échouer en contexte async
        async with async_engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables trouvées en base: {tables}")
            
            if len(tables) < 2:
                print("⚠️  Attention : Très peu de tables détectées. Vérifiez vos imports de modèles.")

        return True
        
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n" + "🧪 TEST COMPLET DE LA BASE DE DONNÉES 🧪")
    print("=" * 50)
    
    # Test 1 : Config
    settings = await test_config_loading()
    if not settings:
        print("\n❌ ARRÊT : Impossible de charger la config")
        return
    
    # Test 2 : Engine
    if not await test_engine_creation(settings):
        print("\n❌ ARRÊT : Engine non fonctionnel")
        return
    
    # Test 3 : Session
    if not await test_session_factory(settings):
        print("\n❌ ARRÊT : Sessions non fonctionnelles")
        return
    
    # Test 4 : Tables (optionnel, peut échouer si Alembic pas initialisé)
    await test_models_creation(settings)
    
    print("\n" + "=" * 50)
    print("✅ TESTS TERMINÉS")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 

import psycopg2
from psycopg2.extras import RealDictCursor

def test_connection(settings):
    print("=" * 60)
    print("TEST CONNEXION POSTGRESQL - TABLES CVISION AI")
    print("=" * 60)
    
    conn = None
    try:
        # 1. Connexion
        # On extrait les paramètres de l'URL pour être raccord avec SQLAlchemy
        from sqlalchemy.engine import make_url
        url = make_url(settings.DATABASE_URL.replace("+asyncpg", ""))
        
        print(f"\n🔄 Connexion à la base : {url.database} sur {url.host}...")
        conn = psycopg2.connect(
            host=url.host,
            port=url.port or 5432,
            database=url.database,
            user=url.username,
            password=url.password
        )
        print("✅ Connexion réussie !")
        
        # 2. Liste des tables
        print("\n📋 Tables existantes :")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"   • {table[0]}")
        
        # 3. Structure de chaque table
        print("\n🔍 Structure des tables :")
        for table in tables:
            table_name = table[0]
            print(f"\n   📌 Table : {table_name}")
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Colonnes
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cur.fetchall()
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"      • {col['column_name']} : {col['data_type']} ({nullable})")
        
        # 4. Test insertion dans users
        print("\n📝 Test insertion (table users) :")
        with conn.cursor() as cur:
            import uuid
            # Vérifie si la table users existe
            cur.execute("SELECT COUNT(*) FROM users;")
            count = cur.fetchone()[0]
            print(f"   Nombre d'utilisateurs actuels : {count}")
            
            # Insertion test
            cur.execute("""
                INSERT INTO users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (email) DO NOTHING
                RETURNING id;
            """, (str(uuid.uuid4()), 'test@example.com', 'hashed_test', 'Test User', 'candidate', True))
            result = cur.fetchone()
            conn.commit()
            
            if result:
                print(f"   ✅ Utilisateur test créé (ID: {result[0]})")
            else:
                print("   ⚠️ Utilisateur test@example.com existe déjà")
            
            # Vérifie l'insertion
            cur.execute("SELECT id, email, full_name, created_at FROM users WHERE email = 'test@example.com';")
            user = cur.fetchone()
            print(f"   📊 Utilisateur trouvé : {user}")
        
        # 5. Test insertion dans cvs
        print("\n📄 Test insertion (table cvs) :")
        with conn.cursor() as cur:
            import uuid
            # Récupère l'ID du user test
            cur.execute("SELECT id FROM users WHERE email = 'test@example.com';")
            user_id = cur.fetchone()[0]
            
            cur.execute("""
                INSERT INTO cvs (id, user_id, filename, file_path, extracted_text, file_size_kb, page_count, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id;
            """, (str(uuid.uuid4()), user_id, 'test_cv.pdf', '/uploads/test.pdf', 'Test extraction texte', 1024, 2))
            cv_id = cur.fetchone()[0]
            conn.commit()
            print(f"   ✅ CV test créé (ID: {cv_id})")
        
        # 6. Test insertion dans analyses
        print("\n📊 Test insertion (table analyses) :")
        with conn.cursor() as cur:
            import uuid
            cur.execute("""
                INSERT INTO analyses (
                    id, cv_id, overall_score, structure_score, content_score, keywords_score,
                    detected_skills, missing_skills, strengths, weaknesses, recommendations,
                    sections_detected, word_count, contact_info_found, created_at
                ) VALUES (
                    %s, %s, 75, 80, 70, 75,
                    '["Python", "React"]'::jsonb, '["Docker"]'::jsonb,
                    '["Bonne structure"]'::jsonb, '["Manque détails"]'::jsonb,
                    '["Ajouter plus de projets"]'::jsonb,
                    '{"experience": true, "education": true}'::jsonb, 350, true, NOW()
                ) RETURNING id;
            """, (str(uuid.uuid4()), cv_id))
            analysis_id = cur.fetchone()[0]
            conn.commit()
            print(f"   ✅ Analyse test créée (ID: {analysis_id})")
        
        # 7. Lecture jointe
        print("\n🔗 Test lecture jointe (users + cvs + analyses) :")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    u.email, u.full_name,
                    c.filename, c.file_size_kb,
                    a.overall_score, a.detected_skills
                FROM users u
                LEFT JOIN cvs c ON c.user_id = u.id
                LEFT JOIN analyses a ON a.cv_id = c.id
                WHERE u.email = 'test@example.com';
            """)
            result = cur.fetchone()
            print(f"   📊 Résultat joint :")
            for key, value in result.items():
                print(f"      • {key}: {value}")
        
        # 8. Nettoyage
        print("\n🧹 Nettoyage des données de test :")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM analyses WHERE cv_id IN (SELECT id FROM cvs WHERE filename = 'test_cv.pdf');")
            cur.execute("DELETE FROM cvs WHERE filename = 'test_cv.pdf';")
            cur.execute("DELETE FROM users WHERE email = 'test@example.com';")
            conn.commit()
            print("   ✅ Données de test supprimées")
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS ONT RÉUSSI !")
        print("=" * 60)
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ ERREUR DE CONNEXION : {e}")
        print("\nVérifie :")
        print("   • PostgreSQL est-il démarré ? (services.msc)")
        print("   • Le mot de passe est-il correct ?")
        print(f"   • La base '{url.database}' existe-t-elle ?")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if conn:
            conn.close()
            print("\n🔌 Connexion fermée")

if __name__ == "__main__":
    from app.core.config import settings
    # On lance d'abord les tests async
    asyncio.run(main())
    # Puis le test synchrone avec la même config
    test_connection(settings)