# Карта интеракторов: единый формат для визуализации

Формат: **Тематическая группа → Интерактор → I/O и валидация → Возможные исключения → Бизнес-правила**.

## Группа: daily_log

### CreateDailyLogInteractor

- **Вход/выход + валидация**
  - Вход: `CreateDailyLogInDTO`
  - Поля входа:
    - `date: str`
    - `creator_uuid: UUID`
    - `project_uuid: UUID`
    - `draft: bool`
    - `hours_spent: float`
    - `description: str`
    - `substage_uuid: UUID | None`
  - Выход: `dto.CreateDailyLogOutDTO`
  - Поля выхода:
    - `daily_log: entities.DailyLog`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `data.description is not None and len(data.description) > 0`
    - `len(description) <= 2000`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogAlreadyExistsError`
    - `common_exceptions.InvalidDate`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
    - `exceptions.DayliLogValidationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `clock_error`
    - `daily_log`
    - `project`
    - `project_members`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create daily log», операция прерывается.
  - Если дата не проходит проверку формата/валидности, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### UpdateDailyLogInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateDailyLogInDTO`
  - Поля входа:
    - `uuid: UUID`
    - `draft: bool | None`
    - `hours_spent: float | None`
    - `description: str | None`
    - `substage_uuid: UUID | None`
  - Выход: `dto.UpdateDailyLogOutDTO`
  - Поля выхода:
    - `daily_log: entities.DailyLog`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `data.description is not None or data.hours_spent is not None or data.substage_uuid is not None`
    - `len(description) <= 2000`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
    - `exceptions.DayliLogValidationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `updated`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update daily log», операция прерывается.
  - Если поле «description» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «draft» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «hours_spent» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «substage_uuid» передано во входных данных, то это поле участвует в изменении данных.
  - Если входные данные не проходят валидацию, операция прерывается.

### GetDailyLogInteractor

- **Вход/выход + валидация**
  - Вход: `GetDailyLogInDTO`
  - Поля входа:
    - `uuid: UUID`
  - Выход: `dto.GetDailyLogOutDTO`
  - Поля выхода:
    - `daily_log: entities.DailyLog`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `project_members`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get daily log», операция прерывается.

### CreateDailyLogFileInteractor

- **Вход/выход + валидация**
  - Вход: `CreateDailyLogFileInDTO`
  - Поля входа:
    - `daily_log_uuid: UUID`
    - `filename: str`
  - Выход: `dto.CreateDailyLogFileOutDTO`
  - Поля выхода:
    - `file: entities.DailyLogFile`
    - `action_link: ActionLink`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.FileAlreadyExistsError`
    - `common_exceptions.FileAlreadyExistsInStorageError`
    - `common_exceptions.FileStorageError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `storage_result`
    - `stored`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update daily log», операция прерывается.

### GetDailyLogFileInteractor

- **Вход/выход + валидация**
  - Вход: `GetDailyLogFileInDTO`
  - Поля входа:
    - `daily_log_uuid: UUID`
    - `file_uuid: UUID`
  - Выход: `dto.GetDailyLogFileOutDTO`
  - Поля выхода:
    - `file: entities.DailyLogFile`
    - `action_link: ActionLink`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.FileNotFoundError`
    - `common_exceptions.FileNotFoundInStorageError`
    - `common_exceptions.FileStorageError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `found`
    - `project_members`
    - `storage_result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get daily log», операция прерывается.

### RemoveDailyLogFileInteractor

