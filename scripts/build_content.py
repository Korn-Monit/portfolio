"""Generate the portfolio data, complete LaTeX CV, and optional PDF."""

from __future__ import annotations

import argparse
from copy import deepcopy
import filecmp
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pypdf import PdfReader

try:
    from .content_blocks import escape_latex, render_latex_parts, resolve_url
    from .validate_profile import load_profile_data
except ImportError:
    from content_blocks import escape_latex, render_latex_parts, resolve_url
    from validate_profile import load_profile_data


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.yaml"
PORTFOLIO_PATH = ROOT / "generated" / "profile.js"
CV_DIRECTORY = ROOT / "cv"
CV_TEMPLATE_PATH = CV_DIRECTORY / "main.tex.j2"
CV_PATH = CV_DIRECTORY / "main.tex"
CV_PDF_PATH = CV_PATH.with_suffix(".pdf")


def targets(record: dict[str, Any], destination: str) -> bool:
    return destination in record.get("targets", [])


def destination_value(record: dict[str, Any], destination: str, field: str, default: Any = None) -> Any:
    override = record.get(destination, {})
    if field in override:
        return override[field]
    return record.get(field, default)


def destination_items(
    items: list[dict[str, Any]],
    destination: str,
    url_context: dict[str, str],
) -> list[dict[str, Any]]:
    """Filter nested targets and resolve URL templates for one output."""
    resolved: list[dict[str, Any]] = []
    for source_item in items:
        if destination not in source_item.get("targets", ["cv", "portfolio"]):
            continue
        item = deepcopy(source_item)
        item["parts"] = []
        for source_part in source_item["parts"]:
            if destination not in source_part.get("targets", ["cv", "portfolio"]):
                continue
            part = deepcopy(source_part)
            if part["type"] == "link":
                part["url"] = resolve_url(part["url"], "link.url", url_context)
            item["parts"].append(part)
        if not item["parts"]:
            continue
        if source_item.get("children"):
            children = destination_items(source_item["children"], destination, url_context)
            if children:
                item["children"] = children
            else:
                item.pop("children", None)
        resolved.append(item)
    return resolved


def portfolio_profile(profile: dict[str, Any]) -> dict[str, Any]:
    person = profile["person"]
    portfolio_url = profile["settings"]["portfolio_url"]
    common_url_context = {"portfolio_url": portfolio_url}
    portfolio_links = {
        link["id"]: link["url"]
        for link in person.get("links", [])
        if targets(link, "portfolio")
    }
    email = next(
        contact["value"]
        for contact in person.get("contacts", [])
        if contact.get("type") == "email" and targets(contact, "portfolio")
    )
    portfolio_links["email"] = email

    experience = []
    for record in profile.get("experience", []):
        if not targets(record, "portfolio"):
            continue
        experience.append(
            {
                "title": destination_value(record, "portfolio", "role"),
                "company": destination_value(record, "portfolio", "company"),
                "dates": destination_value(record, "portfolio", "dates"),
                "items": destination_items(
                    destination_value(record, "portfolio", "items"),
                    "portfolio",
                    common_url_context,
                ),
            }
        )

    education = [
        {
            "degree": destination_value(record, "portfolio", "degree"),
            "institution": destination_value(record, "portfolio", "institution"),
            "dates": destination_value(record, "portfolio", "dates"),
        }
        for record in profile.get("education", [])
        if targets(record, "portfolio")
    ]

    skills = [
        {"title": record["title"], "items": record["items"]}
        for record in profile.get("skills", [])
        if targets(record, "portfolio")
    ]

    projects = []
    for record in profile.get("projects", []):
        if not targets(record, "portfolio"):
            continue
        url_context = {"portfolio_url": portfolio_url, "project_id": record["id"]}
        projects.append(
            {
                "id": record["id"],
                "title": destination_value(record, "portfolio", "title"),
                "items": destination_items(
                    destination_value(record, "portfolio", "items"),
                    "portfolio",
                    url_context,
                ),
                "media": destination_value(record, "portfolio", "media", []),
                "technologies": destination_value(record, "portfolio", "technologies", []),
            }
        )

    certifications = [
        {
            "title": record["title"],
            "issuer": record["issuer"],
            "date": record["date"],
            "link": record["link"],
        }
        for record in profile.get("certifications", [])
        if targets(record, "portfolio")
    ]

    return {
        "person": {"name": person["name"], "title": person["title"], "social": portfolio_links},
        "about": {
            "items": destination_items(
                profile["about"]["portfolio"]["items"],
                "portfolio",
                common_url_context,
            )
        },
        "resumeUrl": profile["settings"]["resume_filename"],
        "experience": experience,
        "education": education,
        "skills": skills,
        "projects": projects,
        "certifications": certifications,
    }


