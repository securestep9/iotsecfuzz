import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from core import ISFProfiles
from shutil import copyfile


@ISFConsole.ISFConsoleCommand("profile_import",
                              description="Imports profile file",
                              params_desc=["presets file name"],
                              aliases=["pimport", "pr_import"])
class CommandProfileImport:

    def run(self, args):
        if len(args) < 2:
            ISFConsole.console_message(
                "Usage: %s <file name>" % (
                    args[0] if len(args) else "presets_import"),
                ISFConsole.LogLevel.ERROR)
            return
        name = args[1]
        try:
            file_name = name.replace("\\", "/").split("/")[-1]
            copyfile(name, "profiles/" + file_name)
            ISFProfiles.import_profile("profiles/" + file_name)
            ISFConsole.console_message("Profile imported successfully",
                                       ISFConsole.LogLevel.FINE)
        except Exception as e:
            ISFConsole.console_message("Unable to load profile file: " + str(e),
                                       ISFConsole.LogLevel.ERROR)
