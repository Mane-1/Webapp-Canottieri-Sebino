from datetime import date, timedelta
import pytest
import models
from factories import create_role, create_user, create_categoria


def test_user_roles_and_category(db_session):
    admin_role = create_role(db_session, "admin")
    coach_role = create_role(db_session, "allenatore")
    atleta_role = create_role(db_session, "atleta")
    categoria = create_categoria(db_session, nome="Junior", eta_min=10, eta_max=18)

    birth = date.today() - timedelta(days=15 * 365)
    user = create_user(db_session, roles=[admin_role, coach_role, atleta_role], date_of_birth=birth)

    assert user.is_admin
    assert user.is_allenatore
    assert user.category == "Junior"

    user.manual_category = "NonEsistente"
    assert user.category == "Junior"
    user.manual_category = "Junior"
    assert user.category == "Junior"

    categoria2 = create_categoria(db_session, nome="Senior", eta_min=19, eta_max=40)
    birth2 = date.today() - timedelta(days=20 * 365)
    user2 = create_user(db_session, username="u2", roles=[atleta_role], date_of_birth=birth2)
    assert user2.category == "Senior"
