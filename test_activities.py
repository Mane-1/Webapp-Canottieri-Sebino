#!/usr/bin/env python3
"""
Test semplice per verificare che i modelli delle attività funzionino
"""

import sys
import os

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models.activities import ActivityType, QualificationType, Activity, ActivityRequirement

def test_models():
    """Test semplice per verificare che i modelli funzionino"""
    print("Test modelli attività...")
    
    try:
        # Crea le tabelle
        Base.metadata.create_all(bind=engine)
        print("✓ Tabelle create con successo")
        
        # Crea una sessione
        db = SessionLocal()
        
        # Test creazione tipi di qualifica
        qual1 = QualificationType(name="Test Qualifica 1", is_active=True)
        qual2 = QualificationType(name="Test Qualifica 2", is_active=True)
        db.add_all([qual1, qual2])
        db.commit()
        print("✓ Tipi di qualifica creati")
        
        # Test creazione tipo di attività
        activity_type = ActivityType(name="Test Attività", color="#ff0000", is_active=True)
        db.add(activity_type)
        db.commit()
        print("✓ Tipo di attività creato")
        
        # Test creazione attività
        from datetime import date, time
        activity = Activity(
            title="Test Attività",
            short_description="Descrizione di test",
            state="bozza",
            type_id=activity_type.id,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        db.add(activity)
        db.commit()
        print("✓ Attività creata")
        
        # Test creazione requisito
        requirement = ActivityRequirement(
            activity_id=activity.id,
            qualification_type_id=qual1.id,
            quantity=2
        )
        db.add(requirement)
        db.commit()
        print("✓ Requisito creato")
        
        # Test query
        activities = db.query(Activity).all()
        print(f"✓ Query attività: {len(activities)} attività trovate")
        
        # Pulisci i dati di test
        db.query(ActivityRequirement).delete()
        db.query(Activity).delete()
        db.query(ActivityType).delete()
        db.query(QualificationType).delete()
        db.commit()
        print("✓ Dati di test puliti")
        
        db.close()
        print("✓ Test completato con successo!")
        
    except Exception as e:
        print(f"✗ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_models()
    sys.exit(0 if success else 1)
