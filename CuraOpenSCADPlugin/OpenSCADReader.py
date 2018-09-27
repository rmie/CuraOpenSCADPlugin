# Copyright (c) 2016 Thomas Karl Pietrowski

# built-ins
import distutils.version.LooseVersion
import os
import platform

# Uranium
from UM.Logger import Logger # @UnresolvedImport
from UM.i18n import i18nCatalog # @UnresolvedImport

# Since 3.4: Register Mimetypes:
if distutils.version.LooseVersion("3.4") <= distutils.version.LooseVersion(Application.getInstance().getVersion()):
    from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType

# CIU
from .CadIntegrationUtils.CommonCLIReader import CommonCLIReader # @UnresolvedImport

i18n_catalog = i18nCatalog("OpenSCADPlugin")

class OpenSCADReader(CommonCLIReader):
    def __init__(self):
        super().__init__("OpenSCAD")

        if distutils.version.LooseVersion("3.4") <= distutils.version.LooseVersion(Application.getInstance().getVersion()):
            MimeTypeDatabase.addMimeType(MimeType(name = "application/x-extension-scad",
                                                  comment="OpenSCAD files",
                                                  suffixes=["scad"]
                                                  )
                                         )

        self._supported_extensions = [".scad".lower(),
                                      ]
        self.scanForAllPaths()

    def openForeignFile(self, options):
        options["fileFormats"].append("stl")

        return super().openForeignFile(options)

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
