import nox

# Пока не закончен

@nox.session
def tests(session: nox.Session) -> None:
    session.install(".", "pytest", 'pytest_asyncio')
    session.run("pytest")