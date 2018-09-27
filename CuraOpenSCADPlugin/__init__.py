# Copyright (c) 2016 Thomas Karl Pietrowski

# Uranium
from UM.Platform import Platform # @UnresolvedImport
from UM.Logger import Logger # @UnresolvedImport
from UM.i18n import i18nCatalog # @UnresolvedImport
i18n_catalog = i18nCatalog("OpenSCADPlugin")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "OpenSCADPlugin"),
            "author": "Thomas Karl Pietrowski",
            "version": "0.1.0",
            "description": i18n_catalog.i18nc("@info:whatsthis", "Gives you the possibility to open *.SCAD files."),
            "api": 3
        },
        "mesh_reader": [
            {
                "extension": "SCAD",
                "description": i18n_catalog.i18nc("@item:inlistbox", "SCAD file")
            },
        ]
    }

def register(app):
    if Platform.isWindows() or Platform.isLinux() or Platform.isOSX(): 
        from . import OpenSCADReader # @UnresolvedImport
        return {"mesh_reader": OpenSCADReader.OpenSCADReader()}
    else:
        Logger.logException("i", "Unsupported OS!")
        return {}
