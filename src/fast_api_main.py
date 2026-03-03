import dishka
from dishka.integrations.fastapi import setup_dishka
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from handlers.api.v1 import routers, exception_handlers
from ioc import AppProvider
from config import Config
from utils import MessageBrokerInitializer


def fast_api_app() -> fastapi.FastAPI:

    app = fastapi.FastAPI(
        title=Config.fastapi.title,
        version=Config.fastapi.version,
        description=Config.fastapi.description,
        on_startup=[MessageBrokerInitializer(Config()).init]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.fastapi.allow_origins,
        allow_credentials=Config.fastapi.allow_credentials,
        allow_methods=Config.fastapi.allow_methods,
        allow_headers=Config.fastapi.allow_headers,
    )

    app.include_router(*routers)

    app.exception_handlers.update(*exception_handlers)

    return app

def create_app() -> fastapi.FastAPI:
    api_app = fastapi.FastAPI()
    container = dishka.make_async_container(
        AppProvider(),
        context={Config: Config()},
    )
    setup_dishka(container, api_app)
    return api_app


app = create_app()