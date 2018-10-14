import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole


@ISFConsole.ISFConsoleCommand("set",
                              description="Executes selected module",
                              params_desc=["parameter name", "value"])
class CommandSet:

    def run(self, args):
        if len(args) < 3:
            ISFConsole.console_message("Usage: set <parameter name> <value>",
                                       ISFConsole.LogLevel.ERROR)
            return
        if not ISFFramework.curr_module:
            ISFConsole.console_message("No module selected",
                                       ISFConsole.LogLevel.ERROR)
            return
        p_name = args[1]
        if p_name not in ISFFramework.curr_module.in_params:
            ISFConsole.console_message(
                "Module '%s' does not require parameter '%s'" % (
                    ISFConsole.curr_module_name, p_name),
                ISFConsole.LogLevel.ERROR)
            return
        p_value_str = " ".join(args[1:])
        p_value_str = p_value_str.replace(p_name, "", 1).strip()
        p_type = ISFFramework.curr_module.in_params[p_name].value_type
        p_value = None
        try:
            p_value = p_type(p_value_str)
        except ValueError:
            ISFConsole.console_message(
                "'%s' is not a valid value of type '%s'" % (
                    p_value_str, p_type.__name__), ISFConsole.LogLevel.ERROR)
            return
        ISFFramework.module_in_params[p_name] = p_value
        ISFConsole.console_message("%s ==> %s" % (p_name, p_value_str),
                                   ISFConsole.LogLevel.FINE)
