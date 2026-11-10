"""Load and validate the canonical portfolio/CV profile."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from urllib.parse import urldefrag

import yaml

try:
    from .content_blocks import ContentBlockError, resolve_url, validate_items, validate_targets
except ImportError:
    from content_blocks import ContentBlockError, resolve_url, validate_items, validate_targets


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.yaml"
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGACY_FIELDS = {
    "summary", "introduction", "portfolio_link", "featured_publication_id",
    "achievements", "description", "emphasis", "link_id", "link_ids",
    "portfolio_anchor_label", "url_ref",
}


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            line = key_node.start_mark.line + 1
            raise ContentBlockError(f"profile.yaml:{line}: duplicate key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_profile_data(path: Path = PROFILE_PATH) -> dict:
    try:
        profile = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        raise ContentBlockError(f"{path.name}: invalid YAML: {error}") from error
    validate_profile(profile)
    return profile


def _error(path: str, message: str) -> ContentBlockError:
    return ContentBlockError(f"{path}: {message}")


def _mapping(value: object, path: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise _error(path, "must be an object")
    return value


def _list(value: object, path: str) -> list:
    if not isinstance(value, list):
        raise _error(path, "must be a list")
    return value


def _string(value: object, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(path, "must be a nonempty string")
    if value != value.strip():
        raise _error(path, "must not have leading or trailing whitespace")
    return value


def _record_id(record: Mapping, path: str, seen_ids: dict[str, str]) -> str:
    record_id = _string(record.get("id"), f"{path}.id")
    if not ID_PATTERN.fullmatch(record_id):
        raise _error(f"{path}.id", "must contain lowercase letters, numbers, and single hyphens")
    if record_id in seen_ids:
        raise _error(f"{path}.id", f"duplicates {seen_ids[record_id]}")
    seen_ids[record_id] = f"{path}.id"
    return record_id


def _destination_value(record: Mapping, destination: str, field: str) -> object:
    override = record.get(destination, {})
    if isinstance(override, Mapping) and field in override:
        return override[field]
    return record.get(field)


def _url_context(portfolio_url: str, project_id: str | None = None) -> dict[str, str]:
    context = {"portfolio_url": portfolio_url}
    if project_id is not None:
        context["project_id"] = project_id
    return context


def _iter_links(items: list):
    for item in items:
        for part in item["parts"]:
            if part["type"] == "link":
                yield part
        yield from _iter_links(item.get("children", []))


def reject_legacy_fields(value: object, path: str = "profile") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in LEGACY_FIELDS:
                raise _error(child_path, "legacy prose field is not allowed; use items/parts")
            reject_legacy_fields(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_legacy_fields(child, f"{path}[{index}]")


def validate_profile(profile: object) -> None:
    profile = _mapping(profile, "profile")
    if profile.get("schema_version") != 2:
        raise _error("schema_version", "must be 2")
    reject_legacy_fields(profile)

    settings = _mapping(profile.get("settings"), "settings")
    portfolio_url = resolve_url(settings.get("portfolio_url"), "settings.portfolio_url")
    resume_filename = _string(settings.get("resume_filename"), "settings.resume_filename")
    resume_path = Path(resume_filename)
    if (
        resume_path.is_absolute()
        or not resume_path.parts
        or ".." in resume_path.parts
        or resume_path.suffix.lower() != ".pdf"
    ):
        raise _error(
            "settings.resume_filename",
            "must be a relative PDF path inside the repository root",
        )
    page_limit = settings.get("cv_page_limit")
    if not isinstance(page_limit, int) or page_limit < 1:
        raise _error("settings.cv_page_limit", "must be a positive integer")

    seen_ids: dict[str, str] = {}
    person = _mapping(profile.get("person"), "person")
    validate_targets(person.get("targets"), "person.targets")
    _string(person.get("name"), "person.name")
    _string(person.get("title"), "person.title")

    portfolio_email_count = 0
    for index, value in enumerate(_list(person.get("contacts"), "person.contacts")):
        path = f"person.contacts[{index}]"
        contact = _mapping(value, path)
        _record_id(contact, path, seen_ids)
        validate_targets(contact.get("targets"), f"{path}.targets")
        contact_type = _string(contact.get("type"), f"{path}.type")
        _string(contact.get("label"), f"{path}.label")
        _string(contact.get("value"), f"{path}.value")
        if contact_type == "email" and "portfolio" in contact["targets"]:
            portfolio_email_count += 1
    if portfolio_email_count != 1:
        raise _error("person.contacts", "must contain exactly one portfolio email")

    for index, value in enumerate(_list(person.get("links"), "person.links")):
        path = f"person.links[{index}]"
        link = _mapping(value, path)
        _record_id(link, path, seen_ids)
        validate_targets(link.get("targets"), f"{path}.targets")
        _string(link.get("label"), f"{path}.label")
        resolve_url(link.get("url"), f"{path}.url")

    about = _mapping(profile.get("about"), "about")
    validate_targets(about.get("targets"), "about.targets")
    for destination in ("cv", "portfolio"):
        block = _mapping(about.get(destination), f"about.{destination}")
        validate_items(block.get("items"), f"about.{destination}.items", _url_context(portfolio_url))

    for index, value in enumerate(_list(profile.get("education"), "education")):
        path = f"education[{index}]"
        record = _mapping(value, path)
        _record_id(record, path, seen_ids)
        validate_targets(record.get("targets"), f"{path}.targets")
        _string(record.get("institution"), f"{path}.institution")
        _string(record.get("degree"), f"{path}.degree")
        if "cv" in record["targets"]:
            _string(record.get("location"), f"{path}.location")
        for destination in record["targets"]:
            _string(_destination_value(record, destination, "institution"), f"{path}.{destination}.institution")
            _string(_destination_value(record, destination, "degree"), f"{path}.{destination}.degree")
            _string(_destination_value(record, destination, "dates"), f"{path}.{destination}.dates")

    for index, value in enumerate(_list(profile.get("experience"), "experience")):
        path = f"experience[{index}]"
        record = _mapping(value, path)
        _record_id(record, path, seen_ids)
        validate_targets(record.get("targets"), f"{path}.targets")
        _string(record.get("company"), f"{path}.company")
        _string(record.get("role"), f"{path}.role")
        if "cv" in record["targets"]:
            _string(record.get("location"), f"{path}.location")
        for destination in record["targets"]:
            _string(_destination_value(record, destination, "company"), f"{path}.{destination}.company")
            _string(_destination_value(record, destination, "role"), f"{path}.{destination}.role")
            _string(_destination_value(record, destination, "dates"), f"{path}.{destination}.dates")
            validate_items(
                _destination_value(record, destination, "items"),
                f"{path}.{destination}.items",
                _url_context(portfolio_url),
            )

    project_ids: set[str] = set()
    project_links: list[tuple[str, str]] = []
    for index, value in enumerate(_list(profile.get("projects"), "projects")):
        path = f"projects[{index}]"
        record = _mapping(value, path)
        project_id = _record_id(record, path, seen_ids)
        project_ids.add(project_id)
        validate_targets(record.get("targets"), f"{path}.targets")
        _string(record.get("title"), f"{path}.title")
        for tech_index, technology in enumerate(_list(record.get("technologies"), f"{path}.technologies")):
            _string(technology, f"{path}.technologies[{tech_index}]")
        context = _url_context(portfolio_url, project_id)
        for destination in record["targets"]:
            _string(_destination_value(record, destination, "title"), f"{path}.{destination}.title")
            if destination == "cv":
                _string(_destination_value(record, destination, "dates"), f"{path}.cv.dates")
            items = _destination_value(record, destination, "items")
            validate_items(items, f"{path}.{destination}.items", context)
            for part in _iter_links(items):
                project_links.append((
                    f"{path}.{destination}.items",
                    resolve_url(part["url"], f"{path}.link.url", context),
                ))
        cv_block = record.get("cv", {})
        if isinstance(cv_block, Mapping) and "order" in cv_block:
            if not isinstance(cv_block["order"], int) or cv_block["order"] < 0:
                raise _error(f"{path}.cv.order", "must be a nonnegative integer")
        media_items = _destination_value(record, "portfolio", "media") or []
        for media_index, media_value in enumerate(media_items):
            media_path = f"{path}.portfolio.media[{media_index}]"
            media = _mapping(media_value, media_path)
            if media.get("type") != "video":
                raise _error(f"{media_path}.type", "must be video")
            _string(media.get("label"), f"{media_path}.label")
            resolve_url(media.get("url"), f"{media_path}.url")

    portfolio_base = urldefrag(portfolio_url).url.rstrip("/")
    for path, url in project_links:
        base, fragment = urldefrag(url)
        if base.rstrip("/") == portfolio_base and fragment and fragment not in project_ids:
            raise _error(path, f"links to unknown portfolio project id: {fragment}")

    for index, value in enumerate(_list(profile.get("skills"), "skills")):
        path = f"skills[{index}]"
        record = _mapping(value, path)
        _record_id(record, path, seen_ids)
        validate_targets(record.get("targets"), f"{path}.targets")
        _string(record.get("title"), f"{path}.title")
        for item_index, item in enumerate(_list(record.get("items"), f"{path}.items")):
            _string(item, f"{path}.items[{item_index}]")

    for index, value in enumerate(_list(profile.get("certifications"), "certifications")):
        path = f"certifications[{index}]"
        record = _mapping(value, path)
        _record_id(record, path, seen_ids)
        validate_targets(record.get("targets"), f"{path}.targets")
        for field in ("title", "issuer", "date"):
            _string(record.get(field), f"{path}.{field}")
        resolve_url(record.get("link"), f"{path}.link")


def main() -> None:
    load_profile_data()
    print(f"Validated {PROFILE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
