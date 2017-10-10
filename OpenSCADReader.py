# Copyright (c) 2016 Thomas Karl Pietrowski

import os
import platform
import subprocess

from UM.PluginRegistry import PluginRegistry # @UnresolvedImport
from UM.Logger import Logger # @UnresolvedImport

from UM.i18n import i18nCatalog # @UnresolvedImport
i18n_catalog = i18nCatalog("CuraOpenSCADIntegrationPlugin")

from .dotscad import OpenSCAD as SCAD_handler # @UnresolvedImport

from .CadIntegrationUtils.CommonComReader import CommonCLIReader # @UnresolvedImport

class OpenSCADReader(CommonCLIReader):
    def __init__(self):
        super().__init__("OpenSCAD")
        self._supported_extensions = [".SCAD".lower(),
                                      ]

    def areReadersAvailable(self):
        return bool(self._readerForFileformat)


    def openForeignFile(self, options):
        # We open the file, while converting.. No actual opening of the file needed..
        #Logger.log("d", "Opening file: %s", options["foreignFile"])
        #options["scad_file"] = SCAD_handler(options["foreignFile"], debug=False)
        return options
    
    def exportFileAs(self, options):
        #Logger.log("d", "Exporting file: %s", options["tempFile"])
        #options["scad_file"].render_stl(dest=options["tempFile"], overwrite=False)
        
        # Use the appropriate command for the current OS
        if platform.system() == 'Darwin':
            cmd = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
        elif platform.system() == 'Windows':
            cmd = 'openscad.exe'
        else:
            cmd = 'openscad'

        cmd = [cmd, '-o', options["tempFile"], options["foreignFile"]]
        subprocess.call(cmd, cwd=os.path.split(options["foreignFile"])[0])
