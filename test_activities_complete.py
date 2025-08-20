#!/usr/bin/env python3
"""
Test completo per la macro-sezione Attività
Verifica tutti i modelli, servizi e funzionalità implementate
"""

import sys
import os
from datetime import date, time, datetime
from decimal import Decimal

# Aggiungi il percorso del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import User, Role
from models.activities import (
    ActivityType, QualificationType, Activity, UserQualification,
    ActivityRequirement, ActivityAssignment, ActivityState, 
    PaymentMethod, PaymentState
)
from services.availability import (
    has_time_conflict, compute_activity_coverage,
    get_available_users_for_requirement, can_user_self_assign,
    get_user_activity_hours
)

def test_database_creation():
    """Test creazione tabelle database"""
    print("🔧 Test creazione tabelle database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle create con successo")
        return True
    except Exception as e:
        print(f"❌ Errore creazione tabelle: {e}")
        return False

def test_models_creation():
    """Test creazione modelli base"""
    print("\n🏗️ Test creazione modelli base...")
    
    try:
        # Test ActivityType
        activity_type = ActivityType(
            name="Test Kayak",
            color="#FF5733",
            is_active=True
        )
        print("✅ ActivityType creato")
        
        # Test QualificationType
        qual_type = QualificationType(
            name="Test Istruttore",
            is_active=True
        )
        print("✅ QualificationType creato")
        
        # Test Activity
        activity = Activity(
            title="Test Attività",
            short_description="Descrizione test",
            state=ActivityState.bozza,
            type_id=1,  # Verrà aggiornato dopo l'inserimento
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            customer_name="Cliente Test",
            customer_email="test@example.com",
            participants_plan=10,
            payment_amount=Decimal("150.00"),
            payment_method=PaymentMethod.bonifico,
            payment_state=PaymentState.da_effettuare
        )
        print("✅ Activity creato")
        
        return True
    except Exception as e:
        print(f"❌ Errore creazione modelli: {e}")
        return False

def test_database_operations():
    """Test operazioni database"""
    print("\n💾 Test operazioni database...")
    
    db = SessionLocal()
    try:
        # Inserimento dati di test
        print("📝 Inserimento dati di test...")
        
        # 1. Creazione tipi di attività
        kayak_type = ActivityType(name="Corso Kayak", color="#007BFF", is_active=True)
        teambuilding_type = ActivityType(name="Teambuilding", color="#28A745", is_active=True)
        db.add_all([kayak_type, teambuilding_type])
        db.commit()
        db.refresh(kayak_type)
        db.refresh(teambuilding_type)
        print(f"✅ Tipi attività creati: {kayak_type.id}, {teambuilding_type.id}")
        
        # 2. Creazione tipi di qualifica
        istruttore_qual = QualificationType(name="Istruttore Kayak", is_active=True)
        autista_qual = QualificationType(name="Autista Gommone", is_active=True)
        db.add_all([istruttore_qual, autista_qual])
        db.commit()
        db.refresh(istruttore_qual)
        db.refresh(autista_qual)
        print(f"✅ Tipi qualifica creati: {istruttore_qual.id}, {autista_qual.id}")
        
        # 3. Creazione attività
        activity1 = Activity(
            title="Corso Kayak Principianti",
            short_description="Corso base per principianti",
            state=ActivityState.confermato,
            type_id=kayak_type.id,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            customer_name="Scuola Test",
            customer_email="scuola@test.com",
            participants_plan=8,
            payment_amount=Decimal("200.00"),
            payment_method=PaymentMethod.bonifico,
            payment_state=PaymentState.da_effettuare
        )
        
        activity2 = Activity(
            title="Teambuilding Aziendale",
            short_description="Attività di team building",
            state=ActivityState.bozza,
            type_id=teambuilding_type.id,
            date=date.today(),
            start_time=time(14, 0),
            end_time=time(18, 0),
            customer_name="Azienda Test",
            customer_email="azienda@test.com",
            participants_plan=15,
            payment_amount=Decimal("500.00"),
            payment_method=PaymentMethod.carta,
            payment_state=PaymentState.da_verificare
        )
        
        db.add_all([activity1, activity2])
        db.commit()
        db.refresh(activity1)
        db.refresh(activity2)
        print(f"✅ Attività create: {activity1.id}, {activity2.id}")
        
        # 4. Creazione requisiti
        req1 = ActivityRequirement(
            activity_id=activity1.id,
            qualification_type_id=istruttore_qual.id,
            quantity=2
        )
        
        req2 = ActivityRequirement(
            activity_id=activity1.id,
            qualification_type_id=autista_qual.id,
            quantity=1
        )
        
        req3 = ActivityRequirement(
            activity_id=activity2.id,
            qualification_type_id=istruttore_qual.id,
            quantity=3
        )
        
        db.add_all([req1, req2, req3])
        db.commit()
        print("✅ Requisiti creati")
        
        # 5. Test query e relazioni
        print("\n🔍 Test query e relazioni...")
        
        # Query attività con requisiti
        activity_with_reqs = db.query(Activity).options(
            db.joinedload(Activity.requirements).joinedload(ActivityRequirement.qualification_type)
        ).filter(Activity.id == activity1.id).first()
        
        print(f"📋 Attività '{activity_with_reqs.title}' ha {len(activity_with_reqs.requirements)} requisiti:")
        for req in activity_with_reqs.requirements:
            print(f"   - {req.qualification_type.name}: {req.quantity}")
        
        # Test calcolo copertura
        coverage = compute_activity_coverage(db, activity1.id)
        print(f"📊 Copertura attività {activity1.id}: {coverage[2]}% ({coverage[1]}/{coverage[0]})")
        
        return True, {
            'kayak_type_id': kayak_type.id,
            'teambuilding_type_id': teambuilding_type.id,
            'istruttore_qual_id': istruttore_qual.id,
            'autista_qual_id': autista_qual.id,
            'activity1_id': activity1.id,
            'activity2_id': activity2.id
        }
        
    except Exception as e:
        print(f"❌ Errore operazioni database: {e}")
        db.rollback()
        return False, None
    finally:
        db.close()

