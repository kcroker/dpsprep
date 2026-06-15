import pathlib
import re
import subprocess

import click
from click_man.core import generate_man_page

from dpsprep.cli import dpsprep


ROOT = pathlib.Path(__file__).parent.parent.parent


def build_man_page() -> None:
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

    with open('docs/dpsprep.1', 'w') as man_file, open('docs/examples.man') as example_file:
        man_file.write(man_page)
        man_file.write(example_file.read())


def build_man_md() -> None:
    proc = subprocess.run(
        ['groff', '-mandoc', '-Tutf8', '-rLL=100n', 'docs/dpsprep.1'],
        stdout=subprocess.PIPE,
        encoding='utf-8',
        check=True,
    )

    # The replacement patterns are based on https://stackoverflow.com/a/78367016/2756776
    unescaped = re.sub('\x1B\\[[0-9;]*[JKmsu]', '', proc.stdout)

    with open('docs/dpsprep.1.md', 'w') as file:
        for line in unescaped.splitlines(keepends=True):
            file.write('    ')
            file.write(line)


def extract_version_and_date_from_changelog() -> tuple[str, str]:
    with open(ROOT / 'CHANGELOG.md') as file:
        for line in file:
            if match := re.match(r'## (?P<version>[^\s]+) - (?P<date>[\d-]+)', line):
                return match.group('version'), match.group('date')

        raise SystemExit('Could not determine the version and date from the changelog')
