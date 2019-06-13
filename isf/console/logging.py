import logging
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.styles import Style
import html
import subprocess
import os

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


def log_process_output(proc, prefix='$'):
    while True:
        next_line = proc.stdout.readline().decode()
        result = proc.poll()
        if next_line == '' and result is not None:
            return result
        next_line = html.escape(
            next_line.replace('{', '{{').replace('}', '}}'))
        print_formatted_text(
            HTML('<a fg="#808000">[%s]</a> <a fg="#FFFFFF">%s</a>' % (
                prefix, next_line.rstrip('\r\n').rstrip('\n'))))


def run_with_logger(cmd, *, prefix='$',
                    error_msg='Process finished with non-zero exit code'):
    proc = subprocess.Popen(
        cmd, env=os.environ, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

    result = log_process_output(proc, prefix=prefix)
    if result != 0:
        raise RuntimeError(error_msg)


class ConsoleHandler(logging.Handler):

    def emit(self, record):
        try:
            record.msg = html.escape(
                record.msg.replace('{', '{{').replace('}', '}}'))
            msg = self.format(record)
            print_formatted_text(
                HTML(msg.format(level_msg_styles[record.levelno])), style=style)
        except Exception:
            self.handleError(record)


class ConsoleFormatter(logging.Formatter):

    def formatException(self, exc_info):
        exc_text = super(ConsoleFormatter, self).formatException(exc_info)
        exc_text = html.escape(
            exc_text.replace('{', '{{').replace('}', '}}'))
        return '<a fg="#FF0000">%s</a>' % exc_text
