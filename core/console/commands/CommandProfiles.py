from tabulate import tabulate

import core.console.ISFConsole as ISFConsole
import core.ISFProfiles as ISFProfiles


@ISFConsole.ISFConsoleCommand("profile_list",
                              description="Lists all loaded profiles",
                              aliases=["profiles", "plist", "pr_list"])
class CommandProfiles:

    def run(self, args):
        ISFConsole.console_message("Loaded profiles: ",
                                   ISFConsole.LogLevel.FINE)
        print(tabulate(
            [[n, m.description, len(m.presets)] for n, m in
             ISFProfiles.loaded_profiles.items()],
            headers=["Name", "Description", "Number of presets"],
            tablefmt="psql"))
