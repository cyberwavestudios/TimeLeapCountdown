#!/usr/bin/env python3
"""Make a built web app work under a GitHub Pages sub-address
(https://<user>.github.io/<REPO>/) instead of at the top of a domain.

Usage: python3 patch_site.py <site_dir> <REPO> <kind>
kinds: plain, threadseers, timeleap, drift, sequencer, reader, graviton
"""
import json, os, re, shutil, sys, pathlib

site = pathlib.Path(sys.argv[1]).resolve()
repo = sys.argv[2]
kind = sys.argv[3]
B = "/" + repo  # base path, no trailing slash

TEXT_EXT = {".html", ".js", ".css", ".json", ".webmanifest"}


def text_files():
    for p in site.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_EXT:
            yield p


def edit(path, fn):
    p = site / path if not isinstance(path, pathlib.Path) else path
    s = p.read_text(encoding="utf-8")
    n = fn(s)
    if n != s:
        p.write_text(n, encoding="utf-8")
        return True
    return False


def must_replace(path, old, new, count=None):
    p = site / path
    s = p.read_text(encoding="utf-8")
    if old not in s:
        sys.exit(f"patch failed: {old!r} not found in {path}")
    p.write_text(s.replace(old, new) if count is None else s.replace(old, new, count), encoding="utf-8")


def main_js():
    js = sorted((site / "assets").glob("index-*.js"))
    if len(js) != 1:
        sys.exit(f"expected one main bundle in {site/'assets'}, found {js}")
    return js[0].relative_to(site)


def prefix_root_paths():
    """Rewrite "/folder/..." and "/file.ext" string references that point at
    things that really exist at the top of the site."""
    tops = sorted({p.name for p in site.iterdir()} - {"index.html", "404.html"}, key=len, reverse=True)
    if not tops:
        return
    names = "|".join(re.escape(t) for t in tops)
    # a quote, backtick or "url(" followed by /<top-level entry> then / or the end of the reference
    pat = re.compile(r'''(["'`(])/(?=(?:%s)(?:[/"'`)?#]|$))''' % names)
    for f in text_files():
        edit(f, lambda s: pat.sub(lambda m: m.group(1) + B + "/", s))


def spa_fallback():
    idx = site / "index.html"
    if idx.exists():
        shutil.copyfile(idx, site / "404.html")


# ---------------------------------------------------------------- per-app work

if kind == "threadseers":
    # React Router: give the BrowserRouter a basename
    js = main_js()
    s = (site / js).read_text(encoding="utf-8")
    new, n = re.subn(r'(\w+\.jsx\((\w+),\{)(children:\w+\.jsxs\(\w+,\{children:\[\w+\.jsx\(\w+,\{path:"/")',
                     r'\1basename:"%s",\3' % B, s)
    if n != 1:
        sys.exit("threadseers router patch failed")
    (site / js).write_text(new, encoding="utf-8")

if kind in ("timeleap", "sequencer"):
    # wouter: default router base
    js = main_js()
    s = (site / js).read_text(encoding="utf-8")
    new, n = re.subn(r',base:"",ssrPath:', ',base:"%s",ssrPath:' % B, s)
    if n != 1:
        sys.exit("wouter base patch failed")
    (site / js).write_text(new, encoding="utf-8")

if kind == "sequencer":
    src = pathlib.Path(sys.argv[4]).resolve()  # unzipped release root
    for item in (src / "public").iterdir():
        dest = site / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copyfile(item, dest)
    # turn the server's built-in loop list into a static file
    ts = (src / "server" / "storage.ts").read_text(encoding="utf-8")
    m = re.search(r"const defaultLoops: InsertLoop\[\] = (\[.*?\n    \]);", ts, re.S)
    if not m:
        sys.exit("could not find loop list in storage.ts")
    body = re.sub(r"(\n\s*)(\w+):", r'\1"\2":', m.group(1))      # quote keys
    body = re.sub(r",(\s*[}\]])", r"\1", body)                   # drop trailing commas
    loops = json.loads(body)
    for i, l in enumerate(loops, 1):
        l["id"] = f"loop-{i}"
        l.setdefault("mood", None)
    (site / "api").mkdir(exist_ok=True)
    (site / "api" / "loops.json").write_text(json.dumps(loops, indent=1), encoding="utf-8")
    missing = [l["filename"] for l in loops if not (site / "audio" / "loops" / l["filename"]).exists()]
    if missing:
        print("warning: loop files not found:", missing)
    js = main_js()
    must_replace(js, 'queryKey:["/api/loops"]', 'queryKey:["/api/loops.json"]')
    must_replace(js, "fetch(`/api/loops/${i.id}/download`)",
                 "fetch(`/audio/loops/${encodeURIComponent(i.filename)}`)")

