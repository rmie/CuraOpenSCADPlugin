# Copyright (c) 2016 Thomas Karl Pietrowski

from UM.Platform import Platform

from UM.Logger import Logger

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("CuraCatiaIntegrationPlugin")

def getMetaData():
    return {
        "plugin": {
            "name": i18n_catalog.i18nc("@label", "OpenSCADIntegrationPlugin"),
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
    try:
        from . import OpenSCADReader
        return {"mesh_reader": OpenSCADReader.OpenSCADReader()}
    except:
        Logger.logException("e", "An error occured, when trying to import OpenSCADReader!")
        return {}
