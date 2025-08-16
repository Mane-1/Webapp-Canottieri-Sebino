from __future__ import annotations
from pydantic import BaseModel
from fastapi import Form

class LoginInput(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...),
    ) -> "LoginInput":
        return cls(username=username, password=password)