- **Вход/выход + валидация**
  - Вход: `RemoveDailyLogFileInDTO`
  - Поля входа:
    - `daily_log_uuid: UUID`
    - `file_uuid: UUID`
  - Выход: `dto.GetDailyLogFileOutDTO`
  - Поля выхода:
    - `file: entities.DailyLogFile`
    - `action_link: ActionLink`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.FileNotFoundError`
    - `common_exceptions.FileNotFoundInStorageError`
    - `common_exceptions.FileStorageError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `removed`
    - `storage_result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update daily log», операция прерывается.

### GetDailyLogFileListInteractor

- **Вход/выход + валидация**
  - Вход: `GetDailyLogFileListInDTO`
  - Поля входа:
    - `daily_log_uuid: UUID`
  - Выход: `dto.GetDailyLogFileListOutDTO`
  - Поля выхода:
    - `files: list[tuple[entities.DailyLogFile, ActionLink]]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.DailyLogNotFoundError`
    - `common_exceptions.FileNotFoundError`
    - `common_exceptions.FileNotFoundInStorageError`
    - `common_exceptions.FileStorageError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_log`
    - `files`
    - `project_members`
    - `storage_result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get daily log», операция прерывается.

### GetDailyLogListInteractor

- **Вход/выход + валидация**
  - Вход: `GetDailyLogListInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `start_date: date`
    - `end_date: date`
    - `user_uuid: UUID | None`
  - Выход: `dto.GetDailyLogListOutDTO`
  - Поля выхода:
    - `daily_logs: list[entities.DailyLog]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.DayliLogAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `daily_logs`
    - `project`
    - `project_members`
    - `target`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get daily log list», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если поле «user_uuid» передано во входных данных, то это поле участвует в изменении данных.

## Группа: project

### CreateProjectInteractor

- **Вход/выход + валидация**
  - Вход: `CreateProjectInDTO`
  - Поля входа:
    - `name: str`
    - `description: str | None`
    - `start_date: str | None`
    - `end_date: str | None`
  - Выход: `dto.CreateProjectOutDTO`
  - Поля выхода:
    - `project: entities.Project`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 150`
    - `len(description) <= 500`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserAlreadyHasProjectError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.InvalidProjectDescriptionError`
    - `exceptions.InvalidProjectNameError`
    - `exceptions.ProjectAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `authorization_error`
    - `common_exceptions.InvalidTokenError('Current user not found')`
    - `current_user_uuid`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create project», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если поле «description» передано во входных данных, то это поле участвует в изменении данных.
  - Если входные данные не проходят валидацию, операция прерывается.

### UpdateProjectInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateProjectInDTO`
  - Поля входа:
    - `uuid: UUID`
    - `name: str | None`
    - `description: str | None`
    - `status: entities.ProjectStatus | None`
    - `start_date: str | None`
    - `end_date: str | None`
  - Выход: `dto.UpdateProjectOutDTO`
  - Поля выхода:
    - `project: entities.Project`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `any(asdict(data).values()) is True`
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 150`
    - `len(description) <= 500`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `common_exceptions.UserAlreadyHasProjectError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.AllFieldsNoneError`
    - `exceptions.CantUpdateProjectError`
    - `exceptions.InvalidProjectDescriptionError`
    - `exceptions.InvalidProjectNameError`
    - `exceptions.ProjectAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `authorization_error`
    - `current_user_uuid`
    - `exceptions.CantUpdateProjectError(error)`
    - `members`
    - `project`
    - `subscription`
    - `updated_project`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update project», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «update».
  - Если условия доменной модели нарушены, то изменение состояния не выполняется.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если поле «description» передано во входных данных, то это поле участвует в изменении данных.
  - Если входные данные не проходят валидацию, операция прерывается.

### GetProjectInteractor

- **Вход/выход + валидация**
  - Вход: `GetProjectInDTO`
  - Поля входа:
    - `project_uuid: UUID`
  - Выход: `dto.GetProjectsOutDTO`
  - Поля выхода:
    - `project: entities.Project`
    - `members: list[entities.User]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.ProjectAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `members`
    - `project`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get project», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.

### GetProjectListInteractor

- **Вход/выход + валидация**
  - Вход: `GetProjectListInDTO`
  - Выход: `dto.GetProjectListOutDTO`
  - Поля выхода:
    - `projects: list[entities.Project]`
  - Валидация (требования к значениям):
    - Явные булевы ограничения в `validators.py` не заданы для этого DTO.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.ProjectValidationError`
  - Явные raise в коде:
    - `current_user_uuid`
    - `projects`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если входные данные не проходят валидацию, операция прерывается.

