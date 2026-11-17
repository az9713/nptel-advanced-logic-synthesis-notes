"""Build the offline reader and the timestamp index from the notes."""

import csv
from html import escape
from pathlib import Path
import re

import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


ROOT = Path(__file__).resolve().parents[1]
PLAYLIST = "https://www.youtube.com/playlist?list=PLbMVogVj5nJQe0_9YJlN9S7ktkA8DI-fL"
COURSE = "https://nptel.ac.in/courses/117106109"
TIMESTAMP = re.compile(
    r"\[L(\d{2}) (\d+:\d{2})\]\(https://www\.youtube\.com/watch\?v="
    r"([\w-]{11})&t=(\d+)s\)"
)
MATH = re.compile(r"\$\$(.+?)\$\$|\$([^$\n]+)\$", re.S)


class MathSource(Preprocessor):
    def run(self, lines):
        def protect(match):
            display, inline = match.groups()
            if display is None:
                formula = f'<span class="inline-math">\\({escape(inline)}\\)</span>'
                return self.md.htmlStash.store(formula)
            formula = f'<div class="display-math">\\[{escape(display.strip())}\\]</div>'
            return "\n\n" + self.md.htmlStash.store(formula) + "\n\n"

        return MATH.sub(protect, "\n".join(lines)).split("\n")


class MathExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MathSource(md), "math-source", 26)


def article(source):
    return markdown.markdown(source, extensions=["tables", "fenced_code", "toc", MathExtension()])


