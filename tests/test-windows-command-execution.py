import os
import sys
import subprocess
import winreg

class Core():
    def __init__(self):
        self._supported_extensions = [".scad".lower(),
                                      ]
    
    def executeCommand(self, command, cwd = os.path.curdir):
        environment_with_additional_path = os.environ.copy()
        if self._additional_paths:
            environment_with_additional_path["PATH"] = os.pathsep.join(self._additional_paths) + os.pathsep + environment_with_additional_path["PATH"]
        print("d", "PATH: {}".format(environment_with_additional_path["PATH"]))
        p = subprocess.Popen(command,
                             cwd = cwd,
                             env = environment_with_additional_path,
                             shell=True
                             )
        p.wait()
        
    def scanForAllPaths(self):
        self._additional_paths = []
        if sys.platform == "win32":
            for file_extension in self._supported_extensions:
                path = self._findPathFromExtension(file_extension)
                print("d", "Found path for {}: {}".format(file_extension, path))
                if path:
                    path = path.replace("\\", "/")
                    self._additional_paths.append(path)
    
    def _findPathFromExtension(self, extension):
        file_class = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, extension)
        file_class = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, os.path.join(file_class,
                                                                              "shell",
                                                                              "open",
                                                                              "command",
                                                                              )
                                       )
        file_class = file_class.split("\"")
        while "" in file_class:
            file_class.remove("")
        file_class = file_class[0]
        path = os.path.split(file_class)[0]
        if os.path.isdir(path):
            return path
        return

c = Core()
c.scanForAllPaths()
cmd = 'openscad'
cmd = [cmd, '-o', "./test.stl", "./test.scad"]
c.executeCommand(cmd)