def render_portfolio(profile: dict[str, Any]) -> str:
    payload = json.dumps(portfolio_profile(profile), ensure_ascii=False, indent=4)
    return f"// Generated from data/profile.yaml. Do not edit directly.\nwindow.PROFILE_DATA = {payload};\n"


def _header_entry(icon: str, label: str, url: str | None = None) -> str:
    content = rf"\raisebox{{-0.2\height}}\{icon}\ {escape_latex(label)}"
    if url is None:
        return content
    return rf"\href{{{escape_latex(url)}}}{{{content}}}"


def cv_profile(profile: dict[str, Any]) -> dict[str, Any]:
    person = profile["person"]
    portfolio_url = profile["settings"]["portfolio_url"]
    common_url_context = {"portfolio_url": portfolio_url}

    contacts = [record for record in person["contacts"] if targets(record, "cv")]
    links = [record for record in person["links"] if targets(record, "cv")]
    primary: list[tuple[int, str]] = []
    secondary: list[tuple[int, str]] = []
    contact_icons = {"email": "faEnvelope", "phone": "faPhone", "location": "faMapMarker"}
    contact_order = {"email": 10, "phone": 10, "location": 20}
    for contact in contacts:
        contact_type = contact["type"]
        icon = contact_icons.get(contact_type, "faAddressCard")
        url = f"mailto:{contact['value']}" if contact_type == "email" else None
        entry = _header_entry(icon, contact["label"], url)
        collection = primary if contact_type == "email" else secondary
        collection.append((contact_order.get(contact_type, 100), entry))

    link_icons = {"linkedin": "faLinkedin", "portfolio": "faGlobe", "github": "faGithub"}
    link_order = {"linkedin": 20, "portfolio": 30, "github": 40}
    for link in links:
        primary.append(
            (
                link_order.get(link["id"], 100),
                _header_entry(link_icons.get(link["id"], "faLink"), link["label"], link["url"]),
            )
        )

    education = [
        {
            "institution": destination_value(record, "cv", "institution"),
            "degree": destination_value(record, "cv", "degree"),
            "dates": destination_value(record, "cv", "dates"),
            "location": destination_value(record, "cv", "location"),
        }
        for record in profile["education"]
        if targets(record, "cv")
    ]

    experience = []
    for record in profile["experience"]:
        if not targets(record, "cv"):
            continue
        experience.append(
            {
                "company": destination_value(record, "cv", "company"),
                "role": destination_value(record, "cv", "role"),
                "dates": destination_value(record, "cv", "dates"),
                "location": destination_value(record, "cv", "location"),
                "items": destination_items(
                    destination_value(record, "cv", "items"),
                    "cv",
                    common_url_context,
                ),
            }
        )

    projects = []
    for source_index, record in enumerate(profile["projects"]):
        if not targets(record, "cv"):
            continue
        url_context = {"portfolio_url": portfolio_url, "project_id": record["id"]}
        projects.append(
            {
                "id": record["id"],
                "title": destination_value(record, "cv", "title"),
                "dates": destination_value(record, "cv", "dates"),
                "items": destination_items(
                    destination_value(record, "cv", "items"),
                    "cv",
                    url_context,
                ),
                "url_context": url_context,
                "order": record.get("cv", {}).get("order", 1000 + source_index),
            }
        )
    projects.sort(key=lambda project: project["order"])

    return {
        "person": {"name": person["name"], "title": person["title"]},
        "header_primary": " ~\n    ".join(entry for _, entry in sorted(primary)),
        "header_secondary": " \n    \\hspace{0.25cm}".join(entry for _, entry in sorted(secondary)),
        "url_context": common_url_context,
        "about": destination_items(profile["about"]["cv"]["items"], "cv", common_url_context),
        "education": education,
        "experience": experience,
        "projects": projects,
        "skills": [record for record in profile["skills"] if targets(record, "cv")],
        "certifications": [record for record in profile["certifications"] if targets(record, "cv")],
    }


def _jinja_environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(CV_DIRECTORY),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="<<",
        variable_end_string=">>",
        comment_start_string="<#",
        comment_end_string="#>",
    )
    environment.filters["latex"] = escape_latex
    environment.filters["latex_parts"] = render_latex_parts
    environment.filters["join_latex"] = lambda values: ", ".join(escape_latex(str(value)) for value in values)
    return environment


def render_cv(profile: dict[str, Any]) -> str:
    template = _jinja_environment().get_template(CV_TEMPLATE_PATH.name)
    return template.render(cv=cv_profile(profile))


