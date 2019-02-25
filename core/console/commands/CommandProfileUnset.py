import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from core import ISFProfiles


@ISFConsole.ISFConsoleCommand("profile_unset",
                              description="Unsets selected profile",
                              params_desc=["profile name"],
                              aliases=["punset", "pr_unset"])
class CommandUse:

    def run(self, args):
        ISFConsole.curr_profile_name = None
        ISFFramework.unset_profile()
