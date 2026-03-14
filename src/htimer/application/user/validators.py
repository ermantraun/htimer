import re

from . import dto, exceptions


class CreateUserValidator:
    """Validator for CreateUser DTO - only checks data format/constraints."""

    def validate(
        self, dto_data: dto.CreateUserInDTO
    ) -> exceptions.UserValidationError | None:
        return _validate_common_create(dto_data)


class UpdateUserValidator:
    """Validator for UpdateUser DTO - only checks data format/constraints."""

    def validate(
        self, dto_data: dto.UpdateUserInDTO
    ) -> exceptions.UserValidationError | None:
        if dto_data.name is not None:
            if (err := _validate_name(dto_data.name)) is not None:
                return err

        if dto_data.email is not None:
            if (err := _validate_email(dto_data.email)) is not None:
                return err

        if dto_data.password is not None:
            if (err := _validate_password(dto_data.password)) is not None:
                return err

        return None


class ResetUserPasswordValidator:
    """Validator for ResetPassword DTO - only checks data format/constraints."""

    def validate(
        self, dto_data: dto.ResetUserPasswordInDTO
    ) -> exceptions.UserValidationError | None:
        if (err := _validate_password(dto_data.new_password)) is not None:
            return err

        return None


class LoginUserValidator:
    """Validator for LoginUser DTO - only checks data format/constraints."""

    def validate(
        self, dto_data: dto.LoginUserInDTO
    ) -> exceptions.UserValidationError | None:
        if (err := _validate_email(dto_data.email)) is not None:
            return err

        if (err := _validate_password(dto_data.password)) is not None:
            return err

        return None


class GetUsersListValidator:
    """Validator for GetUsersList DTO - only checks data format/constraints."""

    def validate(
        self, dto_data: dto.GetUserListInDTO
    ) -> exceptions.UserValidationError | None:
        return None


def _validate_common_create(
    dto_data: dto.CreateUserInDTO,
) -> exceptions.UserValidationError | None:
    if (err := _validate_name(dto_data.name)) is not None:
        return err

    if (err := _validate_email(dto_data.email)) is not None:
        return err

    if (err := _validate_password(dto_data.password)) is not None:
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
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return exceptions.InvalidEmailError("Неверный формат email.")
    if len(email) > 254:
        return exceptions.InvalidEmailError("Email слишком длинный.")
    return None


def _validate_password(password: str | None) -> exceptions.UserValidationError | None:
    if password is None:
        return exceptions.InvalidPasswordError("Некорректный пароль.")
    if len(password) < 8:
        return exceptions.InvalidPasswordError(
            "Пароль должен быть не менее 8 символов."
        )
    return None
