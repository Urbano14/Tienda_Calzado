from __future__ import annotations

import uuid
from typing import Optional, Type

from django.db import models
from django.utils.text import slugify


def build_unique_slug(
    model_class: Type[models.Model],
    label: str,
    current_pk: Optional[int] = None,
    slug_field: str = "slug",
) -> str:
    """Return a slug derived from *label* that is unique for ``model_class``."""

    base_slug = slugify(label) or f"item-{uuid.uuid4().hex[:8]}"
    slug_candidate = base_slug
    suffix = 1

    query = model_class.objects
    if current_pk is not None:
        query = query.exclude(pk=current_pk)

    while query.filter(**{slug_field: slug_candidate}).exists():
        suffix += 1
        slug_candidate = f"{base_slug}-{suffix}"

    return slug_candidate
