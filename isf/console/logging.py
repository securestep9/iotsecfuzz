import logging
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.styles import Style

style = Style.from_dict({
    'debug': 'bg:ansigreen fg:ansiwhite',
    'info': '#4079FF',
    'warning': '#FF7700',
    'error': 'bg:#DE0000 fg:#FFFB00'
})

level_msg_styles = {
    logging.ERROR: 'fg="#DD0000"',
    logging.DEBUG: 'fg="#AAAAFF"',
    logging.INFO: 'fg="#FFFFFF"',
    logging.WARN: 'fg="#FFCC00"',
}


class ConsoleHandler(logging.Handler):

    def emit(self, record):
        try:
            msg = self.format(record)
            print_formatted_text(
                HTML(msg.format(level_msg_styles[record.levelno])), style=style)
        except Exception:
            self.handleError(record)


class ConsoleFormatter(logging.Formatter):

    def formatException(self, exc_info):
        exc_text = super(ConsoleFormatter, self).formatException(exc_info)
        return '<a fg="#FF0000">%s</a>' % exc_text
