class QwenError(Exception):
    """Базовый класс ошибок Qwen"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class QwenTimeoutError(QwenError):
    pass


class QwenAuthError(QwenError):
    pass


class QwenRateLimitError(QwenError):
    pass


class QwenServerError(QwenError):
    pass


class QwenValidationError(QwenError):
    pass


class TProError(Exception):
    """Базовый класс ошибок T-Pro"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class TProTimeoutError(TProError):
    pass


class TProAuthError(TProError):
    pass


class TProRateLimitError(TProError):
    pass


class TProServerError(TProError):
    pass


class TProValidationError(TProError):
    pass
