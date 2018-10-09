from core.ISFFramework import ISFModule, Param


@ISFModule(name="golddigger",
           version="1.0",
           description="Finds passwords, configs & logs in the unpacked files",
           author="Not_so_sm4rt_hom3 team")
class ExampleModule:
    in_params = {
        "TARGET": Param("The target path", required=True),
        "DEPTH": Param("Nested folder lookup level", value_type=int,
                       required=True, default_value=3),
        "VERBOSE": Param("Use verbose output", required=False)
    }

    out_params = {
        "TEST": Param("Test out parameter")
    }

    def run(self, params):
        print(params["TARGET"])
        return {"TEST": "yay"}
