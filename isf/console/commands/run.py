import console.command
import core


class CommandRun(console.command.Command):

    def __init__(self):
        super(CommandRun, self).__init__(name='run',
                                         description='Executes selected module',
                                         aliases=['start'])

    def run(self, args):
        output = [_ for _ in core.run_current_module()]
        # TODO create correct output parameter logging
        core.logger.info(str(output))
