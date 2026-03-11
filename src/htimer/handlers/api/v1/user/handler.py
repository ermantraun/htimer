from fastapi import APIRouter, status, Body
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from htimer.application.user import dto, interactors
from htimer.domain.entities import UserRole
from . import schemas

router = APIRouter(prefix='/users', tags=['User'], route_class=DishkaRoute)

@router.post('', status_code=status.HTTP_201_CREATED, name='Create user', 
             summary='Creates a new user',  response_model=schemas.CreateUserOut,
             responses={}
             )
async def create_user(interactor: FromDishka[interactors.CreateUserInteractor], user: schemas.CreateUserIn = Body(...)) -> schemas.CreateUserOut:
    result = await interactor.execute(dto.CreateUserInDTO(name=user.name, email=user.email, password=user.password, role=UserRole(user.role)))
    return schemas.CreateUserOut(user_uuid=result.user_uuid)

