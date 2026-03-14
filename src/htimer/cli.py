# app/cli.py
import typer
import uvicorn

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def dev(
    host: str = "127.0.0.1",
    port: int = 8000,
):
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
    )


@cli.command()
def prod(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 4,
):
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        workers=workers,
    )


def main():
    cli()