### AddMembersToProjectInteractor

- **Вход/выход + валидация**
  - Вход: `AddMembersInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `members_uuids: list[UUID]`
  - Выход: `dto.AddMembersOutDTO`
  - Поля выхода:
    - `members: list[entities.MemberShip]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserAlreadyProjectMemberError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.ProjectAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `added_members`
    - `added_users`
    - `authorization_error`
    - `project`
    - `project_members`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update project», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.

### RemoveMembersFromProjectInteractor

- **Вход/выход + валидация**
  - Вход: `RemoveMembersInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `members_uuids: list[UUID]`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.MemberNotFound`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.ProjectAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `members`
    - `project`
    - `result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update project», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.

## Группа: reports

### CreateReportRequestInteractor

- **Вход/выход + валидация**
  - Вход: `CreateReportRequestInDTO`
  - Поля входа:
    - `project_id: UUID`
    - `start_date: date | None`
    - `end_date: date | None`
    - `target_users: list[UUID] | None`
  - Выход: `dto.CreateReportRequestOutDTO`
  - Поля выхода:
    - `report: entities.Report`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidDate`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.JobGatewayError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.InvalidPeriodError`
    - `exceptions.ReportAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `authorization_error`
    - `create_report_error`
    - `enqueue_error`
    - `project`
    - `project_members`
    - `users`
    - `validate_error`
    - `verify_period_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create report», операция прерывается.
  - Если переданы даты и период некорректен, то операция прерывается.
  - Если переданы целевые пользователи, то они дополнительно участвуют в проверках доступа и формировании результата.
  - Если валидация завершилась ошибкой, то операция прерывается.
  - Если период дат некорректен, то операция прерывается.

### CreateReportInteractor

- **Вход/выход + валидация**
  - Вход: `CreateReportInDTO`
  - Поля входа:
    - `report_id: str`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.FileAlreadyExistsInStorageError`
    - `common_exceptions.FileStorageError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.ReportNotFoundError`
    - `common_exceptions.RepositoryError`
    - `exceptions.ReportCreateError`
  - Явные raise в коде:
    - `daily_logs`
    - `error`
    - `project_members`
    - `report`
    - `report_update_error`
    - `tasks`

- **Бизнес-правила интерактора**
  - Формирует агрегированный отчёт, если запрошен сводный режим.

## Группа: stage

### CreateStageInteractor

- **Вход/выход + валидация**
  - Вход: `CreateStageInDTO`
  - Поля входа:
    - `name: str`
    - `project_uuid: UUID`
    - `parent_uuid: UUID | None`
    - `description: str | None`
    - `main_path: bool | None`
  - Выход: `dto.CreateStageOutDTO`
  - Поля выхода:
    - `stage: entities.Stage`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 150`
    - `len(description) <= 500`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ParentStageAlreadyHasMainSubStageError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageAlreadyExistsError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.InvalidStageDescriptionError`
    - `exceptions.InvalidStageNameError`
    - `exceptions.StageAuthorizationError`
    - `exceptions.StageCantCreateError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `created_stage`
    - `exceptions.StageCantCreateError(str(error))`
    - `parent_stage`
    - `project`
    - `project_members`
    - `subscription`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create stage», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «create».
  - Если условия доменной модели нарушены, то изменение состояния не выполняется.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### UpdateStageInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateStageInDTO`
  - Поля входа:
    - `uuid: UUID`
    - `name: str | None`
    - `description: str | None`
    - `status: str | None`
  - Выход: `dto.UpdateStageOutDTO`
  - Поля выхода:
    - `stage: entities.Stage`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `any(asdict(data).values()) is True`
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 150`
    - `len(description) <= 500`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.AllFieldsNoneError`
    - `exceptions.InvalidStageDescriptionError`
    - `exceptions.InvalidStageNameError`
    - `exceptions.StageAuthorizationError`
    - `exceptions.StageCantUpdateError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `exceptions.StageCantUpdateError(str(error))`
    - `project_members`
    - `stage`
    - `stage_children`
    - `subscription`
    - `updated_stage`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update stage», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «update».
  - Если условия доменной модели нарушены, то изменение состояния не выполняется.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если поле «description» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «name» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «status» передано во входных данных, то это поле участвует в изменении данных.
  - Если этап относится к главной ветке, то применяется отдельный сценарий обновления.
  - Если входные данные не проходят валидацию, операция прерывается.

### DeleteStageInteractor

- **Вход/выход + валидация**
  - Вход: `DeleteStageInDTO`
  - Поля входа:
    - `uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.StageAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `delete_result`
    - `project_members`
    - `stage`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update stage», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.

