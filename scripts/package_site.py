"""Assemble and validate the static GitHub Pages artifact."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import shutil
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist"
STATIC_FILES = (
    "index.html",
    "styles.css",
    "script.js",
    "robots.txt",
    "sitemap.xml",
    "assets/resume.pdf",
    "assets/favicon.svg",
)
GENERATED_FILES = ("generated/profile.js",)
BLOG_EXCLUDED_DIRECTORIES = {"drafts", "posts", "done", "__pycache__"}
SOURCE_SUFFIXES = {".md", ".py", ".pyc", ".tex", ".j2", ".toml", ".lock", ".yaml", ".yml"}


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = "href" if tag in {"a", "link"} else "src" if tag in {"script", "img", "source", "video"} else None
        if attribute is None:
            return
        for name, value in attrs:
            if name == attribute and value:
                self.links.append(value)


def _safe_output_path(output: Path) -> Path:
    output = output.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError(f"output directory must be inside {ROOT}")
    return output


def _copy_file(relative: str, output: Path) -> None:
    source = ROOT / relative
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"required site file is missing or empty: {relative}")
    destination = output / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_blog(output: Path) -> None:
    blog_root = ROOT / "blog"
    for source in blog_root.rglob("*"):
        relative = source.relative_to(blog_root)
        if any(part in BLOG_EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if not source.is_file() or source.name.startswith(".") or source.suffix.lower() in SOURCE_SUFFIXES:
            continue
        destination = output / "blog" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _local_target(html_path: Path, link: str, output: Path) -> Path | None:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    if path.startswith("/portfolio/"):
        target = output / path.removeprefix("/portfolio/")
    elif path.startswith("/"):
        return None
    else:
        target = html_path.parent / path
    if path.endswith("/"):
        target /= "index.html"
    return target.resolve()


def validate_site(output: Path) -> None:
    output = _safe_output_path(output)
    missing: list[str] = []
    for html_path in output.rglob("*.html"):
        parser = LinkCollector()
        parser.feed(html_path.read_text(encoding="utf-8"))
        for link in parser.links:
            target = _local_target(html_path, link, output)
            if target is not None and output not in target.parents and target != output:
                missing.append(f"{html_path.relative_to(output)} -> {link} (outside artifact)")
            elif target is not None and not target.exists():
                missing.append(f"{html_path.relative_to(output)} -> {link}")
    if missing:
        raise ValueError("broken local site links:\n" + "\n".join(missing))

    leaked = [
        path.relative_to(output)
        for path in output.rglob("*")
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES
    ]
    if leaked:
        raise ValueError("source-only files leaked into site artifact: " + ", ".join(map(str, leaked)))


def package_site(output: Path = DEFAULT_OUTPUT) -> Path:
    output = _safe_output_path(output)
    staging = output.with_name(f".{output.name}.tmp")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    try:
        for relative in (*STATIC_FILES, *GENERATED_FILES):
            _copy_file(relative, staging)
        _copy_blog(staging)
        (staging / ".nojekyll").write_text("", encoding="utf-8")
        validate_site(staging)
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    files = sum(1 for path in output.rglob("*") if path.is_file())
    print(f"Packaged {files} static file(s) in {output.relative_to(ROOT)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output = arguments.output
    if not output.is_absolute():
        output = ROOT / output
    package_site(output)


if __name__ == "__main__":
    main()
