import core.ISFFramework as ISFFramework
import core.console.ISFConsole as ISFConsole
from core import ISFProfiles


@ISFConsole.ISFConsoleCommand("presets_import",
                              description="Imports presets file",
                              params_desc=["presets file name"])
class CommandPresetsImport:

    def run(self, args):
        if len(args) < 2:
            ISFConsole.console_message(
                "Usage: %s <file name>" % (
                    args[0] if len(args) else "presets_import"),
                ISFConsole.LogLevel.ERROR)
            return
        name = args[1]
        try:
            ISFProfiles.import_preset_pack(name)
            ISFConsole.console_message("Presets imported successfully",
                                       ISFConsole.LogLevel.FINE)
        except Exception as e:
            ISFConsole.console_message("Unable to load preset file: " + str(e),
                                       ISFConsole.LogLevel.ERROR)