### GetStageListInteractor

- **Вход/выход + валидация**
  - Вход: `GetStageListInDTO`
  - Поля входа:
    - `project_uuid: UUID`
  - Выход: `dto.GetStageListOutDTO`
  - Поля выхода:
    - `stages: list[entities.Stage]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.StageAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `members`
    - `project`
    - `stages`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get stage list», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.

## Группа: subscription

### CreateSubscriptionInteractor

- **Вход/выход + валидация**
  - Вход: `CreateSubscriptionInDTO`
  - Поля входа:
    - `project_uuid: UUID`
  - Выход: `dto.CreateSubscriptionOutDTO`
  - Поля выхода:
    - `subscription: entities.Subscription`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionAlreadyExistsError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantCreateSubscription`
    - `exceptions.SubscriptionAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `created_subscription`
    - `exceptions.CantCreateSubscription(ensure_err)`
    - `project`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create subscription», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «create».
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если нарушены доменные ограничения сущности, то операция прерывается.

### UpdateSubscriptionInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateSubscriptionInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `auto_renew: bool | None`
    - `status: str | None`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantUpdateSubscription`
    - `exceptions.SubscriptionAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `auth_err`
    - `exceptions.CantUpdateSubscription(ensure_err)`
    - `project`
    - `subscription`
    - `update_result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update subscription», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «update».
  - Продолжает сценарий только при наличии значения «auth_err».
  - Если нарушены доменные ограничения сущности, то операция прерывается.

### ExtendSubscriptionInteractor

- **Вход/выход + валидация**
  - Вход: `ExtendSubscriptionInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `payment_uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.PaymentNotComplete`
    - `common_exceptions.PaymentNotExistsError`
    - `common_exceptions.PaymentNotFoundError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `exceptions.CantExtendSubscription`
  - Явные raise в коде:
    - `applied_to_subscription`
    - `exceptions.CantExtendSubscription('Платёж не завершён, невозможно продлить подписку.')`
    - `exceptions.CantExtendSubscription(ensure_res)`
    - `gateway_payment_id`
    - `payment`
    - `project`
    - `subscription`
    - `update_payment_res`
    - `update_res`
    - `verify`

- **Бизнес-правила интерактора**
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «extend».
  - Учитывает, что платёж может быть уже привязан к подписке.
  - Если нарушены ограничения продления подписки, то операция прерывается.
  - Не допускает повторную обработку уже завершённого платежа.

### ActivateSubscriptionInteractor

- **Вход/выход + валидация**
  - Вход: `ActivateSubscriptionInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `payment_uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.PaymentNotComplete`
    - `common_exceptions.PaymentNotExistsError`
    - `common_exceptions.PaymentNotFoundError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `exceptions.CantActivateSubscription`
  - Явные raise в коде:
    - `applied_to_subscription`
    - `exceptions.CantActivateSubscription(ensure_res)`
    - `gateway_payment_id`
    - `payment`
    - `project`
    - `subscription`
    - `update_payment_res`
    - `update_res`
    - `verify`