if kind == "reader":
    src = pathlib.Path(sys.argv[4]).resolve()
    api_pub = src / "artifacts" / "api-server" / "public"
    shutil.copytree(api_pub / "comic-pages", site / "comic-pages", dirs_exist_ok=True)
    shutil.copyfile(api_pub / "cover.jpg", site / "cover.jpg")
    shutil.copyfile(api_pub / "sampler.pdf", site / "sampler.pdf")
    pages = sorted(int(m.group(1)) for p in (site / "comic-pages").iterdir()
                   if (m := re.match(r"page-0*(\d+)\.jpg$", p.name)))
    if pages != list(range(1, len(pages) + 1)):
        sys.exit(f"comic pages not contiguous: {pages}")
    total = len(pages)
    (site / "api" / "comic").mkdir(parents=True, exist_ok=True)
    (site / "api" / "comic" / "pages.json").write_text(json.dumps({
        "title": "CONTINUUM", "subtitle": "Issue #1: Stay Alive or Die Trying",
        "author": "Charlie Hadley", "totalPages": total,
        "coverUrl": B + "/cover.jpg", "downloadUrl": B + "/sampler.pdf", "freePages": total}), encoding="utf-8")
    pad = {p.name for p in (site / "comic-pages").iterdir()}
    padded = "page-01.jpg" in pad
    js = main_js()
    s = (site / js).read_text(encoding="utf-8")
    s2 = re.sub(r"cover:`\$\{(\w+)\}/api/comic/cover`", r"cover:`${\1}/cover.jpg`", s)
    page_expr = 'String(e).padStart(2,"0")' if padded else "e"
    s2 = re.sub(r"page:e=>`\$\{(\w+)\}/api/comic/page/\$\{e\}`",
                lambda m: "page:e=>`${%s}/comic-pages/page-${%s}.jpg`" % (m.group(1), page_expr), s2)
    s2 = re.sub(r"download:`\$\{(\w+)\}/api/comic/download`", r"download:`${\1}/sampler.pdf`", s2)
    s2 = s2.replace('()=>"/api/comic/pages"', '()=>"/api/comic/pages.json"')
    # the frontend's own base ("/" at build time) becomes the repo path
    s2, n = re.subn(r'(\w+)="/"\.replace\(/\\/\$/,""\)', r'\1="%s/".replace(/\\/$/,"")' % B, s2)
    for need in ("/cover.jpg", "/comic-pages/page-", "/sampler.pdf", "/api/comic/pages.json"):
        if need not in s2:
            sys.exit(f"reader patch failed: {need}")
    if n < 1:
        sys.exit("reader base patch failed")
    (site / js).write_text(s2, encoding="utf-8")

if kind == "graviton":
    must_replace("index.html", "register('/sw.js')", "register('%s/sw.js')" % B)
    edit("sw.js", lambda s: re.sub(r"'/([^'\s]*)'", lambda m: "'%s/%s'" % (B, m.group(1)), s))
    edit("manifest.json", lambda s: s.replace('"start_url": "/"', '"start_url": "%s/"' % B))

# ---------------------------------------------------------------- common work
if kind != "graviton":
    prefix_root_paths()
if kind in ("threadseers", "timeleap", "sequencer", "reader", "drift"):
    spa_fallback()
(site / ".nojekyll").write_text("", encoding="utf-8")
print(f"patched {site} for {B}/ ({kind})")
