import dto
from dataclasses import asdict
from . import exceptions


class CreateTaskValidator:
    """Validator for CreateTaskInDTO. Returns None on success or a specific TaskValidationError on failure."""

    def validate(self, data: dto.CreateTaskInDTO) -> None | exceptions.InvalidTaskNameError | exceptions.InvalidTaskDescriptionError:
        if (err := _validate_name(data.name)) is not None:
            return err

        # description is required in CreateTaskInDTO; validate directly
        if (err := _validate_description(data.description)) is not None:
            return err

        return None


class UpdateTaskValidator:
    """Validator for UpdateTaskInDTO. Returns None on success or a specific TaskValidationError on failure."""

    def validate(self, data: dto.UpdateTaskInDTO) -> None | exceptions.InvalidTaskNameError | exceptions.InvalidTaskDescriptionError | exceptions.AllFieldsNoneError:
        # ensure at least one field present
        if any(asdict(data).values()) is False:
            return exceptions.AllFieldsNoneError("Все поля для обновления отсутствуют.")

        if data.name is not None:
            if (err := _validate_name(data.name)) is not None:
                return err

        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err

        return None


def _validate_name(name: str) -> exceptions.InvalidTaskNameError | None:
    if not name or not name.strip():
        return exceptions.InvalidTaskNameError("Название задачи не может быть пустым.")
    if len(name.strip()) > 255:
        return exceptions.InvalidTaskNameError("Название задачи не может превышать 255 символов.")
    return None


def _validate_description(description: str) -> exceptions.InvalidTaskDescriptionError | None:
    if len(description) > 2000:
        return exceptions.InvalidTaskDescriptionError("Описание не может превышать 2000 символов.")
    return None