- **Бизнес-правила интерактора**
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «activate».
  - Учитывает, что платёж может быть уже привязан к подписке.
  - Если нарушены ограничения активации подписки, то операция прерывается.

### CreatePaymentInteractor

- **Вход/выход + валидация**
  - Вход: `CreatePaymentInDTO`
  - Поля входа:
    - `uuid: UUID`
    - `project_uuid: UUID`
    - `amount: float`
    - `currency: str`
  - Выход: `dto.CreatePaymentOutDTO`
  - Поля выхода:
    - `process_payment_link: str`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.PaymentFailedError`
    - `common_exceptions.PaymentNotFoundError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantCreatePayment`
    - `exceptions.SubscriptionAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `exceptions.CantCreatePayment(ensure_err)`
    - `gateway_payment`
    - `payment`
    - `project`
    - `subscription`
    - `update_gateway_id_result`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create payment», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «create».
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если нарушены доменные ограничения сущности, то операция прерывается.

### CompletePaymentInteractor

- **Вход/выход + валидация**
  - Вход: `CompletePaymentInDTO`
  - Поля входа:
    - `payment_uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.PaymentNotComplete`
    - `common_exceptions.PaymentNotExistsError`
    - `common_exceptions.PaymentNotFoundError`
    - `common_exceptions.PaymentRefundFailedError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `exceptions.CantCompletePayment`
  - Явные raise в коде:
    - `exceptions.CantCompletePayment('Платёж не подтверждён платёжной системой.')`
    - `exceptions.CantCompletePayment(complete_err)`
    - `gateway_payment_id`
    - `is_verified`
    - `payment`
    - `payment_error`
    - `refund_result`

- **Бизнес-правила интерактора**
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «complete».
  - Если платёж не проходит доменную проверку, то завершение операции прерывается.
  - Не завершает операцию, пока внешний статус не подтверждён.

### CompletePaymentAndUpdateSubscriptionInteractor

- **Вход/выход + валидация**
  - Вход: `CompletePaymentAndUpdateSubscriptionInDTO`
  - Поля входа:
    - `project_uuid: UUID`
    - `payment_uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.PaymentNotComplete`
    - `common_exceptions.PaymentNotExistsError`
    - `common_exceptions.PaymentNotFoundError`
    - `common_exceptions.PaymentRefundFailedError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.SubscriptionNotFoundError`
    - `exceptions.CantActivateSubscription`
    - `exceptions.CantCompletePayment`
    - `exceptions.CantExtendSubscription`
  - Явные raise в коде:
    - `activate_subscription_result`
    - `complete_payment_result`
    - `exceptions.CantActivateSubscription(ensure_activate_res)`
    - `exceptions.CantExtendSubscription(extend_ensure_res)`
    - `extend_subscription_result`
    - `subscription`

- **Бизнес-правила интерактора**
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «activate».
  - Операция выполняется только если выполнены доменные условия для «extend».
  - Продолжает сценарий только при наличии значения «activate_subscription_result».
  - Продолжает сценарий только при наличии значения «complete_payment_result».
  - Если не выполнены условия активации подписки, то операция активации прерывается.
  - Если не выполнены условия продления подписки, то операция продления прерывается.
  - Продолжает сценарий только при наличии значения «extend_subscription_result».

## Группа: task

### CreateTaskInteractor

- **Вход/выход + валидация**
  - Вход: `CreateTaskInDTO`
  - Поля входа:
    - `name: str`
    - `description: str`
    - `substage_uuid: UUID`
  - Выход: `dto.CreateTaskOutDTO`
  - Поля выхода:
    - `task: entities.Task`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 255`
    - `len(description) <= 2000`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.TaskAlreadyExistsError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantCreateTask`
    - `exceptions.TaskAuthorizationError`
    - `exceptions.TaskValidationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `created`
    - `exceptions.CantCreateTask(ensure_err)`
    - `project_members`
    - `subscription`
    - `substage`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create task», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «create».
  - Если нарушены доменные ограничения сущности, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### GetTaskInteractor

