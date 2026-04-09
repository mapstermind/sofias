"""Model introspection utilities for dynamic field prompting."""

from dataclasses import dataclass, field
from typing import Any

from django.db import models

from .prompts import ask, ask_bool, ask_int, choose

SKIP_FIELDS = {"id", "created_at", "updated_at", "published_at", "started_at", "completed_at"}


@dataclass
class FieldSpec:
    name: str
    verbose_name: str
    field_type: str  # char/text/int/bool/choices/json
    required: bool
    default: Any = None
    choices: list[tuple[str, str]] = field(default_factory=list)


def _field_type(f: models.Field) -> str:
    if getattr(f, "choices", None):
        return "choices"
    if isinstance(f, (models.CharField, models.TextField)):
        return "text"
    if isinstance(f, (models.PositiveIntegerField, models.IntegerField)):
        return "int"
    if isinstance(f, models.BooleanField):
        return "bool"
    if isinstance(f, models.JSONField):
        return "json"
    return "text"


def _is_required(f: models.Field) -> bool:
    return not (getattr(f, "blank", False) or getattr(f, "null", False) or f.has_default())


def get_promptable_fields(model_class: type) -> list[FieldSpec]:
    specs = []
    for f in model_class._meta.get_fields():
        if not isinstance(f, models.Field):
            continue
        if f.name in SKIP_FIELDS:
            continue
        if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
            continue
        if isinstance(f, models.JSONField):
            continue
        if f.is_relation:
            continue
        ft = _field_type(f)
        default = f.default if f.has_default() else None
        if default is models.fields.NOT_PROVIDED:
            default = None
        choices = list(f.choices) if getattr(f, "choices", None) else []
        specs.append(FieldSpec(
            name=f.name,
            verbose_name=str(f.verbose_name).capitalize(),
            field_type=ft,
            required=_is_required(f),
            default=default,
            choices=choices,
        ))
    return specs


def prompt_for_model(model_class: type, exclude: list[str] | None = None) -> dict[str, Any]:
    exclude_set = set(exclude or [])
    data: dict[str, Any] = {}
    for spec in get_promptable_fields(model_class):
        if spec.name in exclude_set:
            continue
        if spec.field_type == "choices":
            options = [(label, value) for value, label in spec.choices]
            data[spec.name] = choose(spec.verbose_name, options)
        elif spec.field_type == "bool":
            default_bool = spec.default if isinstance(spec.default, bool) else True
            data[spec.name] = ask_bool(spec.verbose_name, default=default_bool)
        elif spec.field_type == "int":
            default_int = spec.default if isinstance(spec.default, int) else None
            data[spec.name] = ask_int(spec.verbose_name, default=default_int, required=spec.required)
        else:
            default_str = str(spec.default) if spec.default not in (None, "") else None
            value = ask(spec.verbose_name, default=default_str, required=spec.required)
            data[spec.name] = value
    return data
