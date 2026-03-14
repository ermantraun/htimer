from . import dto, exceptions


class CreateReportRequestValidator:
    @staticmethod
    def validate(
        data: dto.CreateReportRequestInDTO,
    ) -> exceptions.InvalidPeriodError | None:
        if data.start_date and data.end_date:
            if data.start_date > data.end_date:
                return exceptions.InvalidPeriodError(
                    "Дата начала не может быть позже даты окончания."
                )
        return None
