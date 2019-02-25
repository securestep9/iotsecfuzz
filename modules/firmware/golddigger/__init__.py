from core.ISFFramework import ISFContainer, submodule, Param


@ISFContainer(version="1.0",
              author="Not_so_sm4rt_hom3 team")
class goldDigger:
    in_params = {
        "Debug": Param("Use verbose output", required=False, value_type=bool, default_value=False)
    }

    out_params = {
        "status": Param("Request status", value_type=int)
    }

    def __init__(self,params):
        self.debug = params['Debug']
