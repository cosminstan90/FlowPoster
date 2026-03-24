"""
CMS adapter factory.

Usage::

    adapter = get_adapter(project)
    result  = await adapter.publish(page)
"""
from __future__ import annotations

from fastapi import HTTPException

from backend.models.project import Project
from backend.services.cms.base_adapter import PublishAdapter
from backend.services.cms.php_custom import PHPCustomAdapter
from backend.services.cms.wordpress import WordPressAdapter


def get_adapter(project: Project) -> PublishAdapter:
    config = project.cms_config or {}
    if project.cms_type == "wordpress":
        _require_keys(config, ["url", "username", "app_password"], "WordPress")
        return WordPressAdapter(config)
    elif project.cms_type == "php_custom":
        _require_keys(config, ["endpoint_url", "secret_token"], "PHP Custom")
        return PHPCustomAdapter(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown CMS type: {project.cms_type}")


def _require_keys(config: dict, keys: list[str], adapter_name: str) -> None:
    missing = [k for k in keys if not config.get(k)]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"{adapter_name} config missing required keys: {missing}",
        )
