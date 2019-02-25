import console.command
import core


class CommandSet(console.command.Command):

    def __init__(self):
        super(CommandSet, self).__init__(name='set',
                                         description='Sets current modules ' +
                                                     'input parameter value',
                                         param_descriptions=['parameter name',
                                                             'value'],
                                         min_args_number=2)

    def run(self, args):
        core.set_parameter(args[0], ' '.join(args[1:]))
        core.logger.info('%s ==> %s' % (args[0], ' '.join(args[1:])))
