import dto, exceptions
from dataclasses import asdict

class CreateStageValidator:
    """Validator for CreateStageInDTO. Only validates and returns None or raises StageValidationError."""

    def validate(self, data: dto.CreateStageInDTO) ->  None | exceptions.InvalidStageNameError | exceptions.InvalidStageDescriptionError:
        if (err := _validate_name(data.name)) is not None:
            return err
        
        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err
        return None
    


class UpdateStageValidator:
    """Validator for UpdateStageInDTO. Only validates and returns None or raises StageValidationError."""

    def validate(self, data: dto.UpdateStageInDTO) ->  None | exceptions.InvalidStageNameError | exceptions.InvalidStageDescriptionError | exceptions.AllFieldsNoneError:
        
        if any(asdict(data).values()) is False:
            return exceptions.AllFieldsNoneError("Все поля для обновления отсутствуют.")
        
        if data.name is not None:
            if (err := _validate_name(data.name)) is not None:
                return err
        
        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err
        return None
    
    
    
def _validate_name(name: str) -> exceptions.InvalidStageNameError | None:
    
    if not name or not name.strip():
        return exceptions.InvalidStageNameError("Имя этапа не может быть пустым.")
    if len(name.strip()) > 150:
        return exceptions.InvalidStageNameError("Имя этапа слишком длинное.")
    return None

def _validate_description(description: str) -> exceptions.InvalidStageDescriptionError | None:
    if len(description) > 500:
        return exceptions.InvalidStageDescriptionError("Описание этапа не может превышать 500 символов.")
    return None
