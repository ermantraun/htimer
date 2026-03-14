import nox


@nox.session
def tests(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("pytest")


@nox.session(python=["3.14"])
def coverage(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("coverage", "run", "-m", "pytest")
    session.notify("combine")


@nox.session(default=False)
def combine(session: nox.Session) -> None:
    session.install(".[dev]")
    session.run("coverage", "combine")
    session.run("coverage", "report", "-m")
    session.run("coverage", "html")


@nox.session
def linter(session: nox.Session) -> None:
    session.install("ruff>=0.15.6", "black>=23.3.0")
    session.run("ruff", "check", "--fix", "--show-fixes", ".")
    session.run("black", ".")
