from app.database import engine, Base

# Crea tutte le tabelle
Base.metadata.create_all(bind=engine)

print("✅ Database e tabelle create con successo!")