import click

from . import docs


@click.group()
def docs_cli() -> None:
    pass


@docs_cli.command()
def build_man_page() -> None:
    docs.build_man_page()


@docs_cli.command()
def build_dynamic_docs() -> None:
    docs.build_man_md()


if __name__ == '__main__':
    docs_cli()
