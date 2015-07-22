# -*- Mode: Python -*-

from tinyber.ber import length_of_length, length_of_integer

class c_node:

    def __init__ (self, kind, attrs, subs):
        self.kind = kind
        self.attrs = attrs
        self.subs = subs

    def dump (self):
        if self.subs:
            return (self.kind, self.attrs, [x.dump() for x in self.subs])
        else:
            return (self.kind, self.attrs)

# type grammar
# type ::= base_type | sequence | sequence_of | choice | enumerated | defined
# base_type ::= (INTEGER | BOOLEAN | OCTETSTRING), max_size
# sequence ::= (name, type)+
# sequence_of ::= (type, max_size)
# choice ::= (name, tag, type)+
# enumerated ::= (name, val)+

class c_base_type (c_node):

    def __init__ (self, name, min_size=None, max_size=None):
        c_node.__init__ (self, 'base_type', (name, min_size, max_size), [])

    def max_size (self):
        type_name, min_size, max_size = self.attrs
        if type_name == 'OCTET STRING' or type_name == 'UTF8String':
            return 1 + length_of_length (max_size) + max_size
        elif type_name == 'BOOLEAN':
            return 1 + length_of_length (1) + 1
        elif type_name == 'INTEGER':
            if max_size is None:
                # this actually depends on what integer size is in use (asn1int_t)
                max_size = 2**64
            loi = length_of_integer (int (max_size))
            return 1 + length_of_length (loi) + loi
        elif type_name == 'NULL':
            return 2
        else:
            import pdb
            pdb.set_trace()

    tag_map = {
        'OCTET STRING': 'TAG_OCTETSTRING',
        'UTF8String': 'TAG_UTF8STRING',
        'INTEGER': 'TAG_INTEGER',
        'BOOLEAN': 'TAG_BOOLEAN',
        'NULL': 'TAG_NULL',
    }

    def tag_name (self):
        type_name, min_size, max_size = self.attrs
        return self.tag_map[type_name]

class c_sequence (c_node):

    def __init__ (self, name, pairs):
        slots, types = zip(*pairs)
        c_node.__init__ (self, 'sequence', (name, slots,), types)

    def max_size (self):
        name, slots = self.attrs
        types = self.subs
        r = 0
        for slot_type in types:
            r += slot_type.max_size()
        return 1 + length_of_length(r) + r

class c_sequence_of (c_node):

    def __init__ (self, seq_type, min_size, max_size):
        c_node.__init__ (self, 'sequence_of', (min_size, max_size,), [seq_type])

    def max_size (self):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs
        r = seq_type.max_size() * max_size
        return 1 + length_of_length(r) + r

class c_set_of (c_node):

    def __init__ (self, item_type, min_size, max_size):
        c_node.__init__ (self, 'set_of', (min_size, max_size,), [item_type])

    def max_size (self):
        min_size, max_size, = self.attrs
        [item_type] = self.subs
        r = item_type.max_size() * max_size
        return 1 + length_of_length(r) + r

class c_choice (c_node):

    def __init__ (self, name, alts):
        names, tags, types = zip(*alts)
        c_node.__init__ (self, 'choice', (name, names, tags), types)

    def max_size (self):
        name, slots, tags = self.attrs
        types = self.subs
        r = 0
        for slot_type in types:
            r = max (r, slot_type.max_size())
        return 1 + length_of_length (r) + r

class c_enumerated (c_node):

    def __init__ (self, name, pairs):
        c_node.__init__ (self, 'enumerated', (name, pairs), [])

    def max_size (self):
        _, alts, = self.attrs
        max_val = len(alts)
        for name, val in alts:
            if val is not None:
                max_val = max (max_val, int(val))
        loi = length_of_integer (max_val)
        return 1 + length_of_length (loi) + loi

class c_defined (c_node):

    def __init__ (self, name, max_size):
        c_node.__init__ (self, 'defined', (name, max_size), [])

    def name (self):
        name, max_size = self.attrs
        return name

    def max_size (self):
        name, max_size = self.attrs
        return max_size
