from . import dto, exceptions


class CreateDailyLogValidator:
    """Validator for CreateDailyLogInDTO. Returns None on success or a DayliLogValidationError on failure."""

    def validate(
        self, data: dto.CreateDailyLogInDTO
    ) -> None | exceptions.DayliLogValidationError:

        if data.description:
            if (err := _validate_description(data.description)) is not None:
                return err

        return None


def _validate_description(
    description: str,
) -> exceptions.InvalidDailyLogDescriptionError | None:
    if len(description) > 2000:
        return exceptions.InvalidDailyLogDescriptionError(
            "Описание не может превышать 2000 символов."
        )
    return None


class UpdateDailyLogValidator:
    """Validator for UpdateDailyLogInDTO. Ensures at least one updatable field is present and validates description."""

    def validate(
        self, data: dto.UpdateDailyLogInDTO
    ) -> None | exceptions.DayliLogValidationError:
        if (
            data.description is None
            and data.hours_spent is None
            and data.substage_uuid is None
        ):
            return exceptions.DayliLogValidationError("Нет полей для обновления.")

        if data.description is not None:
            if (err := _validate_description(data.description)) is not None:
                return err

        return None