def page(title, body, prefix="", math=False, label="Advanced Logic Synthesis"):
    scripts = (
        f'<script defer src="{prefix}assets/math-config.js"></script>'
        f'<script defer src="{prefix}assets/mathjax-tex-svg.js"></script>'
        if math else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/reader.css">
{scripts}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><nav aria-label="Course navigation">
  <a class="brand" href="{prefix}index.html">{escape(label)}</a>
  <a href="{prefix}source-map.html">Recordings</a>
  <a href="{prefix}laboratory.html">Laboratory</a>
</nav></header>
<main id="main">{body}</main>
</body>
</html>
"""


def write(path, value):
    (ROOT / path).write_text(value, encoding="utf-8", newline="\n")


def collection():
    chapters = []
    pointers = {}
    for path in sorted((ROOT / "chapters").glob("*.md")):
        source = path.read_text(encoding="utf-8")
        title = source.splitlines()[0].removeprefix("# ")
        for number, clock, video, seconds in TIMESTAMP.findall(source):
            pointers.setdefault(int(number), []).append((clock, video, int(seconds), path.stem))
        chapters.append((path, title, source))
    return chapters, pointers


def sources(chapters, pointers):
    with (ROOT / "lecture-inventory.csv").open(encoding="utf-8", newline="") as file:
        inventory = list(csv.DictReader(file))
    assert len(inventory) == 34 and set(pointers) == set(range(1, 35))
    titles = {path.stem: title for path, title, _ in chapters}
    rows = []
    for row in inventory:
        index, duration, video = int(row["index"]), int(row["duration_s"]), row["video_id"]
        transcript = row["transcript_source"]
        assert transcript and row["sha256"] and float(row["caption_end_s"]) >= duration * 0.98
        minutes, seconds = divmod(duration, 60)
        anchors = pointers[index]
        for clock, anchor_video, anchor_seconds, _ in anchors:
            assert anchor_video == video and anchor_seconds < duration
            assert clock == f"{anchor_seconds // 60:02}:{anchor_seconds % 60:02}"
        stem = anchors[0][3]
        assert all(anchor[3] == stem for anchor in anchors)
        video_link = f'https://www.youtube.com/watch?v={video}'
        rows.append(
            f'<tr><th scope="row">{index:02}</th>'
            f'<td><a href="{video_link}">{escape(row["title"])}</a></td>'
            f'<td>{minutes}:{seconds:02}</td>'
            f'<td><a href="chapters/{stem}.html">{escape(titles[stem])}</a></td>'
            f'<td>{escape(transcript)}</td></tr>'
        )
    body = (
        '<section class="opening"><h1>Recordings and transcripts</h1>'
        '<p>The 34 recordings appear in playlist order. Chapter headings link to the '
        'relevant points in each recording. The inventory records the provenance '
        'and coverage of the caption or speech-recognition track used for each video.</p>'
        f'<p><a href="{PLAYLIST}">YouTube playlist</a> · '
        f'<a href="{COURSE}">NPTEL course record</a> · '
        '<a href="lecture-inventory.csv">Transcript inventory (CSV)</a></p></section>'
        '<div class="table-scroll" role="region" tabindex="0" aria-label="Recording inventory">'
        '<table><thead><tr><th scope="col">#</th><th scope="col">Recording</th>'
        '<th scope="col">Minutes</th><th scope="col">Chapter</th>'
        '<th scope="col">Transcript source</th></tr></thead>'
        '<tbody>' + "\n".join(rows) + '</tbody></table></div>'
    )
    write("source-map.html", page("Recordings and transcripts", body))


def build():
    chapters, pointers = collection()
    sources(chapters, pointers)
    entries = []
    for i, (path, title, source) in enumerate(chapters):
        number = i + 1
        lecture_ids = sorted({int(found[0]) for found in TIMESTAMP.findall(source)})
        lecture_range = f"Recording {lecture_ids[0]:02}"
        if len(lecture_ids) > 1:
            lecture_range = f"Recordings {lecture_ids[0]:02}–{lecture_ids[-1]:02}"
        entries.append(
            f'<li><a href="chapters/{path.stem}.html">'
            f'<span>{escape(title)}</span><small>{lecture_range}</small></a></li>'
        )
        previous = (
            f'<a rel="prev" href="{chapters[i - 1][0].stem}.html">Previous chapter</a>'
            if i else '<a rel="prev" href="../index.html">Contents</a>'
        )
        following = (
            f'<a rel="next" href="{chapters[i + 1][0].stem}.html">Next chapter</a>'
            if number < len(chapters) else '<a rel="next" href="../laboratory.html">Laboratory</a>'
        )
        source_link = f'<a href="{path.name}">Markdown</a>'
        heading = f'<div class="chapter-meta">{lecture_range} <span>·</span> {source_link}</div>'
        section_nav = '<nav class="pagination" aria-label="Chapters">' + previous + following + '</nav>'
        body = f'<article>{heading}\n{article(source)}</article>\n{section_nav}'
        write(path.with_suffix(".html").relative_to(ROOT), page(title, body, "../", math=True))
    home = (
        '<section class="opening"><p class="course-credit">NPTEL · IIT Madras · Dhiraj Taneja</p>'
        '<h1>Advanced Logic Synthesis</h1>'
        '<p>From MOS transistor behavior to a mapped netlist, timing closure, '
        'and formal equivalence. Follow a small execution slice through '
        '11 chapters covering all 34 recordings.</p>'
        '<div class="actions"><a class="start" href="chapters/01-mos.html">Start reading</a>'
        '<a href="source-map.html">Browse recordings</a></div></section>'
        '<section><h2>Chapters</h2><ol class="contents">'
        + "\n".join(entries) + '</ol></section>'
    )
    write("index.html", page("Advanced Logic Synthesis", home))
    lab_md = (ROOT / "code" / "README.md").read_text(encoding="utf-8")
    downloads = (
        '<ul class="downloads"><li><a href="code/lab.py">Python model checks</a></li>'
        '<li><a href="code/rc.cir">ngspice RC deck</a></li>'
        '<li><a href="code/slice.v">Verilog source</a></li>'
        '<li><a href="code/synthesis.ys">Yosys script</a></li></ul>'
    )
    write("laboratory.html", page("Computational laboratory", f'<article>{article(lab_md)}{downloads}</article>'))


if __name__ == "__main__":
    build()
