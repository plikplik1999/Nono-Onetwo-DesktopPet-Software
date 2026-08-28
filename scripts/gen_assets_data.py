"""生成 assets_data.py：将 assets/ 下所有素材转为 base64 内嵌。

用法：
    python scripts/gen_assets_data.py

会读取项目根目录的 assets/，在项目根目录生成 assets_data.py。
修改素材（新增/删除/替换文件）后，运行本脚本并重新打包即可。
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets"
OUT = ROOT / "assets_data.py"

SKIN_CHARS = ("nono", "onetwo", "both")
AUDIO_CHARS = ("nono", "onetwo", "both")
AUDIO_EXTS = (".mp3", ".wav")


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def emit(files: dict) -> str:
    lines = []
    for name, s in files.items():
        lines.append(f'    "{name}": (')
        for i in range(0, len(s), 76):
            lines.append(f'        "{s[i:i + 76]}"')
        lines.append("    ),")
    return "\n".join(lines)


def main() -> None:
    skins = {}
    for char in SKIN_CHARS:
        d = SRC / "skin" / char
        skins[char] = {p.name: b64(p) for p in sorted(d.glob("*.gif"))}

    audio = {}
    for char in AUDIO_CHARS:
        d = SRC / "audio" / char
        audio[char] = {
            p.name: b64(p)
            for p in sorted(d.iterdir())
            if p.suffix.lower() in AUDIO_EXTS
        }

    parts = ['"""Embedded assets (base64). Generated - do not edit."""\n\n']
    parts.append("SKINS = {\n")
    for char, files in skins.items():
        parts.append(f'    "{char}": {{\n')
        parts.append(emit(files))
        parts.append("    },\n")
    parts.append("}\n\n")
    parts.append("AUDIO = {\n")
    for char, files in audio.items():
        parts.append(f'    "{char}": {{\n')
        parts.append(emit(files))
        parts.append("    },\n")
    parts.append("}\n")

    OUT.write_text("".join(parts), encoding="utf-8")

    print("skins:", {k: len(v) for k, v in skins.items()})
    print("audio:", {k: len(v) for k, v in audio.items()})
    print("assets_data.py size MB:", round(OUT.stat().st_size / 1024 / 1024, 2))


if __name__ == "__main__":
    main()
