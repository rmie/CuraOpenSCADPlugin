# Copyright (c) 2016 Thomas Karl Pietrowski

import os
import tempfile

from UM.Mesh.MeshReader import MeshReader # @UnresolvedImport
from UM.PluginRegistry import PluginRegistry # @UnresolvedImport
from UM.Logger import Logger # @UnresolvedImport
from UM.Message import Message # @UnresolvedImport

from UM.i18n import i18nCatalog # @UnresolvedImport
i18n_catalog = i18nCatalog("CuraOpenSCADIntegrationPlugin")

from .dotscad import Customizer # @UnresolvedImport

class OpenSCADReader(MeshReader):
    def __init__(self):
        super(OpenSCADReader, self).__init__()
        self._supported_extensions = [".SCAD".lower(),
                                      ]
        self._readerForFileformat = {}

        # Trying 3MF first because it describes the model much better..
        # However, this is untested since this plugin was only tested with STL support
        if PluginRegistry.getInstance().isActivePlugin("STLReader"):
            self._readerForFileformat["stl"] = PluginRegistry.getInstance().getPluginObject("STLReader")

        if not len(self._readerForFileformat):
            Logger.log("d", "Could not find any reader for (probably) supported file formats!")


    def areReadersAvailable(self):
        return bool(self._readerForFileformat)

    ## Decide if we need to use ascii or binary in order to read file
    def read(self, file_name):
        Logger.log("i", "Trying to convert into: %s" %(self._readerForFileformat.keys()))
        for fileFormat in self._readerForFileformat.keys():
            Logger.log("d", "Trying to convert <%s> into  '%s'" %(file_name, fileFormat))

            # Only get a save name for a temp_file here...
            temp_stl_file = tempfile.NamedTemporaryFile()
            temp_stl_file_name = "%s.%s" %(temp_stl_file.name, fileFormat)
            temp_stl_file.close()

            # In case there is already a file with this name (very unlikely...)
            if os.path.isfile(temp_stl_file_name):
                Logger.log("w", "Removing already avilable file, called: %s" %(temp_stl_file_name))
                os.remove(temp_stl_file_names)

            Logger.log("d", "Using temporary file <%s>" %(temp_stl_file_name))
            try:
                Logger.log("d", "Opening file with OpenSCAD...")
                customizableScadFile = Customizer(file_name, debug=False)
            except Exception:
                Logger.logException("e", "Failed to convert via OpenSCAD...")
                error_message = Message(i18n_catalog.i18nc("@info:status", "Error while starting OpenSCAD!"))
                error_message.show()
                return None

            try:
                Logger.log("d", "Rendering and saving as: <%s>" %(temp_stl_file_name))
                customizableScadFile.render_stl(dest=temp_stl_file_name, overwrite=False)
            except:
                Logger.log("e", "Could not render or convert <%s> into '%s'." %(file_name, fileFormat))
                continue

            Logger.log("d", "Saved as: <%s>" %(temp_stl_file_name))

            # Opening file in Cura
            try:
                reader = self._readerForFileformat[fileFormat]
                scene_node = reader.read(os.path.normpath(temp_stl_file_name))
            except:
                Logger.log("e", "Failed to open exported <%s> file in Cura!" %(fileFormat))
                continue

            # Remove the temp_file again
            Logger.log("d", "Removing temporary STL file, called <%s>", temp_stl_file_name)
            os.remove(temp_stl_file_name)

        return scene_node
