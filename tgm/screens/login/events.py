from textual.message import Message


class LoginEvent(Message):
    # namespace ties all subclasses to the "on_login_screen_*" handler convention
    NAMESPACE = "login_screen"


class PhoneSubmitted(LoginEvent):
    def __init__(self, phone: str) -> None:
        super().__init__()
        self.phone = phone


class CodeSubmitted(LoginEvent):
    def __init__(self, phone: str, code: str) -> None:
        super().__init__()
        self.phone = phone
        self.code = code


class PasswordSubmitted(LoginEvent):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.password = password


class SmsRequested(LoginEvent):
    def __init__(self, phone: str) -> None:
        super().__init__()
        self.phone = phone
