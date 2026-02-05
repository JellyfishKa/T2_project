class QwenError(Exception):
    """Базовый класс ошибок Qwen"""

    pass


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
