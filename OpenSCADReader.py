# Copyright (c) 2016 Thomas Karl Pietrowski

# built-ins
import os
import platform

# Uranium
from UM.Logger import Logger # @UnresolvedImport
from UM.i18n import i18nCatalog # @UnresolvedImport

# CIU
from .CadIntegrationUtils.CommonCLIReader import CommonCLIReader # @UnresolvedImport

i18n_catalog = i18nCatalog("OpenSCADPlugin")

class OpenSCADReader(CommonCLIReader):
    def __init__(self):
        super().__init__("OpenSCAD")
        self._supported_extensions = [".scad".lower(),
                                      ]
        self.scanForAllPaths()

    def areReadersAvailable(self):
        return bool(self._readerForFileformat)

    def exportFileAs(self, options, quality_enum = None):
        Logger.log("d", "Exporting file: %s", options["tempFile"])
        
        # Use the appropriate command for the current OS
        if platform.system() == 'Darwin':
            cmd = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
        else:
            cmd = 'openscad'

        cmd = [cmd, '-o', options["tempFile"], options["foreignFile"]]
        self.executeCommand(cmd, cwd = os.path.split(options["foreignFile"])[0])
