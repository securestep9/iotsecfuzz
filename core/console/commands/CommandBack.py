import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole


@ISFConsole.ISFConsoleCommand("back", description="Clears the current module")
class CommandBack:

    def run(self, args):
        ISFFramework.curr_module = None
        ISFConsole.curr_module_name = None
        ISFFramework.module_in_params = dict()
