from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneStep:
    pass


@dataclass(frozen=True)
class CodeStep:
    phone: str


@dataclass(frozen=True)
class PasswordStep:
    phone: str


LoginStep = PhoneStep | CodeStep | PasswordStep