- **Вход/выход + валидация**
  - Вход: `GetTaskInDTO`
  - Поля входа:
    - `uuid: UUID`
  - Выход: `dto.GetTaskOutDTO`
  - Поля выхода:
    - `task: entities.Task`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.TaskAlreadyExistsError`
    - `common_exceptions.TaskNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.TaskAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `project`
    - `project_members`
    - `task`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get task», операция прерывается.

### UpdateTaskInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateTaskInDTO`
  - Поля входа:
    - `uuid: UUID`
    - `name: str | None`
    - `description: str | None`
    - `substage_uuid: UUID | None`
    - `completed: bool | None`
  - Выход: `dto.UpdateTaskOutDTO`
  - Поля выхода:
    - `task: entities.Task`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `any(asdict(data).values()) is True`
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 255`
    - `len(description) <= 2000`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.TaskAlreadyExistsError`
    - `common_exceptions.TaskNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantUpdateTask`
    - `exceptions.TaskAuthorizationError`
    - `exceptions.TaskValidationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `exceptions.CantUpdateTask(ensure_err)`
    - `project_members`
    - `subscription`
    - `substage`
    - `task`
    - `updated`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update task», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «update».
  - Если поле «completed» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «description» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «name» передано во входных данных, то это поле участвует в изменении данных.
  - Если поле «substage_uuid» передано во входных данных, то это поле участвует в изменении данных.
  - Если нарушены доменные ограничения сущности, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### DeleteTaskInteractor

- **Вход/выход + валидация**
  - Вход: `DeleteTaskInDTO`
  - Поля входа:
    - `uuid: UUID`
  - Выход: `None`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.TaskAlreadyExistsError`
    - `common_exceptions.TaskNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.TaskAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `delete_result`
    - `project_members`
    - `task`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «delete task», операция прерывается.

### GetTaskListInteractor

- **Вход/выход + валидация**
  - Вход: `ListTasksInDTO`
  - Поля входа:
    - `substage_uuid: UUID`
  - Выход: `dto.ListTasksOutDTO`
  - Поля выхода:
    - `tasks: list[entities.Task]`
  - Валидация: явные булевы ограничения в отдельном `validator` не заданы; применяются только типы DTO и проверки в ходе выполнения интерактора.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.StageNotFoundError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.TaskAuthorizationError`
  - Явные raise в коде:
    - `actor`
    - `actor_uuid`
    - `authorization_error`
    - `project_members`
    - `substage`
    - `tasks`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get task», операция прерывается.

## Группа: user

### CreateUserInteractor

- **Вход/выход + валидация**
  - Вход: `CreateUserInDTO`
  - Поля входа:
    - `name: str`
    - `email: str`
    - `password: str`
    - `role: entities.UserRole`
  - Выход: `dto.CreateUserOutDTO`
  - Поля выхода:
    - `user_uuid: UUID`
  - Валидация (требования к значениям):
    - Явные булевы ограничения в `validators.py` не заданы для этого DTO.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.EmailAlreadyExistsError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.UserAuthorizationError`
    - `exceptions.UserValidationError`
  - Явные raise в коде:
    - `auth_error`
    - `created_user`
    - `current_user`
    - `current_user_uuid`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «create user», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### GetUsersListInteractor

- **Вход/выход + валидация**
  - Вход: `GetUserListInDTO`
  - Поля входа:
    - `projects_names: set[str]`
    - `is_active: bool | None`
  - Выход: `dto.GetUserListOutDTO`
  - Поля выхода:
    - `users: list[entities.User]`
  - Валидация (требования к значениям):
    - Явные булевы ограничения в `validators.py` не заданы для этого DTO.

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.ProjectNotFoundError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.UserAuthorizationError`
    - `exceptions.UserValidationError`
  - Явные raise в коде:
    - `auth_error`
    - `current_user`
    - `current_user_uuid`
    - `user_projects`
    - `users`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «get users list», операция прерывается.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если входные данные не проходят валидацию, операция прерывается.

