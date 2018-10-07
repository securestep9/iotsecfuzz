from core.ISFFramework import ISFModule, Param


@ISFModule(name="golddigger",
           version="1.0",
           description="Finds passwords, configs & logs in the unpacked files",
           author="Not_so_sm4rt_hom3 team")
class ExampleModule:

    in_params = {
        "TARGET": Param("The target path", value_type=str, required=True)
    }

    out_params = {
        "TEST": Param("Just a test parameter")
    }

    def run(self, params):
        print("kek")
        return {"TEST": "yay"}
