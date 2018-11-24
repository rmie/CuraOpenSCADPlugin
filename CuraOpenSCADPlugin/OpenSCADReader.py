# Copyright (c) 2016 Thomas Karl Pietrowski

# built-ins
import os
import tempfile
import uuid
import platform

# Uranium
from UM.Application import Application  # @UnresolvedImport
from UM.Logger import Logger  # @UnresolvedImport
from UM.i18n import i18nCatalog  # @UnresolvedImport
from UM.Version import Version  # @UnresolvedImport
from UM.Mesh.MeshReader import MeshReader  # @UnresolvedImport
from UM.Scene.GroupDecorator import GroupDecorator  # @UnresolvedImport
from UM.Settings.SettingInstance import SettingInstance  # @UnresolvedImport

# Since 3.4: Register Mimetypes:
if Version("3.4") <= Version(Application.getInstance().getVersion()):
    from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType

from cura.Scene.BuildPlateDecorator import BuildPlateDecorator  # @UnresolvedImport
from cura.Scene.CuraSceneNode import CuraSceneNode  # @UnresolvedImport
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator  # @UnresolvedImport
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator  # @UnresolvedImport

# CIU
from .CadIntegrationUtils.CommonCLIReader import CommonCLIReader  # @UnresolvedImport

from .CommentParser import CommentParser
from .OpenSCADDecorator import OpenSCADDecorator

i18n_catalog = i18nCatalog("OpenSCADPlugin")


class OpenSCADReader(CommonCLIReader):
    def __init__(self):
        super().__init__("OpenSCAD")

        if Version("3.4") <= Version(Application.getInstance().getVersion()):
            MimeTypeDatabase.addMimeType(MimeType(name="application/x-extension-scad",
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

    def parseFileComments(self, file_name, receiv):
        with open(file_name, 'r') as inp:
            text = inp.read()
            blocks = text.split('/*cura-')
            # send everything before the first block, needed during write back
            receiv(None, blocks.pop(0))
            for block in blocks:
                [comment, post] = block.split('*/', 1)
                if comment.startswith('export'):
                    receiv(comment[6:], post)
                    # self.parts.append(parser.read(section[6:]))
                elif comment.startswith('profile'):
                    # TODO: how to deal with profile changes?
                    pass
                else:
                    # unknown section, send for write back
                    receiv(None, post)

        Logger.log("d", "parts: #{0} {1}".format(len(self.parts), self.parts))

    def nodePostProcessing(self, options, scene_nodes):
        self.renameNodes(options, scene_nodes)
        return scene_nodes


    def preRead(self, options):
        Logger.log("d", "preRead file: %s", options)

        parser = CommentParser(self)
        self.parts = []
        def _collector(comment, post):
            if comment:
                self.parts.append(parser.read(comment))
        self.parseFileComments(options, _collector)

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

    def importParts(self, options):
        Logger.log("d", "importParts: {0}".format(options))
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
                        node.addDecorator(OpenSCADDecorator(file_name, mesh))
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
            result = self.importParts(options)

        # Unlock if needed
        if not self._parallel_execution_allowed:
            self.conversion_lock.release()

        return result

    def exportFileAs(self, options, quality_enum=None):
        Logger.log("d", "Exporting file: %s", options["tempFile"])

        # Use the appropriate command for the current OS
        if platform.system() == 'Darwin':
            cmd = '/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD'
        else:
            cmd = 'openscad'

        cmd = [cmd, '-o', options["tempFile"], options["foreignFile"]]
        self.executeCommand(cmd, cwd=os.path.split(options["foreignFile"])[0])

    def _get_scene_items(self, node):
        items = node.callDecoration("items") if node.hasDecoration("getOverwrites") else {}
        for child in node.getChildren():
            items.update(self._get_scene_items(child))
        return items


    def write(self, output_device):
        # hook into write, to save changes back to the OpenSCAD files
        root = Application.getInstance().getController().getScene().getRoot()
        items = self._get_scene_items(root);
        Logger.log("d", "items:{0}".format(items))

        groups = set((key.group for key in items.keys()))
        # ensure that every group of parts is made from parts from the same file
        # collect file_name for each part in a every group use set() to remove duplicates
        unique =  {outer:set([inner.file_name for inner in items if inner.group == outer]) for outer in groups}
        for node, files in unique.items():
            if len(files) > 1:
                #TODO: warning
                return

        parser = CommentParser(self)
        files = set([k.file_name for k in items.keys()])
        for file in files:
            # filter all items form this file
            self.parts = [item.obj for item in items if item.file_name == file]

            tmp = os.path.join(os.path.dirname(file), '.' + os.path.basename(file))
            with open(tmp, 'w') as out:
                def _writer(comment, post):
                    if comment:
                        part = parser.read(comment)
                        if set(part.keys()).issubset(self.parts):
                            Logger.log("d", "found:{0}".format(part.keys()))
                            # this might return multiple groups (after ungrouping)
                            groups = set((key.group for key in items.keys() if key.obj in set(part.keys())))
                            Logger.log("d", "groups:{0}".format(groups))

                            for node in groups:
                                if node.hasDecoration('isGroup'):
                                    out.write("/*cura-export\n")
                                    for child in node.getChildren():
                                        if child.hasDecoration("save"):
                                            out.write("{0}\n".format(child.callDecoration("save")))
                                            for e in child.callDecoration("items"): self.parts.remove(e.obj)
                                    out.write("*/")
                                else:
                                    out.write("/*cura-export\n{0}\n*/".format(node.callDecoration("save")))
                                    for e in node.callDecoration("items"):
                                        Logger.log("d", "remove:{0}".format(e.obj))
                                        self.parts.remove(e.obj)
                        else:
                            # no longer on the build plate, or part of a group,
                            # remove for the future by adding a space in the comment
                            out.write("/* cura-export{0}*/".format(comment))
                    out.write(post)

                self.parseFileComments(file, _writer)
                #TODO: keep project settings?

            os.rename(file, file + '.old')
            os.rename(tmp, file)
            # only parts that have been removed from the file in between, log them for debug
            for part in self.parts: Logger.log("d", "leftover:{0}".format(part))
