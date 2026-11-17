"""Check transcript provenance, local links, navigation, and rendered math."""

import argparse
import csv
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

from build import ROOT, collection


class Markup(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.refs = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        for name, value in attributes:
            if name == "id":
                assert value not in self.ids, f"Duplicate HTML id {value}"
                self.ids.add(value)
            if name in {"href", "src"} and value:
                self.refs.append(value)


def verify_inventory(site, local_transcripts):
    chapters, pointers = collection()
    with (ROOT / "lecture-inventory.csv").open(encoding="utf-8", newline="") as file:
        inventory = list(csv.DictReader(file))
    assert [int(row["index"]) for row in inventory] == list(range(1, 35))
    assert len({row["video_id"] for row in inventory}) == 34
    assert len(chapters) == 11
    for row in inventory:
        index = int(row["index"])
        origin = row["transcript_source"]
        assert origin in {"YouTube en", "YouTube en-orig", "Local Whisper small.en"}, row
        assert re.fullmatch(r"[a-f0-9]{64}", row["sha256"]), row
        duration = int(row["duration_s"])
        assert abs(float(row["caption_end_s"]) - duration) < 30, row
        for clock, video, seconds, _ in pointers[index]:
            assert video == row["video_id"], (index, seconds)
            assert seconds < duration and clock == f"{seconds // 60:02}:{seconds % 60:02}"
        if local_transcripts:
            check_transcript(row, pointers[index])
    return site / "index.html", site / "source-map.html", site / "laboratory.html", *[
        site / "chapters" / path.with_suffix(".html").name for path, _, _ in chapters
    ]


def check_transcript(row, anchors):
    prefix = f'{int(row["index"]):02}-{row["video_id"]}'
    folder = ROOT / "work" / "transcripts"
    origin = row["transcript_source"]
    tag = origin.split()[-1] if origin.startswith("YouTube ") else "asr"
    raw = folder / f"{prefix}.{tag}.json3"
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == row["sha256"], raw
    local = folder / f"{prefix}.txt"
    cues = [int(m) * 60 + int(s) for m, s in re.findall(
        r"^\[(\d+):(\d{2})\]", local.read_text(encoding="utf-8"), flags=re.M
    )]
    assert cues and cues == sorted(cues), local
    for _, _, seconds, _ in anchors:
        assert min(abs(cue - seconds) for cue in cues) <= 12, (prefix, seconds)


def verify_links(pages):
    parsed = {path: Markup(path) for path in pages}
    for path, markup in parsed.items():
        for reference in markup.refs:
            parts = urlsplit(reference)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            assert target.is_file(), f"{path.name}: missing local target {reference}"
            if parts.fragment:
                assert target in parsed, (path, reference)
                assert unquote(parts.fragment) in parsed[target].ids, (path, reference)


def verify_browser(pages, browser_path, base_url):
    from playwright.sync_api import sync_playwright

    def address(path):
        return urljoin(base_url, path.relative_to(pages[0].parent).as_posix()) if base_url else path.as_uri()

    with sync_playwright() as runtime:
        browser = runtime.chromium.launch(executable_path=browser_path)
        for width in (1440, 390):
            tab = browser.new_page(viewport={"width": width, "height": 900})
            def route_request(route):
                if base_url and route.request.url.startswith(base_url):
                    route.continue_()
                else:
                    route.abort()

            tab.route("https://**/*", route_request)
            errors = []
            tab.on("pageerror", lambda error: errors.append(str(error)))
            for path in pages:
                response = tab.goto(address(path))
                if base_url:
                    assert response and response.ok, (response, path)
                assert tab.locator("h1").count() == 1, path
                assert tab.locator("main img").evaluate_all(
                    "images => images.every(image => image.complete && image.naturalWidth > 0)"
                ), path
                if path.parent.name == "chapters":
                    tab.evaluate("() => MathJax.startup.promise")
                    math = tab.locator(".inline-math, .display-math")
                    assert math.count() > 0, path
                    for index, state in enumerate(math.evaluate_all(
                        """nodes => nodes.map(node => ({
                          equation: !!node.querySelector('mjx-container svg'),
                          error: !!node.querySelector('[data-mml-node="merror"]'),
                          expanded: node.scrollWidth > node.clientWidth + 1,
                          inline: node.classList.contains('inline-math')
                        }))"""
                    )):
                        assert state["equation"] and not state["error"], (path, index, state)
                        if not state["inline"] and state["expanded"]:
                            assert math.nth(index).evaluate("""node => {
                              node.scrollLeft = node.scrollWidth;
                              return node.scrollLeft > 0;
                            }"""), (path, index, width)
                overflow = tab.evaluate(
                    "() => document.documentElement.scrollWidth > innerWidth + 1"
                )
                assert not overflow and not errors, (path, width, overflow, errors)
            tab.goto(base_url or address(pages[0]))
            tab.get_by_role("link", name="Start reading").click()
            assert tab.url.endswith("/01-mos.html")
            tab.get_by_role("link", name="Next chapter").click()
            assert tab.url.endswith("/02-cmos.html")
            tab.get_by_role("link", name="Recordings").click()
            assert tab.locator("tbody tr").count() == 34
            assert tab.get_by_role("cell", name="Local Whisper small.en").count() == 3
            tab.close()
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--render", action="store_true", help="Use Playwright Chromium.")
    parser.add_argument("--site-dir", type=Path, default=ROOT)
    parser.add_argument("--base-url", help="Check the deployed site in Chromium.")
    parser.add_argument("--local-transcripts", action="store_true")
    args = parser.parse_args()
    paths = verify_inventory(args.site_dir.resolve(), args.local_transcripts)
    verify_links(paths)
    print("Verified 34 recording metadata rows, timing pointers, and site links.")
    if args.local_transcripts:
        print("Verified local transcript digests and timestamp neighborhoods.")
    if args.browser or args.render or args.base_url:
        base = args.base_url.rstrip("/") + "/" if args.base_url else None
        verify_browser(paths, str(args.browser) if args.browser else None, base)
        print("Verified 14 pages at 1440 px and 390 px with bundled math rendering.")
