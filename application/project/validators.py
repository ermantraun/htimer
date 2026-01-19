from dataclasses import asdict
import dto
from . import exceptions



class CreateProjectValidator:
    """Validator for CreateProjectInDTO. Only validates and returns None or raises ProjectValidationError."""

    def validate(self, data: dto.CreateProjectInDTO) ->  None | exceptions.InvalidProjectDescriptionError | exceptions.InvalidProjectNameError:
        if (err := _validate_name(data.name)) is not None:
            return err
        
        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err
        return None

class UpdateProjectValidator:
    """Validator for UpdateProjectInDTO. Only validates and returns None or raises ProjectValidationError."""

    def validate(self, data: dto.UpdateProjectInDTO) ->  None | exceptions.InvalidProjectDescriptionError | exceptions.InvalidProjectNameError | exceptions.AllFieldsNoneError:
        
        if any(asdict(data).values()) is False:
            return exceptions.AllFieldsNoneError("Все поля для обновления отсутствуют.")
        
        if data.name is not None:
            if (err := _validate_name(data.name)) is not None:
                return err
        
        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err
        return None

def _validate_name(name: str) -> exceptions.InvalidProjectNameError | None:
    
    if not name or not name.strip():
        return exceptions.InvalidProjectNameError("Имя пользователя не может быть пустым.")
    if len(name.strip()) > 150:
        return exceptions.InvalidProjectNameError("Имя пользователя слишком длинное.")
    return None

def _validate_description(description: str) -> exceptions.InvalidProjectDescriptionError | None:
    if len(description) > 500:
        return exceptions.InvalidProjectDescriptionError("Описание проекта не может превышать 500 символов.")
    return None