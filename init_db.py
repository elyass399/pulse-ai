#!/usr/bin/env python3
"""
Inizializza il database Pulse.
"""

from app.database import engine, Base

# 🔴 CRITICO: importa i modelli PRIMA di create_all()
# altrimenti SQLAlchemy non sa quali tabelle creare
from app.models import Briefing, UserPreference  # noqa: F401

Base.metadata.create_all(bind=engine)

print("✅ Database e tabelle create con successo!")