from datetime import date
import models
from datetime import date
import models
import security


def create_role(db, name: str = "atleta"):
    role = models.Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def create_categoria(db, nome: str = "Junior", eta_min: int = 0, eta_max: int = 18, ordine: int = 1):
    categoria = models.Categoria(nome=nome, eta_min=eta_min, eta_max=eta_max, ordine=ordine)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def create_user(db, username: str = "user", roles=None, date_of_birth: date = date(2000, 1, 1)):
    user = models.User(
        username=username,
        hashed_password=security.get_password_hash("password"),
        first_name="Test",
        last_name="User",
        date_of_birth=date_of_birth,
    )
    if roles:
        user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin_user(db, username: str = "admin"):
    admin_role = create_role(db, "admin")
    return create_user(db, username=username, roles=[admin_role])
