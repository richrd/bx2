
import os
import sys
import imp
import logging
import traceback


class ModuleLoader:
    def __init__(self):
        self.module_path = ""
        self.logger = logging.getLogger("{}".format(__name__))

    def set_module_path(self, path):
        self.module_path = path

    def get_available_modules(self):
        contents = os.listdir(self.module_path)
        modules = []
        for name in contents:
            if name[0] in [".", "_"]:
                continue
            parts = name.split(".")
            if len(parts) < 2:
                continue
            # only use .py modules
            name = parts[0]
            ext = parts[-1]
            if ext == "py":
                modules.append(name)
        return modules

    def _import_module(self, name):
        path = os.path.join(self.module_path, name + ".py")
        try:
            module = imp.load_source(name, path)
            if "Module" not in dir(module):
                self.logger.error("Module '{}' didn't specify a class named 'Module'!".format(name))
                return False
            return module
        except Exception:
            # FIXME: use logging lib
            print("Failed loading:", name)
            print(traceback.format_exc())
            print(sys.exc_info()[0])
            return False

    def load_module(self, name):
        module = self._import_module(name)
        return module

if __name__ == "__main__":
    ml = ModuleLoader()
    ml.set_module_path("/home/wavi/Code/python/bx2/bx/modules")
    mods = ml.get_available_modules()
    print(mods)
    mod = ml.load_module("ping")
    print(mod)
