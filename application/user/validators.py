
from domain import entities
from . import exceptions
from . import dto 
import re


class CreateUserValidator:
    
    def validate(self, user: entities.User, dto: dto.CreateUserInDTO) -> exceptions.UserValidationError | None:
        if not user.can_create_users():
            return exceptions.UserCannotCreateUsersError("Пользователь не имеет прав для создания других пользователей.")
        # Общие проверки для создания пользователя
        return _validate_common_create(dto)
        
class UpdateUserValidator:
    
    def validate(self, user: entities.User, dto: dto.UpdateUserInDTO, 
                 admin: entities.User | None = None, user_projects: set[entities.Project] | None = None, 
                 admin_projects: set[entities.Project] | None = None) -> exceptions.UserValidationError | None:

        # Если админ пытаетcя обновлять другого пользователя — он должен быть 
        # администратором в проекте пользователя, либо его создателем
        if is_remote_update := admin is not None and admin.uuid != user.uuid and not admin.can_update_users(admin_projects_names={p.name for p in admin_projects} if admin_projects else set(),
                                                        user_projects_names={p.name for p in user_projects} if user_projects else set()):
            return exceptions.AdminIsNotProjectOwner("Пользователь не имеет прав для изменения других пользователей.")
        # Проверки для полей, если они предоставлены
        # Общие имя/почта/пароль
        name = dto.name
        email = dto.email
        password = dto.password

        if name is not None:
            if (err := _validate_name(name)) is not None:
                return err

        if email is not None:
            if (err := _validate_email(email)) is not None:
                return err

        if password is not None:
            if (err := _validate_password(password)) is not None:
                return err

        # Запрещаем самопроизвольное повышение привилегий: обычный пользователь не может менять is_admin
        if dto.is_admin is not None:
            # изменение флага is_admin возможно только при административном обновлении
            if not is_remote_update:
                return exceptions.CannotChangeAdminSelfError("Нельзя изменять права администратора самому себе.")

        # Изменение статуса активности/архивации только для админа при редактировании другого пользователя
        if (dto.is_active is not None or dto.is_archived is not None) and not is_remote_update:
            # разрешим пользователю изменять лишь некоторые свои поля, но не активность/архив
            return exceptions.CannotChangeStatusSelfError("Нельзя менять статус активности или архивности своего аккаунта.")

        return None
    
class GetUsersListValidator:
    
    def validate(self, dto: dto.GetUsersInDto, user: entities.User, user_projects_names: set[str], ) -> exceptions.UserValidationError | None:
        # Проверяем почему доступ запрещён — вернём более конкретную ошибку
        if not user.is_admin:
            return exceptions.UserIsNotAdmin("Только администратор может получать список пользователей.")

        if dto.projects_names is not None:
            requested = set(dto.projects_names)
            if not user_projects_names <= requested:
                return exceptions.AdminIsNotProjectOwner("Запрошены проекты, к которым у пользователя нет доступа.")
            

        # status может быть True/False/None — никаких дополнительных проверок
        return None


# --- вспомогательные проверки ---
def _validate_common_create(dto: dto.CreateUserInDTO) -> exceptions.UserValidationError | None:
    if (err := _validate_name(dto.name)) is not None:
        return err

    if (err := _validate_email(dto.email)) is not None:
        return err

    if (err := _validate_password(dto.password)) is not None:
        return err

    return None


def _validate_name(name: str) -> exceptions.UserValidationError | None:
    if not name or not name.strip():
        return exceptions.InvalidNameError("Имя пользователя не может быть пустым.")
    if len(name.strip()) > 150:
        return exceptions.InvalidNameError("Имя пользователя слишком длинное.")
    return None


def _validate_email(email: str) -> exceptions.UserValidationError | None:
    if not email or not email.strip():
        return exceptions.InvalidEmailError("Email не может быть пустым.")
    email = email.strip()
    # Простая проверка email
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return exceptions.InvalidEmailError("Неверный формат email.")
    if len(email) > 254:
        return exceptions.InvalidEmailError("Email слишком длинный.")
    return None


def _validate_password(password: str | None) -> exceptions.UserValidationError | None:
    if password is None:
        return exceptions.InvalidPasswordError("Некорректный пароль.")
    if len(password) < 8:
        return exceptions.InvalidPasswordError("Пароль должен быть не менее 8 символов.")
    return None