def load_profile() -> dict[str, Any]:
    return load_profile_data(PROFILE_PATH)


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)
    return True


def generated_outputs(profile: dict[str, Any]) -> dict[Path, str]:
    return {
        PORTFOLIO_PATH: render_portfolio(profile),
        CV_PATH: render_cv(profile),
    }


def pdf_page_count(pdf_path: Path) -> int:
    try:
        return len(PdfReader(pdf_path).pages)
    except Exception as error:
        raise SystemExit(f"Cannot validate CV page count for {pdf_path}: {error}") from error


def public_resume_path(resume_filename: str) -> Path:
    """Resolve a configured public PDF path without allowing root traversal."""
    resume_relative = Path(resume_filename)
    if (
        resume_relative.is_absolute()
        or not resume_relative.parts
        or any(part in {".", ".."} for part in resume_relative.parts)
        or resume_relative.suffix.lower() != ".pdf"
    ):
        raise SystemExit("settings.resume_filename must be a relative PDF path inside the repository root")
    return ROOT / resume_relative


def install_compiled_pdf(
    source_pdf: Path,
    resume_filename: str,
    page_limit: int,
) -> tuple[Path, bool]:
    if not source_pdf.is_file() or source_pdf.stat().st_size == 0:
        raise SystemExit(f"CV compilation did not produce a nonempty {source_pdf}")

    page_count = pdf_page_count(source_pdf)
    if page_count > page_limit:
        raise SystemExit(f"CV has {page_count} pages; configured limit is {page_limit}")
    print(f"Validated CV page count: {page_count}/{page_limit}")

    resume_path = public_resume_path(resume_filename)
    if resume_path.exists() and filecmp.cmp(source_pdf, resume_path, shallow=False):
        return resume_path, False

    resume_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = resume_path.with_suffix(resume_path.suffix + ".tmp")
    shutil.copyfile(source_pdf, temporary)
    temporary.replace(resume_path)
    return resume_path, True


def compile_cv(resume_filename: str, page_limit: int | None = None) -> tuple[Path, bool]:
    """Compile the generated CV with MiKTeX and refresh the public PDF."""
    resume_path = public_resume_path(resume_filename)

    texify = shutil.which("texify")
    if texify is None:
        raise SystemExit("Cannot compile CV: MiKTeX texify was not found on PATH")

    subprocess.run(
        [texify, "--pdf", "--batch", "--tex-option=--halt-on-error", CV_PATH.name],
        cwd=CV_PATH.parent,
        check=True,
    )
    if page_limit is None:
        if not CV_PDF_PATH.is_file() or CV_PDF_PATH.stat().st_size == 0:
            raise SystemExit(f"CV compilation did not produce a nonempty {CV_PDF_PATH.name}")
        if resume_path.exists() and filecmp.cmp(CV_PDF_PATH, resume_path, shallow=False):
            return resume_path, False
        resume_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = resume_path.with_suffix(resume_path.suffix + ".tmp")
        shutil.copyfile(CV_PDF_PATH, temporary)
        temporary.replace(resume_path)
        return resume_path, True
    return install_compiled_pdf(CV_PDF_PATH, resume_filename, page_limit)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fail when generated files are stale")
    mode.add_argument(
        "--pdf",
        action="store_true",
        help="compile main.tex with MiKTeX texify and update the public resume PDF",
    )
    mode.add_argument(
        "--pdf-source",
        type=Path,
        help="validate an already compiled PDF and update the public resume PDF",
    )
    arguments = parser.parse_args()

    profile = load_profile()
    outputs = generated_outputs(profile)
    stale = [
        path
        for path, content in outputs.items()
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if arguments.check:
        if stale:
            names = ", ".join(str(path.relative_to(ROOT)) for path in stale)
            raise SystemExit(f"Generated content is stale: {names}")
        print("Generated content is current")
        return
    for path, content in outputs.items():
        state = "updated" if write_if_changed(path, content) else "unchanged"
        print(f"{state}: {path.relative_to(ROOT)}")
    if arguments.pdf:
        resume_path, changed = compile_cv(
            profile["settings"]["resume_filename"],
            profile["settings"]["cv_page_limit"],
        )
        state = "updated" if changed else "unchanged"
        print(f"{state}: {resume_path.relative_to(ROOT)}")
    elif arguments.pdf_source:
        source_pdf = arguments.pdf_source
        if not source_pdf.is_absolute():
            source_pdf = ROOT / source_pdf
        resume_path, changed = install_compiled_pdf(
            source_pdf.resolve(),
            profile["settings"]["resume_filename"],
            profile["settings"]["cv_page_limit"],
        )
        state = "updated" if changed else "unchanged"
        print(f"{state}: {resume_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
