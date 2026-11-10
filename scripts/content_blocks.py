"""Validation and LaTeX rendering for author-local prose blocks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from string import Formatter
from urllib.parse import urlparse


ALLOWED_TARGETS = {"cv", "portfolio"}
ALLOWED_STYLES = {"bold", "italic"}
ALLOWED_JOINS = {"space", "none"}
URL_TEMPLATE_FIELDS = {"portfolio_url", "project_id"}


class ContentBlockError(ValueError):
    """Raised when a content block does not match the canonical schema."""


def _error(path: str, message: str) -> ContentBlockError:
    return ContentBlockError(f"{path}: {message}")


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_targets(value: object, path: str) -> None:
    if not isinstance(value, list) or not value:
        raise _error(path, "must be a nonempty list")
    unknown = [target for target in value if target not in ALLOWED_TARGETS]
    if unknown:
        raise _error(path, f"contains unknown target(s): {', '.join(map(str, unknown))}")
    if len(set(value)) != len(value):
        raise _error(path, "must not contain duplicate targets")


def resolve_url(value: object, path: str, url_context: Mapping[str, str] | None = None) -> str:
    if not _nonempty_string(value):
        raise _error(path, "must be a nonempty URL")
    resolved = str(value)
    try:
        fields = {field_name for _, field_name, _, _ in Formatter().parse(resolved) if field_name}
    except ValueError as error:
        raise _error(path, f"contains an invalid URL template: {error}") from error
    unknown_fields = fields - URL_TEMPLATE_FIELDS
    if unknown_fields:
        raise _error(path, f"contains unknown URL template field(s): {', '.join(sorted(unknown_fields))}")
    if fields:
        if url_context is None:
            raise _error(path, "uses URL template fields outside a project")
        missing_fields = fields - set(url_context)
        if missing_fields:
            raise _error(path, f"cannot resolve URL template field(s): {', '.join(sorted(missing_fields))}")
        resolved = resolved.format_map(url_context)

    parsed = urlparse(resolved)
    if parsed.scheme not in {"http", "https", "mailto"}:
        raise _error(path, "must use http, https, or mailto")
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        raise _error(path, "must include a host")
    return resolved


def validate_items(
    items: object,
    path: str = "items",
    url_context: Mapping[str, str] | None = None,
) -> None:
    """Validate a list of content items, including optional nested children."""
    if not isinstance(items, list) or not items:
        raise _error(path, "must be a nonempty list")

    for item_index, item in enumerate(items):
        item_path = f"{path}[{item_index}]"
        if not isinstance(item, Mapping):
            raise _error(item_path, "must be an object")
        allowed_item_fields = {"parts", "targets", "children"}
        unknown_item_fields = set(item) - allowed_item_fields
        if unknown_item_fields:
            raise _error(item_path, f"contains unsupported field(s): {', '.join(sorted(unknown_item_fields))}")
        if "targets" in item:
            validate_targets(item["targets"], f"{item_path}.targets")
        parts = item.get("parts")
        if not isinstance(parts, list) or not parts:
            raise _error(f"{item_path}.parts", "must be a nonempty list")

        after_break = True
        for part_index, part in enumerate(parts):
            part_path = f"{item_path}.parts[{part_index}]"
            if not isinstance(part, Mapping):
                raise _error(part_path, "must be an object")
            part_type = part.get("type")
            if part_type not in {"text", "link", "break"}:
                raise _error(f"{part_path}.type", "must be text, link, or break")

            common_fields = {"type", "targets", "join"}
            if "targets" in part:
                validate_targets(part["targets"], f"{part_path}.targets")
            if "join" in part and part["join"] not in ALLOWED_JOINS:
                raise _error(f"{part_path}.join", "must be space or none")

            if part_type == "break":
                unknown = set(part) - {"type"}
                if unknown:
                    raise _error(part_path, f"break contains unrelated field(s): {', '.join(sorted(unknown))}")
                after_break = True
                continue

            allowed = common_fields | {"styles"}
            required = "value" if part_type == "text" else "label"
            allowed.add(required)
            if part_type == "link":
                allowed.add("url")
            unknown = set(part) - allowed
            if unknown:
                raise _error(part_path, f"contains unsupported field(s): {', '.join(sorted(unknown))}")
            if not _nonempty_string(part.get(required)):
                raise _error(f"{part_path}.{required}", "must be nonempty")
            text = part[required]
            if text != text.strip():
                raise _error(f"{part_path}.{required}", "must not have leading or trailing whitespace")
            if part_type == "link":
                resolve_url(part.get("url"), f"{part_path}.url", url_context)
            if "styles" in part:
                styles = part["styles"]
                if not isinstance(styles, list) or not styles:
                    raise _error(f"{part_path}.styles", "must be a nonempty list")
                invalid_styles = [style for style in styles if style not in ALLOWED_STYLES]
                if invalid_styles:
                    raise _error(f"{part_path}.styles", f"contains invalid style(s): {', '.join(map(str, invalid_styles))}")
                if len(set(styles)) != len(styles):
                    raise _error(f"{part_path}.styles", "must not contain duplicates")
            after_break = False

        if after_break:
            raise _error(f"{item_path}.parts", "must not end with a break")
        if "children" in item:
            validate_items(item["children"], f"{item_path}.children", url_context)


def escape_latex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def _applies_to(part: Mapping[str, object], destination: str) -> bool:
    return destination in part.get("targets", ALLOWED_TARGETS)


def render_latex_parts(
    parts: Sequence[Mapping[str, object]],
    destination: str = "cv",
    link_color: str | None = None,
    url_context: Mapping[str, str] | None = None,
) -> str:
    """Render validated parts, escaping text before adding modeled markup."""
    rendered: list[str] = []
    at_line_start = True
    for part in parts:
        if not _applies_to(part, destination):
            continue
        if part["type"] == "break":
            rendered.append(r" \\")
            at_line_start = True
            continue
        separator = "" if at_line_start or part.get("join", "space") == "none" else " "
        label_field = "value" if part["type"] == "text" else "label"
        value = escape_latex(str(part[label_field]))
        if part["type"] == "link" and link_color:
            value = rf"\textcolor{{{link_color}}}{{{value}}}"
        for style in reversed(part.get("styles", [])):
            command = "textbf" if style == "bold" else "textit"
            value = rf"\{command}{{{value}}}"
        if part["type"] == "link":
            url = resolve_url(part["url"], "link.url", url_context)
            value = rf"\href{{{escape_latex(url)}}}{{{value}}}"
        rendered.append(separator + value)
        at_line_start = False
    return "".join(rendered)
