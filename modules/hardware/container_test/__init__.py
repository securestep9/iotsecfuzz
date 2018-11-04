from core.ISFFramework import ISFModule, Param


@ISFModule(name="container_test",
           version="1.0",
           description="Test some containers",
           author="Not_so_sm4rt_hom3 team")
class ExampleModule:
    in_params = {
        "TARGET": Param("The target path", required=True),
    }

    out_params = {
        "TEST": Param("Test out parameter")
    }

    def run(self, params):
        test_cont_class = self.get_container_class("firmware/test")
        test_container = test_cont_class({
            "TARGET": params["TARGET"],
            "VERBOSE": True
        })
        out1 = test_container.test_one({"T1": "kek"})
        out1.update(test_container.test_two({"T2": 10}))
        return out1
