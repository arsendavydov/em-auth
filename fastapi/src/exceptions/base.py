class DomainException(Exception):
    """Базовое доменное исключение приложения с HTTP-статусом."""

    def __init__(self, detail: str, status_code: int = 400) -> None:
        """
        Создает доменное исключение.

        Args:
            detail: Человекочитаемое описание ошибки.
            status_code: HTTP-статус, который должен быть возвращен клиенту.
        """

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

