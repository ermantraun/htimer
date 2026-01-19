import dto
from . import exceptions


class CreateDailyLogValidator:
    """Validator for CreateDailyLogInDTO. Returns None on success or a DayliLogValidationError on failure."""

    def validate(self, data: dto.CreateDailyLogInDTO) -> None | exceptions.DayliLogValidationError:

        if data.description:
            if (err := _validate_description(data.description)) is not None:
                return err

        return None



def _validate_description(description: str) -> exceptions.InvalidDailyLogDescriptionError | None:
    if len(description) > 2000:
        return exceptions.InvalidDailyLogDescriptionError("Описание не может превышать 2000 символов.")
    return None


 