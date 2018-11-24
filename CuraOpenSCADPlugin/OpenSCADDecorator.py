from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.Application import Application
from UM.Logger import Logger
from cura.Settings.ExtruderManager import ExtruderManager
from collections import namedtuple

Index = namedtuple('Index', ['file_name', 'group', 'obj'])

class OpenSCADDecorator(SceneNodeDecorator):
    non_printing_mesh = ("infill_mesh", "cutting_mesh", "support_mesh", "anti_overhang_mesh")

    def __init__(self, file_name, obj):
        super(OpenSCADDecorator, self).__init__()
        self.file_name = file_name
        self.obj = obj

    def getOverwrites(self):
        node = self.getNode()

        settings = {}
        skip_extruder = False
        if node.hasDecoration('getStack'):
            stack = node.callDecoration('getStack')
            for key in stack.getContainer(0).getAllKeys():
                settings[key] = stack.getProperty(key, 'value')
                skip_extruder = skip_extruder or key in self.non_printing_mesh

        if not skip_extruder and node.hasDecoration('getActiveExtruder'):
            extruder_stack = node.callDecoration('getActiveExtruder')
            settings['extruder'] = extruder_stack

        return settings

    def items(self):
        node = self.getNode()
        topGroup = node
        while node:
            if node.hasDecoration('isGroup'):
                topGroup = node
            node = node.getParent()
        return {Index(self.file_name, topGroup, self.obj): self.getOverwrites()}

    def save(self):
        name = "" if self.obj.name == "" else " AS {0}".format(self.obj.name)
        file = "FILE " if self.obj.type == "stl" else ""
        out = "  {0}'{1}'{2}".format(file, self.obj.source, name)
        settings = []
        for k,v in self.getOverwrites().items():
            if isinstance(v, str):
                settings.append("    {0} = '{1}'".format(k,v))
            else:
                settings.append("    {0} = {1}".format(k, v))
        if len(settings) > 0:
            out += " SETTINGS\n"
            out += ',\n'.join(settings)
        return out

    def __deepcopy__(self, memo):
        return OpenSCADDecorator(self.file_name, self.obj)
