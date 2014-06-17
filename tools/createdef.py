# Copyright (c) Mathias Kaerlev 2013-2014.
#
# This file is part of cuwo.
#
# cuwo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cuwo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cuwo.  If not, see <http://www.gnu.org/licenses/>.

import sys
sys.path.append('..')
import re
import collections
from cuwo import tgen


def comment_remover(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return ""
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)


class FormattedOutput(object):
    def __init__(self, description):
        self.data = ''
        self.indentation = 0
        self.putln(license_header % description)

    def putln(self, value=''):
        if not value.strip():
            self.data += '\n'
            return
        self.data += ' ' * (4 * self.indentation) + value + '\n'

    def get(self):
        return self.data.encode('utf-8')

    def indent(self):
        self.indentation += 1

    def dedent(self):
        self.indentation -= 1
        if self.indentation < 0:
            raise TypeError('invalid indentation')

    def write_dict(self, name, value):
        self.putln('%s = {' % name)
        self.indent()

        def sort_func(key):
            if isinstance(key, tuple):
                return key[0] * 500000 + key[1]
            return key

        for index, key in enumerate(sorted(value, key=sort_func)):
            v = '%s: %r' % (key, value[key])
            if index < len(value) - 1:
                v += ','
            self.putln(v)

        self.dedent()
        self.putln('}')
        self.putln()

TYPE_DEF = {
    '__int64': 'int64',
    'uint64_t': 'uint64',
    '_DWORD': 'uint32',
    'int': 'int32',
    'signed int': 'int32',
    'signed short': 'int16',
    '_BYTE': 'uint8',
    '_WORD': 'uint16',
    'char': 'int8',
    'float': 'float',
    'vec3': 'vec3',
    'qvec3': 'qvec3'
}

TYPE_SIZE = {
    'uint8': 1,
    'int8': 1,
    'uint16': 2,
    'in16': 2,
    'int64': 8,
    'uint64': 8,
    'uint32': 4,
    'int32': 4,
    'vec3': 4 * 3,
    'qvec3': 8 * 3,
    'float': 4
}

DEFAULTS = {
    'uint8': 0,
    'int8': 0,
    'uint16': 0,
    'int16': 0,
    'int64': 0,
    'uint64': 0,
    'uint32': 0,
    'int32': 0,
    'vec3': 'Vector3(0, 0, 0)',
    'qvec3': 'Vector3(0, 0, 0)',
    'float': 0.0
}

CYTHON_TYPES = {
    'int8': 'char',
    'uint8': 'unsigned char',
    'int16': 'short',
    'uint16': 'unsigned short',
    'int32': 'int',
    'uint32': 'unsigned int',
    'int64': 'int64_t',
    'uint64': 'uint64_t',
    'vec3': 'object',
    'qvec3': 'object',
    'float': 'double',
    'double': 'double'
}

struct_dict = collections.OrderedDict()


class Struct(object):
    def __init__(self, name):
        self.name = name
        self.attrs = []
        self.defs = []

    def get_size(self):
        size = 0
        for attr in self.attrs:
            size += attr.get_size()
        return size


class Attribute(object):
    def __init__(self, name, typ, dim=None, default=None):
        self.name = name
        self.typ = typ
        self.dim = dim
        self.default = default

    def get(self):
        return (self.name, self.typ, self.dim, self.is_local())

    def get_size(self):
        if self.is_local():
            size = struct_dict[self.typ].get_size()
        else:
            size = TYPE_SIZE[self.typ]
        return size * (self.dim or 1)

    def is_local(self):
        return self.typ not in TYPE_DEF.values()


def parse_header(data):
    defs = []
    lines = data.splitlines()
    struct = None
    for line in lines:
        line = line.strip()
        if not line or line == '{':
            continue
        if line.startswith('struct '):
            name = line.split(' ')[-1]
            struct = Struct(name)
            struct_dict[name] = struct
            continue
        if line.startswith('#define'):
            name, val = line[7:].strip().split()
            defs.append((name, val))
        if line == '};':
            struct.defs = defs
            defs = []
            struct = None
            continue
        if struct is not None:
            if not line.endswith(';'):
                raise NotImplementedError()
            line = line[:-1]
            if '=' in line:
                line, default = line.split('=')
                line = line.strip()
                default = default.strip()
            else:
                default = None
            typ, name = line.rsplit(' ', 1)
            typ = TYPE_DEF.get(typ, typ)
            if name.endswith(']'):
                start_dim = name.find('[')
                dim = int(name[start_dim+1:-1])
                name = name[:start_dim]
            else:
                dim = None
            if 'gap' in name or 'pad' in name:
                name = 'pad'
            struct.attrs.append(Attribute(name, typ, dim, default))
    return struct_dict


def get_structs():
    with open('input.h', 'rU') as f:
        text = comment_remover(f.read())
    return parse_header(text)

license_header = '''\
# Copyright (c) Mathias Kaerlev 2013-2014.
#
# This file is part of cuwo.
#
# cuwo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cuwo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cuwo.  If not, see <http://www.gnu.org/licenses/>.

"""
%s

NOTE: This file is automatically generated. Do not modify.
"""
'''


