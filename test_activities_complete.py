#!/usr/bin/env python3
"""
Test completo per la sezione Attività
Verifica tutti i miglioramenti implementati
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, time, datetime
from decimal import Decimal

from main import app
from database import get_db
from models import (
    Activity, ActivityType, QualificationType, ActivityRequirement, 
    ActivityAssignment, UserQualification, User, Role
)
from tests.conftest import TestingSessionLocal


@pytest.fixture
def client():
    """Client di test."""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def db():
    """Database di test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db):
    """Utente di test con ruolo admin."""
    user = User(
        username="testadmin",
        email="admin@test.com",
        first_name="Admin",
        last_name="Test",
        is_active=True,
        is_admin=True,
        is_allenatore=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_activity_type(db):
    """Tipo di attività di test."""
    activity_type = ActivityType(
        name="Test Activity",
        color="#007BFF",
        is_active=True
    )
    db.add(activity_type)
    db.commit()
    db.refresh(activity_type)
    return activity_type


@pytest.fixture
def test_qualification_type(db):
    """Tipo di qualifica di test."""
    qualification_type = QualificationType(
        name="Test Qualification",
        is_active=True
    )
    db.add(qualification_type)
    db.commit()
    db.refresh(qualification_type)
    return qualification_type


@pytest.fixture
def test_activity(db, test_activity_type):
    """Attività di test."""
    activity = Activity(
        title="Test Activity",
        short_description="Test Description",
        state="confermato",
        type_id=test_activity_type.id,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(12, 0),
        customer_name="Test Customer",
        customer_email="customer@test.com",
        participants_plan=10,
        payment_amount=Decimal("100.00"),
        payment_state="da_effettuare"
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@pytest.fixture
def test_requirement(db, test_activity, test_qualification_type):
    """Requisito di test."""
    requirement = ActivityRequirement(
        activity_id=test_activity.id,
        qualification_type_id=test_qualification_type.id,
        quantity=2
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


class TestActivitiesSection:
    """Test per la sezione Attività."""
    
    def test_calendar_page_loads(self, client, test_user):
        """Test che la pagina calendario si carichi correttamente."""
        # Simula login
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        response = client.get("/attivita/calendario")
        assert response.status_code == 200
        assert "Calendario Attività" in response.text
        assert "Canottieri Sebino" in response.text  # Verifica che il navbar sia presente
    
    def test_management_page_loads(self, client, test_user):
        """Test che la pagina gestione si carichi correttamente."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        response = client.get("/attivita/gestione")
        assert response.status_code == 200
        assert "Gestione Attività" in response.text
        assert "Canottieri Sebino" in response.text
    
    def test_filters_work_correctly(self, client, test_user, db, test_activity):
        """Test che i filtri funzionino correttamente."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        # Test filtro per tipo
        response = client.get(f"/attivita/gestione?type_id={test_activity.type_id}")
        assert response.status_code == 200
        assert test_activity.title in response.text
        
        # Test filtro per stato
        response = client.get(f"/attivita/gestione?state={test_activity.state}")
        assert response.status_code == 200
        assert test_activity.title in response.text
        
        # Test filtro per data
        today = date.today().strftime("%Y-%m-%d")
        response = client.get(f"/attivita/gestione?date_from={today}&date_to={today}")
        assert response.status_code == 200
        assert test_activity.title in response.text
    
    def test_api_activities_endpoint(self, client, test_user, db, test_activity):
        """Test che l'endpoint API delle attività funzioni."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        response = client.get("/api/attivita")
        assert response.status_code == 200
        
        activities = response.json()
        assert len(activities) > 0
        assert any(a["id"] == test_activity.id for a in activities)
    
    def test_available_instructors_endpoint(self, client, test_user, db, test_activity, test_requirement):
        """Test che l'endpoint per istruttori disponibili funzioni."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        response = client.get(f"/api/attivita/{test_activity.id}/available-instructors?requirement_id={test_requirement.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "instructors" in data
        assert "conflicts" in data
    
    def test_assign_instructor_endpoint(self, client, test_user, db, test_activity, test_requirement):
        """Test che l'endpoint per assegnare istruttori funzioni."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        # Prima crea una qualifica per l'utente
        user_qualification = UserQualification(
            user_id=test_user.id,
            qualification_type_id=test_requirement.qualification_type_id
        )
        db.add(user_qualification)
        db.commit()
        
        response = client.post(
            f"/api/attivita/{test_activity.id}/assign-instructor",
            json={
                "instructor_id": test_user.id,
                "requirement_id": test_requirement.id
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
    
    def test_activity_modal_structure(self, client, test_user):
        """Test che il modal delle attività abbia la struttura corretta."""
        with client.session_transaction() as session:
            session["user_id"] = test_user.id
        
        response = client.get("/attivita/calendario")
        assert response.status_code == 200
        
        # Verifica che il modal sia presente
        assert "activityModal" in response.text
        assert "assignInstructorModal" in response.text
        
        # Verifica che le tab siano presenti
        assert "generale-tab" in response.text
        assert "copertura-tab" in response.text
        assert "risorse-tab" in response.text
        assert "pagamento-tab" in response.text
    
    def test_coverage_calculation(self, db, test_activity, test_requirement):
        """Test che il calcolo della copertura funzioni correttamente."""
        from services.availability import compute_activity_coverage
        
        assigned, required, percent = compute_activity_coverage(db, test_activity.id)
        
        assert required == test_requirement.quantity
        assert assigned == 0
        assert percent == 0.0
        
        # Assegna un istruttore
        assignment = ActivityAssignment(
            activity_id=test_activity.id,
            user_id=1,  # ID utente di test
            requirement_id=test_requirement.id,
            hours=3
        )
        db.add(assignment)
        db.commit()
        
        assigned, required, percent = compute_activity_coverage(db, test_activity.id)
        assert assigned == 1
        assert required == test_requirement.quantity
        assert percent == 50.0  # 1/2 = 50%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