### LoginUserInteractor

- **Вход/выход + валидация**
  - Вход: `LoginUserInDTO`
  - Поля входа:
    - `email: str`
    - `password: str`
  - Выход: `dto.LoginUserOutDTO`
  - Поля выхода:
    - `token: str`
    - `user_uuid: UUID`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `email is not None and len(email.strip()) > 0`
    - `re.match('^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$', email) is not None`
    - `len(email) <= 254`
    - `password is not None`
    - `len(password) >= 8`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.EmailAlreadyExistsError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.InvalidCredentialsError`
    - `exceptions.UserValidationError`
  - Явные raise в коде:
    - `exceptions.InvalidCredentialsError('Неверные учетные данные.')`
    - `updated_user`
    - `user`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если пароль не совпадает с сохранённым хэшем, то вход отклоняется.
  - Если входные данные не проходят валидацию, операция прерывается.

### ResetUserPasswordInteractor

- **Вход/выход + валидация**
  - Вход: `ResetUserPasswordInDTO`
  - Поля входа:
    - `user_uuid: UUID | None`
    - `new_password: str`
  - Выход: `None`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `password is not None`
    - `len(password) >= 8`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantResetPasswordError`
    - `exceptions.UserAuthorizationError`
    - `exceptions.UserValidationError`
  - Явные raise в коде:
    - `auth_error`
    - `current_user`
    - `current_user_uuid`
    - `exceptions.CantResetPasswordError(error)`
    - `target_user`
    - `updated_user`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «reset user password», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «reset password».
  - Если условия доменной модели нарушены, то изменение состояния не выполняется.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Если целевой пользователь не указан, применяется текущий пользователь.
  - Если входные данные не проходят валидацию, операция прерывается.

### UpdateUserInteractor

- **Вход/выход + валидация**
  - Вход: `UpdateUserInDTO`
  - Поля входа:
    - `uuid: UUID | None`
    - `name: str | None`
    - `email: str | None`
    - `password: str | None`
    - `status: str | None`
    - `role: str | None`
  - Выход: `dto.UpdateUserOutDTO`
  - Поля выхода:
    - `user: entities.User`
  - Валидация (требования к значениям):
    - Булевы ограничения (каждое выражение должно быть `True`):
    - `name is not None and len(name.strip()) > 0`
    - `len(name.strip()) <= 150`
    - `email is not None and len(email.strip()) > 0`
    - `re.match('^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$', email) is not None`
    - `len(email) <= 254`
    - `password is not None`
    - `len(password) >= 8`

- **Возможные исключения**
  - Из сигнатуры execute:
    - `common_exceptions.EmailAlreadyExistsError`
    - `common_exceptions.InvalidTokenError`
    - `common_exceptions.RepositoryError`
    - `common_exceptions.UserNotFoundError`
    - `exceptions.CantUpdateError`
    - `exceptions.UserAuthorizationError`
    - `exceptions.UserValidationError`
  - Явные raise в коде:
    - `auth_error`
    - `current_user`
    - `current_user_uuid`
    - `exceptions.CantUpdateError(error)`
    - `target_user`
    - `updated_user`
    - `validation_error`

- **Бизнес-правила интерактора**
  - Если текущий пользователь не определён, не найден или токен некорректен, операция прерывается.
  - Если политика доступа запрещает действие «update user», операция прерывается.
  - Если доменные ограничения не выполнены, изменение данных не выполняется.
  - Операция выполняется только если выполнены доменные условия для «update».
  - Если условия доменной модели нарушены, то изменение состояния не выполняется.
  - Если проверка авторизации возвращает запрет, то операция прерывается.
  - Выполняет альтернативный сценарий, когда «data.uuid» отсутствует.
  - Если входные данные не проходят валидацию, операция прерывается.
