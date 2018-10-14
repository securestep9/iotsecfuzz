from core.ISFFramework import ISFContainer, submodule, Param


@ISFContainer(version="1.0",
              author="Not_so_sm4rt_hom3 team")
class TestContainer:

    def __init__(self, in_params):
        # do some general stuff
        self.connected = True
        print("Connected to target %s" % in_params["TARGET"])

    in_params = {
        "TARGET": Param("The target path", required=True),
        "VERBOSE": Param("Use verbose output", default_value=False,
                         required=False)
    }

    @submodule(name="test1",
               description="Wow such test",
               in_params={
                   "T1": Param("A test param", value_type=int, required=True)
               },
               out_params={"kek": Param("So kek")})
    def test_one(self, in_params):
        print("Here are my in params: ")
        print(in_params)
        print(self.connected)
        return {"kek": in_params["T1"] + 1}

    @submodule(name="test2",
               description="Sweet another test",
               in_params={
                   "T2": Param("A test param v2", value_type=int, required=True)
               },
               out_params={"ohgodwhat": Param("No idea")})
    def test_one(self, in_params):
        print("Psss, these are my in parameters: ")
        print(in_params)
        print(self.connected)
        return {"ohgodwhat": in_params["T2"] * 4}
