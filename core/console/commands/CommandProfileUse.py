import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from core import ISFProfiles


@ISFConsole.ISFConsoleCommand("profile_use",
                              description="Selects profile to use",
                              params_desc=["profile name"],
                              aliases=["puse", "pr_use"])
class CommandUse:

    def run(self, args):
        if len(args) < 2:
            ISFConsole.console_message(
                "Usage: %s <profile name>" % (
                    args[0] if len(args) else "profile_use"),
                ISFConsole.LogLevel.ERROR)
            return
        name = args[1]
        if name not in ISFProfiles.loaded_profiles:
            ISFConsole.console_message("No profile named %s" % name,
                                       ISFConsole.LogLevel.ERROR)
            return
        ISFConsole.curr_profile_name = name
        ISFFramework.use_profile(name)
        ISFConsole.console_message("Profile set: %s" % name,
                                   ISFConsole.LogLevel.FINE)
