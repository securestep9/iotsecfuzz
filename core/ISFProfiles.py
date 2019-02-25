import json
from os import listdir
from os.path import isfile, join
import core.ISFFramework as ISFFramework

from util.exceptions import ProfileNotFoundException, \
    PresetsAlreadyPresentException, InitializationException

loaded_profiles = dict()


class Profile:

    def __init__(self, loaded_from, name, description, presets_packs):
        self.location = loaded_from
        self.name = name
        self.description = description
        self.presets = dict()
        self.presets_packs = presets_packs
        self.build_presets()

    def build_presets(self):
        self.presets = dict()
        for name, pack in self.presets_packs.items():
            for key, preset in pack["presets"].items():
                self.presets[key] = preset

    def save(self):
        with open(self.location, "wt") as out_file:
            json.dump(self.to_dict(), out_file)

    def to_dict(self):
        result = {
            "name": self.name,
            "description": self.description,
            "presets_packs": self.presets_packs
        }
        return result

    def get_preset(self, key):
        return self.presets[key] if key in self.presets else None


def import_preset_pack(file_name):
    with open(file_name, "rt") as file:
        data = json.load(file)
        pack_name = data["name"]
        for name in data["profiles"]:
            if name not in loaded_profiles:
                raise ProfileNotFoundException("No profile named '%s'" % name)
            if pack_name in loaded_profiles[name].presets_packs:
                raise PresetsAlreadyPresentException(
                    "Pack '%s' is already loaded" % pack_name)
            pack = dict()
            pack["description"] = data["description"]
            pack["origin"] = file_name
            pack["presets"] = data["profiles"][name]
            loaded_profiles[name].presets_packs[pack_name] = pack
            loaded_profiles[name].build_presets()
            loaded_profiles[name].save()
            if ISFFramework.curr_profile \
                    and ISFFramework.curr_profile.name == name:
                ISFFramework.use_profile(name)


def import_profile(file_name):
    with open(file_name, "rt") as file:
        data = json.load(file)
        profile = Profile(file_name, data["name"], data["description"],
                          data["presets_packs"])
        if profile.name in loaded_profiles:
            raise InitializationException(
                "Profile '%s' already loaded" % profile.name)
        loaded_profiles[profile.name] = profile


def load_profiles():
    path = "profiles"
    files = [f for f in listdir(path) if isfile(join(path, f))]
    for file_name in files:
        import_profile(path + "/" + file_name)
