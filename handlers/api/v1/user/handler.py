from fastapi import APIRouter, status
from dishka.integrations.fastapi import FromDishka, DishkaRoute
from application.user import dto, interactors

router = APIRouter(prefix='/users', tags=['User'], route_class=DishkaRoute)

@router.post('', status_code=status.HTTP_201_CREATED, name='Create user', 
             summary='Creates a new user',
             responses={status.HTTP_422_UNPROCESSABLE_ENTITY: user_responses['create'][422], 
                        status.HTTP_409_CONFLICT: user_responses['create'][409],
                        status.HTTP_201_CREATED: user_responses['create'][201]}
             )
async def create_user(user: schemas, interactor: FromDishka[interactors.CreateUserInteractor]) -> dict:
    result = await interactor(dto.CreateUserInDTO(
        login=user.login,
        email=user.email,
        password=user.password
    ))
    return {"token": result.token}