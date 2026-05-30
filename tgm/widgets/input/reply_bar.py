from textual.widgets import Static


class ReplyBar(Static):

    def show(self, content: str | None) -> None:
        if content:
            self.update(content)
            self.display = True
        else:
            self.update("")
            self.display = False
