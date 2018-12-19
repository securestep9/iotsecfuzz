from core.ISFFramework import ISFContainer, submodule, Param
import binwalk

#https://github.com/ReFirmLabs/binwalk/blob/master/API.md
#https://github.com/ReFirmLabs/binwalk/wiki/Scripting-With-the-Python-API
@ISFContainer(version="1.0",
           author="Not_so_sm4rt_hom3 team")

class Extractor:
    in_params = {
        "FirmwareBINPath": Param("Path to memory dump (with firmware).", required=True),
        "FirmwareSavePath": Param("Path to save extracted firmware.", required=True, ),
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
    }

    firmware_path = ''
    firmware_bytes = b''

    debug = False

    def __init__(self, in_params):
        self.debug = in_params['Debug']

    @submodule(name="binwalkExtractor",
               description="Extract firmware with binwalk rules.",
               in_params={
                   "Extract": Param("Need to extract files",
                                    value_type=str,
                                    default_value=False,
                                    required=False)
               },
               out_params={"Files": Param("List of files with offset", value_type=list)})
    def binwalkExtractor(self, params):

        files = []

        for module in binwalk.scan(params['FirmwareBINPath'],
                                   signature=True,
                                   quiet=not params['Debug'],
                                   extract=params['Extract']):
            for result in module.results:
                files.append([result.offset, result.description])
        return {'Files': files}