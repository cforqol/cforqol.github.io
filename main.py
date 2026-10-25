"""Auto-generate section index tables from the filesystem."""

import re
from pathlib import Path

FRONT_MATTER = re.compile(r"^---\n.*?\n---\n", re.S)


def _title(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else fallback


def _blurb(text: str) -> str:
    text = FRONT_MATTER.sub("", text, count=1)
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "---", "<", "!")):
            continue
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        return s.replace("`", "").replace("*", "")
    return ""


def _row(path: Path, link: str, fallback: str) -> str:
    text = path.read_text(encoding="utf-8")
    return f"| [{_title(text, fallback)}]({link}) | {_blurb(text)} |"


def define_env(env):
    # env.conf is the config file (mkdocs.yml); env.config is NOT it.
    docs = Path(env.project_dir) / env.conf.get("docs_dir", "docs")

    @env.macro
    def index_of(folder: str = "") -> str:
        d = (docs / folder).resolve()
        if not d.is_dir():
            return f"*no such folder: {folder}*"

        rows = []
        for entry in sorted(d.iterdir(), key=lambda p: p.name.lower()):
            if entry.name.startswith(".") or entry.name == "index.md":
                continue
            if entry.is_dir():
                idx = entry / "index.md"
                if idx.exists():
                    rows.append(_row(idx, f"{entry.name}/index.md", entry.name))
            elif entry.suffix == ".md":
                rows.append(_row(entry, entry.name, entry.stem))

        if not rows:
            return "*nothing here yet*"
        return "| Page | What it covers |\n|------|----------------|\n" + "\n".join(rows)

    @env.macro
    def tools_index() -> str:
        """Index of docs/tools/<repo>/ mirrors, with a link to each source repo."""
        root = docs / "tools"
        if not root.is_dir():
            return "*nothing here yet*"

        rows = []
        for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            idx = entry / "index.md"
            if not idx.exists():
                continue
            rows.append(
                f"| [{entry.name}]({entry.name}/index.md) "
                f"| {_blurb(idx.read_text(encoding='utf-8'))} "
                f"| [cforqol/{entry.name}](https://github.com/cforqol/{entry.name}) |"
            )

        if not rows:
            return "*nothing here yet*"
        return (
            "| Tool | What it does | Source |\n"
            "|------|--------------|--------|\n"
            + "\n".join(rows)
        )