def test_services():
    """Test servizi di business logic"""
    print("\n⚙️ Test servizi di business logic...")
    
    db = SessionLocal()
    try:
        # Test has_time_conflict
        print("⏰ Test controllo conflitti orari...")
        start_dt = datetime.combine(date.today(), time(9, 0))
        end_dt = datetime.combine(date.today(), time(12, 0))
        
        # Test con utente inesistente (dovrebbe restituire False)
        conflict = has_time_conflict(db, 999, start_dt, end_dt)
        print(f"✅ Controllo conflitti: {conflict}")
        
        # Test compute_activity_coverage
        print("📊 Test calcolo copertura...")
        activities = db.query(Activity).limit(2).all()
        for activity in activities:
            coverage = compute_activity_coverage(db, activity.id)
            print(f"   - Attività {activity.id}: {coverage[2]}% copertura")
        
        # Test get_available_users_for_requirement
        print("👥 Test utenti disponibili...")
        requirements = db.query(ActivityRequirement).limit(2).all()
        for req in requirements:
            available_users = get_available_users_for_requirement(db, req.id, req.activity_id, [])
            print(f"   - Requisito {req.id}: {len(available_users)} utenti disponibili")
        
        print("✅ Tutti i servizi testati con successo")
        return True
        
    except Exception as e:
        print(f"❌ Errore test servizi: {e}")
        return False
    finally:
        db.close()

