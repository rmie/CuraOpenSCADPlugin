from .lex import lex
from .yacc import yacc

from collections import namedtuple


# CommentParser BNF
#
# objectlist : object | object objectlist
# object : meshspec | meshspec SETTINGS keyvaluelist
# meshspec : string | string AS NAME | FILE string | FILE string AS NAME
# keyvaluelist : keyvalue | keyvalue COMMA keyvaluelist
# keyvalue : NAME EQUAL value
# value : string | integer | float | boolean | list
# string : SSTRING | DSTRING

class ObjectID(namedtuple('ObjectID', ['type', 'source', 'name'])):
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.name != '' and self.name == other.name or \
               self.name == '' and other.name == '' and self.type == other.type and self.source == other.source
    def __hash__(self):
        if self.name != '':
            return hash(self.name)
        return hash(self.type + self.source)
    def __str__(self):
        return self.name if self.name != '' else "{0}:'{1}'".format(self.type, self.source)


class ObjectDict(dict):

    def __init__(self, kv=None):
        super(ObjectDict, self).__init__
        if kv:
            key, value = kv
            self[key] = value

    def update(self, d):
        for k, v in d.items():
            if k not in self:
                self[k] = v
            else:
                raise KeyError('Duplicate key {0}'.format(k))


class CommentParser(object):
    # reserved words that are NAMEs, too
    reserved = ('SETTINGS', 'FILE', 'AS', 'True', 'False')
    tokens = ('SSTRING', 'DSTRING', 'INTEGER', 'FLOAT', 'NAME', 'LIST', 'EQUAL', 'COMMA') + reserved

    t_SETTINGS = r'SETTINGS'
    t_FILE = r'FILE'
    t_AS = r'AS'
    t_SSTRING = r"\'[^\']*\'"
    t_DSTRING = r'\"[^\"]*\"'
    t_True = r'True'
    t_False = r'False'
    t_EQUAL = r'='
    t_COMMA = r','
    t_FLOAT = r'[+-]?[0-9]*\.[0-9]+'
    t_INTEGER = r'[+-]?[0-9]+'
    t_LIST = r'\[[^\]]*\]'
    t_ignore = " \n\t\r\v\f"

    def __init__(self, reader):
        self.reader = reader

        self.lexer = lex(module=self)

        modname = "parser" + "_" + self.__class__.__name__
        tabmodule = modname + "_" + "parsetab"
        self.parser = yacc(module=self, tabmodule=tabmodule, debug=False)

    def read(self, text):
        self.parse_write = False
        return self.parser.parse(text, lexer=self.lexer)

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        if t.value in self.reserved:
            t.type = t.value
        return t

    def t_error(self, t):
        self.reader.log('e', 'Illegal character "{0}"'.format(t.value[0]))
        t.lexer.skip(1)

    def p_objectlist(self, p):
        '''objectlist : object
                      | object objectlist'''
        p[0] = ObjectDict(p[1])
        if len(p) == 3:
            p[0].update(p[2])

    def p_object(self, p):
        '''object : meshspec
                  | meshspec SETTINGS keyvaluelist'''
        kvl = {}
        if len(p) == 4:
            kvl = p[3]
        p[0] = (p[1], kvl)

    #  def p_meshspeclist(self, p):
    #    '''meshspeclist : meshspec
    #                    | meshspec TIMES NUMBER
    #                    | meshspec COMMA meshspeclist'''
    #    p[0] = [p[1]]
    #    if len(p) == 4:
    #      p[0] += p[3]

    def p_meshspec(self, p):
        '''meshspec : string
                    | string AS NAME
                    | FILE string
                    | FILE string AS NAME'''
        name = '' if len(p) < 4 else p[len(p) - 1]
        p[0] = ObjectID('stl', p[2], name) if p[1] == 'FILE' else ObjectID('scad', p[1], name)

    def p_keyvaluelist(self, p):
        '''keyvaluelist : keyvalue
                        | keyvalue COMMA keyvaluelist'''
        p[0] = p[1]
        if len(p) == 4:
            p[0].update(p[3])

    def p_keyvalue(self, p):
        '''keyvalue : NAME EQUAL value'''
        p[0] = {p[1]: p[3]}

    def p_value(self, p):
        '''value : string
                 | integer
                 | float
                 | boolean
                 | list'''
        p[0] = p[1]

    def p_string(self, p):
        '''string : SSTRING
                  | DSTRING'''
        p[0] = p[1][1:-1]

    def p_list(self, p):
        'list : LIST'
        p[0] = p[1]

    def p_integer(self, p):
        'integer : INTEGER'
        p[0] = int(p[1])

    def p_float(self, p):
        'float : FLOAT'
        p[0] = float(p[1])

    def p_boolean(self, p):
        '''boolean : True
                   | False'''
        p[0] = bool(p[1])

    def p_error(self, p):
        if p:
            self.reader.log('e', "Syntax error at '%s'" % p.value)
        else:
            self.reader.log('e', "Syntax error at EOF")
