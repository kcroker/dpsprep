import io
import re
import subprocess
from typing import TextIO

import click
from click_man.core import generate_man_page

from dpsprep.cli import dpsprep

from .paths import MAN_FILE, ROOT


def write_man_page(sink: TextIO) -> None:
    """Build a man page using click-man.

    We invoke `write_man_page` programmatically because CLI usage requires `dpsprep` to be installed
    as an entry point, which fails when building in source distributions.

    Furthermore, we must initialize the context manually because the more convenient `write_man_pages`
    function has a bug - see [1]

    [1]: https://github.com/click-contrib/click-man/pull/76
    """
    version, date_str = extract_version_and_date_from_changelog()
    ctx = click.Context(dpsprep, info_name=dpsprep.name)
    man_page = generate_man_page(ctx, version=version, date=date_str)
    examples = ROOT.joinpath('docs', 'examples.man').read_text(encoding='utf-8')

    sink.write(man_page)
    sink.write(examples)


def build_man_page() -> None:
    MAN_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MAN_FILE, 'w', encoding='utf-8') as man_file:
        write_man_page(man_file)


def write_man_md(sink: TextIO) -> None:
    buffer = io.StringIO()
    write_man_page(buffer)

    proc = subprocess.run(
        ['groff', '-mandoc', '-Tutf8', '-rLL=100n'],
        stdout=subprocess.PIPE,
        input=buffer.getvalue(),
        encoding='utf-8',
        check=True,
    )

    # The replacement patterns are based on https://stackoverflow.com/a/78367016/2756776
    # ruff: ignore[unraw-re-pattern]
    unescaped = re.sub('\x1B\\[[0-9;]*[JKmsu]', '', proc.stdout)

    for line in unescaped.splitlines(keepends=True):
        sink.write('    ')
        sink.write(line)


def build_man_md() -> None:
    with open(ROOT / 'docs' / 'dpsprep.1.md', 'w', encoding='utf-8') as file:
        write_man_md(file)


def extract_version_and_date_from_changelog() -> tuple[str, str]:
    with open(ROOT / 'CHANGELOG.md', encoding='utf-8') as file:
        for line in file:
            if match := re.match(r'## (?P<version>[^\s]+) - (?P<date>[\d-]+)', line):
                return match.group('version'), match.group('date')

        raise SystemExit('Could not determine the version and date from the changelog')