def test_user_qualifications():
    """Test gestione qualifiche utenti"""
    print("\n👤 Test gestione qualifiche utenti...")
    
    db = SessionLocal()
    try:
        # Cerca utenti esistenti
        users = db.query(User).limit(3).all()
        if not users:
            print("⚠️ Nessun utente trovato per il test")
            return False
        
        # Cerca tipi di qualifica
        qual_types = db.query(QualificationType).limit(2).all()
        if not qual_types:
            print("⚠️ Nessun tipo di qualifica trovato per il test")
            return False
        
        # Assegna qualifiche di test
        print("🎯 Assegnazione qualifiche di test...")
        for i, user in enumerate(users):
            if i < len(qual_types):
                qual = qual_types[i]
                user_qual = UserQualification(
                    user_id=user.id,
                    qualification_type_id=qual.id
                )
                db.add(user_qual)
                print(f"   - Utente {user.username} -> {qual.name}")
        
        db.commit()
        print("✅ Qualifiche assegnate")
        
        # Test query qualifiche
        user_with_quals = db.query(User).options(
            db.joinedload(User.qualifications).joinedload(UserQualification.qualification_type)
        ).first()
        
        if user_with_quals and user_with_quals.qualifications:
            print(f"👤 Utente {user_with_quals.username} ha {len(user_with_quals.qualifications)} qualifiche:")
            for uq in user_with_quals.qualifications:
                print(f"   - {uq.qualification_type.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test qualifiche: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_activity_assignments():
    """Test assegnazioni attività"""
    print("\n📋 Test assegnazioni attività...")
    
    db = SessionLocal()
    try:
        # Cerca attività e requisiti
        activity = db.query(Activity).first()
        requirement = db.query(ActivityRequirement).first()
        user = db.query(User).first()
        
        if not all([activity, requirement, user]):
            print("⚠️ Dati insufficienti per test assegnazioni")
            return False
        
        # Crea assegnazione di test
        assignment = ActivityAssignment(
            activity_id=activity.id,
            requirement_id=requirement.id,
            user_id=user.id,
            role_label="Istruttore Principale",
            hours=3.0
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        print(f"✅ Assegnazione creata: ID {assignment.id}")
        
        # Test query assegnazioni
        activity_with_assignments = db.query(Activity).options(
            db.joinedload(Activity.assignments).joinedload(ActivityAssignment.user)
        ).filter(Activity.id == activity.id).first()
        
        print(f"📋 Attività '{activity_with_assignments.title}' ha {len(activity_with_assignments.assignments)} assegnazioni:")
        for ass in activity_with_assignments.assignments:
            print(f"   - {ass.user.full_name}: {ass.role_label} ({ass.hours}h)")
        
        # Test ricalcolo copertura
        coverage = compute_activity_coverage(db, activity.id)
        print(f"📊 Nuova copertura: {coverage[2]}% ({coverage[1]}/{coverage[0]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test assegnazioni: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def cleanup_test_data():
    """Pulizia dati di test"""
    print("\n🧹 Pulizia dati di test...")
    
    db = SessionLocal()
    try:
        # Elimina in ordine per rispettare i vincoli FK
        db.query(ActivityAssignment).delete()
        db.query(ActivityRequirement).delete()
        db.query(UserQualification).delete()
        db.query(Activity).delete()
        db.query(ActivityType).delete()
        db.query(QualificationType).delete()
        
        db.commit()
        print("✅ Dati di test eliminati")
        return True
        
    except Exception as e:
        print(f"❌ Errore pulizia: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Esegue tutti i test"""
    print("🚀 AVVIO TEST COMPLETO MACRO-SEZIONE ATTIVITÀ")
    print("=" * 60)
    
    # Test sequenziali
    tests = [
        ("Creazione Database", test_database_creation),
        ("Modelli Base", test_models_creation),
        ("Operazioni Database", test_database_operations),
        ("Servizi Business Logic", test_services),
        ("Qualifiche Utenti", test_user_qualifications),
        ("Assegnazioni Attività", test_activity_assignments),
    ]
    
    results = []
    test_data = None
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "Operazioni Database":
                success, test_data = test_func()
            else:
                success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Errore durante {test_name}: {e}")
            results.append((test_name, False))
    
    # Riepilogo risultati
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO TEST")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Risultato: {passed}/{total} test superati")
    
    if passed == total:
        print("🎉 TUTTI I TEST SUPERATI! La macro-sezione Attività è pronta.")
    else:
        print("⚠️ Alcuni test sono falliti. Controllare gli errori sopra.")
    
    # Pulizia finale
    if test_data:
        print("\n🧹 Pulizia finale...")
        cleanup_test_data()
    
    print("\n🏁 Test completato!")

if __name__ == "__main__":
    main()
