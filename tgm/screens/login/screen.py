from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.reactive import reactive
from textual.widgets import Button, Input, LoadingIndicator, Static

from tgm.screens._base import TgmScreen
from tgm.screens.login.events import (
    CodeSubmitted,
    PasswordSubmitted,
    PhoneSubmitted,
    SmsRequested,
)
from tgm.screens.login.steps import CodeStep, LoginStep, PasswordStep, PhoneStep


class LoginError(Static):
    pass


class LoginScreen(TgmScreen):

    step: reactive[LoginStep] = reactive(PhoneStep())

    def __init__(self, loading: bool = False) -> None:
        super().__init__()
        self._loading = loading

    def compose(self) -> ComposeResult:
        yield Center(
            Middle(
                Static("[bold white]Telegram[/]", id="login-title"),
                Static("[dim white]Connecting...[/]", id="login-subtitle"),
                LoadingIndicator(id="login-spinner"),
                Input(placeholder="", id="login-input", disabled=True),
                LoginError("", id="login-error"),
                Button("Connect", variant="primary", id="connect-btn", disabled=True),
                Button(
                    "Send via SMS instead",
                    variant="default",
                    id="sms-btn",
                    disabled=True,
                ),
                id="login-box",
            )
        )

    def on_mount(self) -> None:
        if self._loading:
            self._show_spinner(True)
        else:
            self._render_step(self.step)

    def watch_step(self, step: LoginStep) -> None:
        self._render_step(step)

    def _reset_inputs(self) -> None:
        input_field = self.query_one("#login-input", Input)
        input_field.disabled = False
        input_field.password = False
        input_field.value = ""
        self.query_one("#connect-btn", Button).disabled = False
        self.query_one("#sms-btn", Button).display = False
        self.query_one("#sms-btn", Button).disabled = True
        self.query_one("#login-error", LoginError).update("")
        self._show_spinner(False)

    def _render_step(self, step: LoginStep) -> None:
        self._reset_inputs()

        title = self.query_one("#login-title", Static)
        subtitle = self.query_one("#login-subtitle", Static)
        input_field = self.query_one("#login-input", Input)
        btn = self.query_one("#connect-btn", Button)

        if isinstance(step, PhoneStep):
            title.update("[bold white]Telegram[/]")
            subtitle.update("[dim white]Enter your phone number[/]")
            input_field.placeholder = "Phone number"
            btn.label = "Connect"

        elif isinstance(step, CodeStep):
            title.update("[bold white]Verification code[/]")
            subtitle.update(f"[dim white]Check your Telegram app for {step.phone}[/]")
            input_field.placeholder = "12345"
            btn.label = "Verify"
            sms_btn = self.query_one("#sms-btn", Button)
            sms_btn.display = True
            sms_btn.disabled = False

        elif isinstance(step, PasswordStep):
            title.update("[bold white]Two-factor authentication[/]")
            subtitle.update("[dim white]Enter your password[/]")
            input_field.placeholder = "Password"
            input_field.password = True
            btn.label = "Sign in"

        input_field.focus()

    def _show_spinner(self, show: bool) -> None:
        self.query_one("#login-spinner", LoadingIndicator).display = show

    def _set_busy(self) -> None:
        self.query_one("#login-input", Input).disabled = True
        self.query_one("#connect-btn", Button).disabled = True
        self.query_one("#connect-btn", Button).label = "Please wait..."
        self.query_one("#sms-btn", Button).disabled = True
        self._show_spinner(True)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self._handle_submit(event.value.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect-btn":
            value = self.query_one("#login-input", Input).value.strip()
            if value:
                self._handle_submit(value)
        elif event.button.id == "sms-btn":
            self._request_sms()

    def _handle_submit(self, value: str) -> None:
        self._set_busy()
        step = self.step
        if isinstance(step, PhoneStep):
            self.post_message(PhoneSubmitted(value))
        elif isinstance(step, CodeStep):
            self.post_message(CodeSubmitted(step.phone, value))
        elif isinstance(step, PasswordStep):
            self.post_message(PasswordSubmitted(value))

    def _request_sms(self) -> None:
        self.query_one("#sms-btn", Button).disabled = True
        self.query_one("#sms-btn", Button).label = "Requesting SMS..."
        self._show_spinner(True)
        if isinstance(self.step, CodeStep):
            self.post_message(SmsRequested(self.step.phone))

    def advance_to_code(self, phone: str) -> None:
        self.step = CodeStep(phone=phone)

    def advance_to_password(self) -> None:
        phone = (
            self.step.phone if isinstance(self.step, (CodeStep, PasswordStep)) else ""
        )
        self.step = PasswordStep(phone=phone)

    def show_error(self, error: str) -> None:
        self.step = PhoneStep()
        # force render — watch_step won't fire if already at PhoneStep
        self._render_step(PhoneStep())
        self.query_one("#login-error", LoginError).update(f"[red]{escape(error)}[/]")
