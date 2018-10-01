# Copyright (c) 2016 Thomas Karl Pietrowski

# built-ins
import os
import tempfile
import uuid
import platform

# Uranium
from UM.Application import Application # @UnresolvedImport
from UM.Logger import Logger # @UnresolvedImport
from UM.i18n import i18nCatalog # @UnresolvedImport
from UM.Version import Version # @UnresolvedImport
from UM.Mesh.MeshReader import MeshReader # @UnresolvedImport
from UM.Scene.GroupDecorator import GroupDecorator # @UnresolvedImport
from UM.Settings.SettingInstance import SettingInstance # @UnresolvedImport

# Since 3.4: Register Mimetypes:
if Version("3.4") <= Version(Application.getInstance().getVersion()):
    from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType

from cura.Scene.BuildPlateDecorator import BuildPlateDecorator # @UnresolvedImport
from cura.Scene.CuraSceneNode import CuraSceneNode # @UnresolvedImport
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator # @UnresolvedImport
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator # @UnresolvedImport

# CIU
from .CadIntegrationUtils.CommonCLIReader import CommonCLIReader # @UnresolvedImport

from .CommentParser import CommentParser

import pdb

i18n_catalog = i18nCatalog("OpenSCADPlugin")

class OpenSCADReader(CommonCLIReader):
    def __init__(self):
        super().__init__("OpenSCAD")

        if Version("3.4") <= Version(Application.getInstance().getVersion()):
            MimeTypeDatabase.addMimeType(MimeType(name = "application/x-extension-scad",
                                                  comment="OpenSCAD files",
                                                  suffixes=["scad"]
                                                  )
                                         )

        self._supported_extensions = [".scad".lower(),
                                      ]
        self.scanForAllPaths()
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.write)

    def openForeignFile(self, options):
        options["fileFormats"].append("stl")

        return super().openForeignFile(options)

    def areReadersAvailable(self):
        return bool(self._readerForFileformat)

    def parseFileComments(self, file_name):
        self.parts = []
        with open(file_name, 'r') as inp:
            parser = CommentParser(self)
            text = inp.read()
            blocks = text.split('/*cura-')
            blocks.pop(0)
            for block in blocks:
                section = block.split('*/')[0]
                if section.startswith('export'):
                    self.parts.append(parser.read(section[6:]))
                elif section.startswith('profile'):
                    # TODO: how to deal with profile changes?
                    pass

        Logger.log("d", "parts: #{0} {1}".format(len(self.parts), self.parts))

    def nodePostProcessing(self, options, scene_nodes):
        self.renameNodes(options, scene_nodes)
        return scene_nodes

    def preRead(self, options):
        Logger.log("d", "preRead file: %s", options)
        self.parseFileComments(options)
        return MeshReader.PreReadResult.accepted

    def _node(self, mesh, settings):
        node = CuraSceneNode()
        node.setMeshData(mesh)
        node.setSelectable(True)
        node.addDecorator(SliceableObjectDecorator())

        if len(settings) > 0:
            node.addDecorator(SettingOverrideDecorator())
            stack = node.callDecoration('getStack')
            top = stack.getTop()

            for k, v in settings.items():
                if k == 'extruder':
                    node.callDecoration('setActiveExtruder', v)
                else:
                    definition = stack.getSettingDefinition(k)
                    instance = SettingInstance(definition, top)
                    instance.setProperty("value", v)
                    instance.resetState()
                    top.addInstance(instance)

        Logger.log('d', 'node: {0}'.format(node))
        return node

    def readOnMultipleAppLayer(self, options):
        Logger.log("d", "readOnMultipleAppLayer: {0}".format(options))
        options["tempFileKeep"] = True
        file_name = options["foreignFile"];
        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        nodes = []

        for part in self.parts:
            if len(part) > 1:
                group = CuraSceneNode()
                group.setSelectable(True)
                group.addDecorator(GroupDecorator())
                group.addDecorator(BuildPlateDecorator(active_build_plate))
                nodes.append(group)

            for mesh, settings in part.items():
                Logger.log("d", "import mesh: {0}".format(mesh))
                if mesh.type == "scad":
                    tempdir = tempfile.gettempdir()
                    options["foreignFile"] = os.path.join(tempdir, "{}.{}".format(uuid.uuid4(), "scad"))
                    try:
                        with open(options["foreignFile"], 'w') as f:
                            f.write('!{0};\ninclude <{1}>;\n'.format(mesh.source, file_name))
                            f.close()
                        node = self._node(self.readOnSingleAppLayer(options).getMeshData(), settings)
                        node.addDecorator(BuildPlateDecorator(active_build_plate))
                        if len(part) > 1:
                            group.addChild(node)
                        else:
                            nodes.append(node)
                    finally:
                        if not options["tempFileKeep"]:
                            os.remove(options["foreignFile"])
                else:
                    options["foreignFile"] = os.path.join(os.path.split(file_name)[0], mesh.source)

        return self.nodePostProcessing(options, nodes)

    def read(self, file_path):
        options = self.readCommon(file_path)
        if self.parts == []:
            result = self.readOnSingleAppLayer(options)
        else:
            result = self.readOnMultipleAppLayer(options)

        # Unlock if needed
        if not self._parallel_execution_allowed:
            self.conversion_lock.release()

        return result

    def exportFileAs(self, options, quality_enum = None):
        Logger.log("d", "Exporting file: %s", options["tempFile"])

        # Use the appropriate command for the current OS
        if platform.system() == 'Darwin':
            cmd = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
        else:
            cmd = 'openscad'

        cmd = [cmd, '-o', options["tempFile"], options["foreignFile"]]
        self.executeCommand(cmd, cwd = os.path.split(options["foreignFile"])[0])

    def _getSettings(self, node):
        # example code to test how to get all relevant settings
        for child in node.getChildren():
            self._getSettings(child)

        non_printing_mesh = ("infill_mesh", "cutting_mesh", "support_mesh", "anti_overhang_mesh")
        if node.hasDecoration("isSliceable") and node.hasDecoration("getStack"):
            skip_extruder = False
            stack = node.callDecoration('getStack')
            for key in stack.getContainer(0).getAllKeys():
                skip_extruder = skip_extruder or key in non_printing_mesh
                Logger.log("d", "{0}={1} ({2})".format(key, stack.getProperty(key, 'value'), skip_extruder))
            if not skip_extruder:
                Logger.log("d", "Extruder: {0}".format(node.callDecoration('getActiveExtruder')))

    def write(self, output_device):
        # hook into write, to save changes back to the OpenSCAD files
        root = Application.getInstance().getController().getScene().getRoot()
        self._getSettings(root)
