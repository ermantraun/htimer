from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import dishka
from infrastructure.db.repositories import UserRepository
from ioc import common
from config import Config


async def main():
    container = dishka.make_async_container(common.ConfigProvider(), common.DBProvider(), context={Config: Config()})
    
    
    async with container() as request_scope:
        
        session = await request_scope.get(AsyncSession)
        
        _ = UserRepository(session, Config())


if __name__ == '__main__':
    
    
    asyncio.run(main())