def get_mask_condition(index):
    return 'mask & (<uint64_t>1 << %s) != 0' % index


def main():
    structs = get_structs()

    out = FormattedOutput('Entity data read/write')
    out.putln('cimport cython')
    out.putln('from cuwo.common cimport int64_t, uint64_t')
    out.putln('from cuwo.bytes cimport ByteReader, ByteWriter')
    out.putln()
    out.putln()

    for struct in structs.values():
        if struct.defs:
            for d in struct.defs:
                name, val = d
                out.putln('%s = %s' % (name, val))
            out.putln()
            out.putln()

        out.putln('@cython.final')
        out.putln('cdef class %s:' % struct.name)
        out.indent()

        # reset func
        # out.putln('def reset(self):')
        # out.indent()
        # for attr in struct.attrs:
        #     if attr.default is None:
        #         continue
        #     if attr.dim and attr.typ != 'int8':
        #         out.putln('self.%s = [%s] * %s' % (attr.name, attr.default,
        #                                            attr.dim))
        #     else:
        #         out.putln('self.%s = %s' % (attr.name, attr.default))
        # out.putln('pass')
        # out.dedent()
        # out.putln()

        out.putln('cdef public:')
        out.indent()
        for attr in struct.attrs:
            name, typ, dim, spec = attr.get()
            if name == 'pad':
                continue
            if dim:
                if typ == 'int8':
                    typ = 'str'
                else:
                    typ = 'list'
            else:
                typ = CYTHON_TYPES.get(typ, typ)
            out.putln('%s %s' % (typ, name))
        if struct.name == 'EntityData':
            out.putln('uint64_t mask')
        out.dedent()
        out.putln()

        if struct.name == 'EntityData':
            out.putln('def __cinit__(self):')
            out.indent()
            out.putln('self.mask = 0')
            out.dedent()
            out.putln()

        # read func
        out.putln('cpdef read(self, ByteReader reader):')
        out.indent()
        for attr in struct.attrs:
            name, typ, dim, spec = attr.get()
            if name == 'pad':
                out.putln('reader.skip(%s)' % dim)
                continue
            if dim is not None and typ == 'int8':
                out.putln('self.%s = reader.read_ascii(%s)' % (name, dim))
                continue
            if dim is not None:
                out.putln('self.%s = []' % name)
                out.putln('for _ in range(%s):' % dim)
                out.indent()
                if spec:
                    out.putln('new_item = %s()' % typ)
                    out.putln('(<%s>new_item).read(reader)' % typ)
                    out.putln('self.%s.append(new_item)' % name)
                else:
                    out.putln('self.%s.append(reader.read_%s())' % (name, typ))
                out.dedent()
                continue
            if spec:
                out.putln('self.%s = %s()' % (name, typ))
                out.putln('self.%s.read(reader)' % name)
            else:
                out.putln('self.%s = reader.read_%s()' % (name, typ))
        out.dedent()
        out.putln()

        # write func
        out.putln('cpdef write(self, ByteWriter writer):')
        out.indent()
        for attr in struct.attrs:
            name, typ, dim, spec = attr.get()
            if name == 'pad':
                out.putln('writer.pad(%s)' % dim)
                continue
            if dim is not None and typ == 'int8':
                out.putln('writer.write_ascii(self.%s, %s)' % (name, dim))
                continue
            if dim is not None:
                out.putln('for item in self.%s:' % name)
                out.indent()
                if spec:
                    out.putln('item.write(writer)')
                else:
                    out.putln('writer.write_%s(item)' % typ)
                out.dedent()
                continue
            if spec:
                out.putln('self.%s.write(writer)' % name)
            else:
                out.putln('writer.write_%s(self.%s)' % (typ, name))
        out.dedent()

        if struct.name == 'EntityData':
            # setters
            bits = {}

            for d in struct.defs:
                orig_name, value = d
                if not orig_name.endswith('_BIT'):
                    continue
                value = int(value)
                name = orig_name[:-4].lower()
                bits[value] = name

            for index in sorted(bits):
                name = bits[index]

        out.dedent()
        out.putln()
        out.putln()

    # mask data
    mask_data = []
    mask_input = open('masked_read.h', 'rb').read().decode('utf-8')
    mask_input = mask_input.splitlines()
    entity_struct = structs['EntityData']
    for bit_index, line in enumerate(mask_input):
        start = line.find('read_') + 5
        end = line.find('_masked', start)
        size = int(line[start:end])
        attr_start = line.find('->')
        if attr_start == -1:
            attr = 'x'
        else:
            attr_end = line.find(');')
            attr = line[attr_start+2:attr_end]
        offset = 0
        for struct_attr in entity_struct.attrs:
            name, typ, dim, spec = struct_attr.get()
            if name == attr:
                break
            offset += 1
        else:
            print(attr)
            raise NotImplementedError()
        mask_data.append((offset, size))

    for index in sorted(bits):
        name = bits[index]
        func_name = 'is_%s_set' % name
        out.putln('cpdef inline bint %s(uint64_t mask):' % func_name)
        out.indent()
        out.putln('return %s' % get_mask_condition(index))
        out.dedent()
        out.putln()
        out.putln()

    # read masked data
    out.putln('cpdef uint64_t read_masked_data(EntityData entity, '
              'ByteReader reader):')
    out.indent()
    out.putln('cdef uint64_t mask = reader.read_uint64()')

    for bit_index, v in enumerate(mask_data):
        offset, size = v
        out.putln('if %s:' % get_mask_condition(bit_index))
        out.indent()

        name, typ, dim, spec = entity_struct.attrs[offset].get()

        if spec:
            if dim:
                out.putln('for item in entity.%s:' % name)
                out.indent()
                out.putln('(<%s>item).read(reader)' % typ)
                out.dedent()
            else:
                out.putln('entity.%s.read(reader)' % name)
        else:
            while size > 0:
                name, typ, dim, spec = entity_struct.attrs[offset].get()
                if typ == 'int8' and dim is not None:
                    out.putln('entity.%s = reader.read_ascii(%s)' % (
                        name, dim))
                elif dim is not None:
                    out.putln('entity.%s = []' % name)
                    out.putln('for _ in xrange(%s):' % dim)
                    out.indent()
                    out.putln('entity.%s.append(reader.read_%s())' % (name,
                                                                      typ))
                    out.dedent()
                else:
                    out.putln('entity.%s = reader.read_%s()' % (name, typ))
                size -= TYPE_SIZE[typ] * (dim or 1)
                offset += 1
            if size != 0:
                raise NotImplementedError()
        out.dedent()
    out.putln()
    out.putln('return mask')
    out.dedent()
    out.putln()
    out.putln()

    # get masked size
    out.putln('cpdef unsigned int get_masked_size(uint64_t mask):')
    out.indent()
    out.putln('cdef unsigned int size = 0')
    for bit_index, v in enumerate(mask_data):
        offset, size = v
        out.putln('if %s:' % get_mask_condition(bit_index))
        out.indent()
        out.putln('size += %s' % size)
        out.dedent()
    out.putln('return size')
    out.dedent()
    out.putln()
    out.putln()

    # write masked data (send everything)
    out.putln('cpdef write_masked_data(EntityData entity, ByteWriter writer, '
              'uint64_t mask):')
    out.indent()
    out.putln('writer.write_uint64(mask)')
    for bit_index, v in enumerate(mask_data):
        out.putln('if %s:' % get_mask_condition(bit_index))
        out.indent()
        offset, size = v
        name, typ, dim, spec = entity_struct.attrs[offset].get()

        if spec:
            if dim:
                out.putln('for item in entity.%s:' % name)
                out.indent()
                out.putln('(<%s>item).write(writer)' % typ)
                out.dedent()
            else:
                out.putln('entity.%s.write(writer)' % name)
        else:
            while size > 0:
                name, typ, dim, spec = entity_struct.attrs[offset].get()
                if typ == 'int8' and dim is not None:
                    out.putln('writer.write_ascii(entity.%s, %s)' % (
                        name, dim))
                elif dim is not None:
                    out.putln('for item in entity.%s:' % name)
                    out.indent()
                    out.putln('writer.write_%s(item)' % (typ))
                    out.dedent()
                else:
                    out.putln('writer.write_%s(entity.%s)' % (typ, name))
                size -= TYPE_SIZE[typ] * (dim or 1)
                offset += 1
        out.dedent()
    out.dedent()

    open('../cuwo/entity.pyx', 'wb').write(out.get())

    # sounds
    sound_input = open('sounds.h', 'rb').read().decode('utf-8')
    sound_input = sound_input.splitlines()
    sounds = {}
    current_index = None
    for line in sound_input:
        if 'case ' in line:
            start = line.find('case ') + 5
            end = line.find(':', start)
            current_index = int(line[start:end])
        elif '.wav"' in line:
            end = line.find('.wav"')
            start = line.rfind('"', 0, end) + 1
            sound_name = line[start:end]
            sounds[current_index] = sound_name

    out = FormattedOutput('Constant string definition file')
    out.write_dict('SOUNDS', sounds)

    print('Writing defs from tgen')
    tgen.initialize(1234, '../data/')
    out.write_dict('ITEM_NAMES', tgen.get_item_names())
    out.write_dict('STATIC_NAMES', tgen.get_static_names())
    out.write_dict('ENTITY_NAMES', tgen.get_entity_names())
    out.write_dict('LOCATION_NAMES', tgen.get_location_names())
    out.write_dict('QUARTER_NAMES', tgen.get_quarter_names())

    def remove(value, rem):
        new_dict = {}
        for k, v in value.items():
            new_dict[k] = v.replace(rem, '')
        return new_dict

    out.write_dict('SKILL_NAMES', remove(tgen.get_skill_names(), 'Skill'))
    out.write_dict('ABILITY_NAMES', remove(tgen.get_ability_names(),
                                           'Ability'))
    print('Done')

    open('../cuwo/defs.py', 'wb').write(out.get())


if __name__ == "__main__":
    main()