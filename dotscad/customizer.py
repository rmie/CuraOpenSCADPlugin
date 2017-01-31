
import re

from .openscad import OpenSCAD
from collections import OrderedDict

class Customizer(OpenSCAD):

    __slots__ = (
        'vars',
        'tabs',
        '_customizer_source',
    )

    def __init__(self, path, debug=False):
        self.vars = OrderedDict()
        self.tabs = OrderedDict()
        self._customizer_source = ''
        super(Customizer, self).__init__(path, debug)

    def render(self):
        rendered = self._customizer_source
        for name, var in self.vars.items():
            self.debug("Render {0} = {1}".format(name, encode_value(var.value)))
            rendered = re.sub('~~{0}~~'.format(name), encode_value(var.value), rendered)
        return rendered + self._source

    def _load(self):
        """
        http://customizer.makerbot.com/docs
        """
        super(Customizer, self)._load()

        # Split the customizer source block out from the rest
        parts = re.split(re.compile(r'(\n\s*module\s.+)$', re.DOTALL | re.IGNORECASE), self._source, 2)
        self._source = parts[1] if len(parts) > 1 else ''
        customizer_src = parts[0]

        # tokenize the customizer code
        chunks = re.split(r'^(\s*/\*\s*\[\s*(.+?)\s*\]\s*\*/\s*)$', customizer_src, flags=re.MULTILINE)
        if len(chunks) == 1:
            self._customizer_source = self._tokenize_tab_vars('Global', chunks.pop(0))
        else:
            tokenized = chunks.pop(0) # Everything up to the first match
            for i in xrange(0, len(chunks), 3):
                (tab_chunk, tab_name, tab_source) = chunks[i:i+3]
                tokenized += tab_chunk
                # Ignore the "Hidden" tab
                if tab_name.lower() == 'hidden':
                    tokenized += tab_source
                else:
                    # Normalize "Global"
                    if (tab_name.lower() == 'global'):
                        tab_name = 'Global'
                    tokenized += self._tokenize_tab_vars(tab_name, tab_source)
            self._customizer_source = tokenized


    def _tokenize_tab_vars(self, tab_name, source):
        self.debug("Loading tab: {0}".format(tab_name))
        if tab_name in self.tabs:
            raise ValueError("Multiple '{0}' tabs found".format(tab_name))
        self.tabs[tab_name] = []

        chunks = re.split(r'(?:^|(?<=\n))(?:[\ \t]*?//\s*(.*?))?\n\s*(\w+)\s*=\s*(.+?)\s*;[\ \t]*(?://\s*\[(.+?)\])?[\ \t]*', source, flags=re.MULTILINE)
        # No variables, just return
        if len(chunks) == 1:
            return chunks[0]
        tokenized = chunks.pop(0) # Everything up to the first match
        for i in xrange(0, len(chunks), 5):
            (desc, var_name, val, possible, extra_scad) = chunks[i:i+5]
            # Add to our local caches of the customizer info
            self.debug("  Loading var: {0} = {1} : {2}".format(var_name, val,possible))
            self.vars[var_name] = CustomizerVar(var_name, decode_value(val), possible, desc)
            self.tabs[tab_name].append(self.vars[var_name])
            # Build the tokenized data
            tokenized += "// {0}\n{1} = ~~{1}~~; // [{2}]{3}".format(desc, var_name, possible, extra_scad)
        return tokenized


class CustomizerVar(object):

    __slots__ = (
        'name', 'value', 'possible', 'description',
    )

    def __init__(self, name, value, possible=None, description=None):
        self.name = name
        self.value = value
        self.possible = CustomizerPossible(possible)
        self.description = description if description else ''

    def set(self, value):
        if isinstance(value, (bool, basestring, str, int, long, float, complex)):
            self.value = value
        else:
            raise ValueError("Unsupported value type")

class CustomizerPossible(object):

    __slots__ = (
        '_raw', 'parameters',
    )

    def __init__(self, raw=None):
        self._raw = raw
        self.parameters = OrderedDict()
        if self._raw is None:
            pass
        elif self._raw.lower().startswith('image_surface:'):
            pass
        elif self._raw.lower().startswith('image_array:'):
            pass
        elif self._raw.lower().startswith('draw_polygon:'):
            pass
        elif re.match(r'^\d+:\d+$', self._raw):
            # see __getitem__()
            pass
        else:
            for param in re.split(r'\s*,\s*', self._raw):
                pair = param.split(':', 2)
                # Detect numeric values
                value = pair[0]
                if value.isdigit():
                    value = int(value)
                elif re.match(r'^\d+\.\d+$', value):
                    value = float(value)
                # Assign the parameter
                if len(pair) == 1:
                    self.parameters[value] = value
                else:
                    self.parameters[pair[1]] = value


    def __str__(self):
        return self._raw

    def __getitem__(self, item):
        if item in self.parameters:
            return self.parameters[item]
        # @todo make smarter for range values
        return item


def decode_value(val):
    """
    Return the pythonic value for a value scraped from a scad file (e.g. true, or "thing" including the quotes).
    """
    if val.lower() == 'true':
        return True
    if val.lower() == 'false':
        return False
    if val.startswith('"'):
        return val[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if '.' in val:
        return float(val)
    return int(val)

def encode_value(val):
    """
    Convert a python value to something that can be injected into scad source
    """
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, (basestring, str, unicode)):
        return '"{0}"'.format(str(val).replace('"', '\\"').replace('\\', '\\\\'))
    return str(val)
