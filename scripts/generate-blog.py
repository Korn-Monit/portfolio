from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "blog" / "posts"
BLOG_DIR = ROOT / "blog"
SITE_TITLE = "Technical Blog"
AUTHOR = "Anas"


@dataclass(frozen=True)
class Post:
    title: str
    date: str
    slug: str
    tags: list[str]
    summary: str
    visibility: str
    source: Path
    body: str


def parse_frontmatter(raw: str, source: Path) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        raise ValueError(f"{source} is missing frontmatter")

    end = raw.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{source} has unterminated frontmatter")

    metadata: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{source} has invalid frontmatter line: {line}")
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, raw[end + 4 :].strip()


def parse_tags(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [tag.strip().strip('"').strip("'") for tag in value.split(",") if tag.strip()]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "post"


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        title = metadata.get("title")
        date = metadata.get("date")
        if not title or not date:
            raise ValueError(f"{path} needs title and date frontmatter")

        posts.append(
            Post(
                title=title,
                date=date,
                slug=metadata.get("slug") or slugify(title),
                tags=parse_tags(metadata.get("tags", "")),
                summary=metadata.get("summary", ""),
                visibility=metadata.get("visibility", "private").lower(),
                source=path,
                body=body,
            )
        )

    return sorted(posts, key=lambda post: post.date, reverse=True)


def markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    code_lang = ""
    list_items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{inline_format(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in list_items) + "</ul>")
            list_items.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                blocks.append(
                    f'<pre><code class="language-{html.escape(code_lang)}">'
                    + html.escape("\n".join(code_lines))
                    + "</code></pre>"
                )
                in_code = False
                code_lines.clear()
                code_lang = ""
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_lang = line[3:].strip()
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_format(heading.group(2))}</h{level}>")
            continue

        item = re.match(r"^[-*]\s+(.+)$", line)
        if item:
            flush_paragraph()
            list_items.append(inline_format(item.group(1)))
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def inline_format(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    return escaped


def render_page(title: str, content: str, depth: int = 1) -> str:
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} | {SITE_TITLE}</title>
  <meta name="description" content="Technical writing, notes, and engineering articles by {AUTHOR}.">
  <link rel="stylesheet" href="{prefix}styles.css">
  <link rel="stylesheet" href="{prefix}blog/blog.css">
</head>
<body>
  <main class="blog-shell">
    <header class="blog-header">
      <a class="blog-home-link" href="{prefix}index.html">Portfolio</a>
      <a class="blog-home-link" href="{prefix}blog/">Blog</a>
    </header>
    {content}
  </main>
</body>
</html>
"""


def render_index(posts: Iterable[Post]) -> str:
    grouped: dict[str, list[Post]] = {}
    for post in posts:
        month = datetime.strptime(post.date, "%Y-%m-%d").strftime("%Y %B")
        grouped.setdefault(month, []).append(post)

    sections: list[str] = [
        '<section class="blog-intro">',
        "<h1>Technical Blog</h1>",
        "<p>Engineering notes, implementation write-ups, and technical experiments.</p>",
        "</section>",
    ]

    for month, month_posts in grouped.items():
        sections.append(f'<section class="blog-month"><h2>{html.escape(month)}</h2><div class="blog-post-list">')
        for post in month_posts:
            tags = " ".join(f"<span>{html.escape(tag)}</span>" for tag in post.tags)
            sections.append(
                f"""<article class="blog-list-item">
  <a href="{html.escape(post.slug)}/">{html.escape(post.title)}</a>
  <time datetime="{html.escape(post.date)}">{html.escape(post.date)}</time>
  <p>{html.escape(post.summary)}</p>
  <div class="blog-tags">{tags}</div>
</article>"""
            )
        sections.append("</div></section>")

    return render_page("Blog", "\n".join(sections), depth=1)


def render_post(post: Post) -> str:
    tags = " ".join(f"<span>{html.escape(tag)}</span>" for tag in post.tags)
    body = re.sub(rf"^#\s+{re.escape(post.title)}\s*\n+", "", post.body, count=1)
    content = f"""<article class="blog-article">
  <header>
    <p class="blog-kicker">Technical Blog</p>
    <h1>{html.escape(post.title)}</h1>
    <div class="blog-meta">
      <time datetime="{html.escape(post.date)}">{html.escape(post.date)}</time>
      <div class="blog-tags">{tags}</div>
    </div>
  </header>
  <div class="blog-content">
    {markdown_to_html(body)}
  </div>
</article>"""
    return render_page(post.title, content, depth=2)


def write_blog(posts: list[Post]) -> None:
    BLOG_DIR.mkdir(exist_ok=True)
    public_posts = [post for post in posts if post.visibility == "public"]

    (BLOG_DIR / "index.html").write_text(render_index(public_posts), encoding="utf-8")
    for post in public_posts:
        output_dir = BLOG_DIR / post.slug
        output_dir.mkdir(exist_ok=True)
        (output_dir / "index.html").write_text(render_post(post), encoding="utf-8")

    now = format_datetime(datetime.now().astimezone())
    print(f"Generated {len(public_posts)} public post(s) at {now}")


if __name__ == "__main__":
    write_blog(load_posts())


