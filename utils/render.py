"""Utility per il rendering dei template Jinja2."""

from fastapi import Request
from fastapi.templating import Jinja2Templates

# Importa i templates da main.py
templates = Jinja2Templates(directory="templates")


def render(
    request: Request,
    template_name: str,
    ctx: dict | None = None,
    user=None,
    status_code: int = 200,
):
    """Helper to render Jinja templates with a consistent context."""
    context = {"request": request, "current_user": user}
    if ctx:
        context.update(ctx)
    return templates.TemplateResponse(request, template_name, context, status_code=status_code)
