# -*- Mode: Python -*-

import sys
import keyword
from asn1ate import parser
from asn1ate.support import pygen
from asn1ate.sema import *

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

    def emit (self, out):
        # emit a C type declaration for this node.
        pass

    def emit_decode (self, out, lval, src):
        # out: a c_writer.
        # lval: a string representing an lval - always a pointer.
        # src: a string representing the the buf_t* being read from.
        pass

def csafe (s):
    return s.replace ('-', '_')

class c_writer:

    def __init__ (self, stream):
        self.stream = stream
        self.indent_level = 0

    def indent (self):
        return self

    def __enter__ (self):
        self.indent_level += 1

    def __exit__ (self, t, v, tb):
        self.indent_level -= 1

    def writelines (self, *lines):
        for line in lines:
            self.stream.write ('  ' * self.indent_level)
            self.stream.write (line)
            self.stream.write ('\n')

    def newline (self):
        self.stream.write ('\n')

    def write (self, s, indent=False):
        if indent:
            self.stream.write ('  ' * self.indent_level)
        self.stream.write (s)

def int_max_size_type ( max_size):
    if max_size is None:
        # unconstrained int type.
        return 'asn1int_t'
    elif max_size < 2**8:
        return 'uint8_t'
    elif max_size < 2**16:
        return 'uint16_t'
    elif max_size < 2**32:
        return 'uint32_t'
    elif max_size < 2**64:
        return 'uint64_t'
    else:
        raise NotImplementedError()

# type grammar
# type ::= base_type | sequence | sequence_of | choice | enumerated | defined
# base_type ::= (INTEGER | BOOLEAN | OCTETSTRING), max_size
# sequence ::= (name, type)+
# sequence_of ::= (type, max_size)
# choice ::= (name, tag, type)+
# enumerated ::= (name, val)+

class c_base_type (c_node):
    def __init__ (self, name, max_size=None):
        c_node.__init__ (self, 'base_type', (name, max_size), [])
        
    def emit (self, out):
        type_name, max_size = self.attrs
        if type_name == 'OCTET STRING' or type_name == 'UTF8String':
            out.writelines ('struct {')
            with out.indent():
                out.writelines (
                    'uint8_t val[%s];' % (max_size,),
                    'int len;'
                    )
            out.write ('} ')
        elif type_name == 'BOOLEAN':
            out.write ('asn1bool_t', True)
        elif type_name == 'INTEGER':
            out.write (int_max_size_type (max_size), True)
        else:
            import pdb; pdb.set_trace()

    tag_map = {
        'OCTET STRING' : 'TAG_OCTETSTRING',
        'UTF8String' : 'TAG_UTF8STRING',
        'INTEGER' : 'TAG_INTEGER',
        'BOOLEAN' : 'TAG_BOOLEAN',
    }

    def tag_name (self):
        type_name, max_size = self.attrs
        return self.tag_map[type_name]

    def emit_decode (self, out, lval, src):
        type_name, max_size = self.attrs
        out.writelines (
            'CHECK (decode_TLV (&tlv, %s))' % (src,),
            'if (tlv.type != %s) { return -1; }' % (self.tag_map[type_name],),
        )
        if type_name == 'OCTET STRING' or type_name == 'UTF8String':
            out.writelines (
                'if (tlv.length > %d) { return -1; }' % (max_size,),
                'memcpy ((*%s).val, tlv.value, tlv.length);' % (lval,),
                '(*%s).len = tlv.length;' % (lval,),
                )
        elif type_name == 'INTEGER':
            out.writelines (
                'intval = decode_INTEGER (&tlv);',
            )
            if max_size is not None:
                out.writelines (
                    'if (intval > %s) { return -1; }' % (max_size,),
                )
            out.writelines (
                '*(%s) = intval;' % (lval,)
            )
        elif type_name == 'BOOLEAN':
            out.writelines (
                '*(%s) = decode_BOOLEAN (&tlv);' % (lval,),
            )
        else:
            import pdb; pdb.set_trace()            


class c_sequence (c_node):
    def __init__ (self, name, pairs):
        slots, types = zip(*pairs)
        c_node.__init__ (self, 'sequence', (name, slots,), types)
    def emit (self, out):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('struct %s {' % (name,))
        with out.indent():
            for i in range (len (slots)):
                slot_name = csafe (slots[i])
                slot_type = types[i]
                slot_type.emit (out)
                out.write (' %s;' % (slot_name,))
                out.newline()
        out.write ('}')

    def emit_decode (self, out, lval, src):
        name, slots = self.attrs
        types = self.subs
        out.writelines (
            'CHECK (decode_TLV (&tlv, %s));' % (src,),
            'if (tlv.type != TAG_SEQUENCE) { return -1; }',
            '{'
        )
        with out.indent():
            out.writelines (
                'buf_t src0;',
                'init_ibuf (&src0, tlv.value, tlv.length);'
            )
            for i in range (len (slots)):
                out.writelines ('// slot %s' % (slots[i],))
                slot_type = types[i]
                slot_type.emit_decode (out, '&(%s->%s)' % (lval, csafe (slots[i])), '&src0')
        out.writelines ('}')

class c_sequence_of (c_node):
    def __init__ (self, seq_type, max_size):
        c_node.__init__ (self, 'sequence_of', (max_size,), [seq_type])

    def emit (self, out):
        max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines ('struct {')
        with out.indent():
            seq_type.emit (out)
            out.write (' val[%s];' % (max_size,))
            out.newline()
            out.writelines ('int len;')
        out.write ('}', True)

    def emit_decode (self, out, lval, src):
        max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines ('{')
        with out.indent():
            out.writelines (
                'buf_t src1;',
                'int i;'
                'CHECK (decode_TLV (&tlv, %s));' % (src,),
                'if (tlv.type != TAG_SEQUENCE) { return -1; }',
                'init_ibuf (&src1, tlv.value, tlv.length);',
                'for (i=0; (src1.pos < src1.size); i++) {',
            )
            with out.indent():
                out.writelines ('if (i >= %s) { return -1; }' % (max_size,),)
                seq_type.emit_decode (out, '%s.val[i]' % (lval,), '&src1')
                out.writelines ('(%s)->len = i;' % (lval,))
            out.writelines ('}')
        out.writelines ('}')

class c_choice (c_node):
    def __init__ (self, name, alts):
        names, tags, types = zip(*alts)
        c_node.__init__ (self, 'choice', (name, names, tags), types)
    def emit (self, out):
        name, slots, tags = self.attrs
        out.writelines ('struct %s {' % (name,))
        with out.indent():
            out.writelines ('%s_PR present;' % (name,))
            out.writelines ('union %s_u {' % (name,))
            with out.indent():
                for i in range (len (slots)):
                    slot_name = csafe (slots[i])
                    type_name = self.subs[i].name()
                    out.writelines ('%s_t %s;' % (type_name, slot_name))
            out.writelines ('} choice;')
        out.write ('}')
        
    def emit_enum (self, out):
        name, slots, tags = self.attrs
        # first emit the enum for type_PR
        out.writelines ('typedef enum {')
        with out.indent():
            for i in range (len (slots)):
                out.writelines ('%s_PR_%s = %s,' % (name, csafe (slots[i]), tags[i]))
        out.writelines ('} %s_PR;' % (name,), '')
        
    def emit_decode (self, out, lval, src):
        name, slots, tags = self.attrs
        types = self.subs
        out.writelines ('{')
        with out.indent():
            out.writelines (
                'buf_t src0;',
                'CHECK (decode_TLV (&tlv, %s));' % (src,),
                'init_ibuf (&src0, tlv.value, tlv.length);',
                'switch (tlv.type) {',
                )
            with out.indent():
                for i in range (len (slots)):
                    type_name = types[i].name()
                    tag_name = csafe (slots[i])
                    out.writelines (
                        'case (%s | FLAG_APPLICATION | FLAG_STRUCTURED):' % (tags[i],),
                        '  %s->present = %s_PR_%s;' % (lval, name, tag_name),
                        '  CHECK (decode_%s (&(%s->choice.%s), &src0))' % (type_name, lval, tag_name),
                        '  break;',
                    )
                out.writelines (
                    'default:', '  return -1;', '  break;'
                )
            out.writelines ('}')
        out.writelines ('}')

class c_enumerated (c_node):
    def __init__ (self, pairs):
        c_node.__init__ (self, 'enumerated', (pairs,), [])

    def emit (self, out):
        alts, = self.attrs
        out.write ('enum {\n')
        with out.indent():
            for name, val in alts:
                if val is not None:
                    out.writelines ('%s = %s,' % (name, val))
                else:
                    out.writelines ('%s,' % (name,))
        out.write ('}')

    def emit_decode (self, out, lval, src):
        alts, = self.attrs
        out.writelines ('{')
        with out.indent():
            out.writelines (
                'CHECK (decode_TLV (&tlv, %s))' % (src,),
                'if (tlv.type != TAG_ENUMERATED) { return -1; }',
                'intval = decode_INTEGER (&tlv);',
                'switch (intval) {'
                )
            with out.indent():
                for name, val in alts:
                    out.writelines ('case %s: break;' % (val,))
                out.writelines ('default: return -1;')
            out.writelines ('}')
            out.writelines ('*%s = intval;' % (lval,))
        out.writelines ('}')

class c_defined (c_node):
    def __init__ (self, name):
        c_node.__init__ (self, 'defined', (name,), [])
    def name (self):
        name, = self.attrs
        return name
    def emit (self, out):
        name, = self.attrs
        out.write ('%s_t' % (name,), True)
    def emit_decode (self, out, lval, src):
        type_name, = self.attrs
        out.writelines (
            'CHECK (decode_%s (%s, %s));' % (type_name, lval, src),
        )
        
class TinyBERBackend(object):
    def __init__(self, sema_module, out):
        self.sema_module = sema_module
        self.out = c_writer (out)

    def gen_ChoiceType (self, ob, name=None):
        alts = []
        for c in ob.components:
            if isinstance (c, ExtensionMarker):
                continue
            if not isinstance (c.type_decl, TaggedType):
                raise NotImplementedError ("CHOICE elements need a tag")
            tag = c.type_decl.class_number
            slot_type = self.gen_dispatch (c.type_decl.type_decl)
            slot_name = c.identifier
            alts.append ((slot_name, tag, slot_type))
        return c_choice (name, alts)

    def gen_SequenceType (self, ob, name=None):
        slots = []
        for c in ob.components:
            slot_type = self.gen_dispatch (c.type_decl)
            slot_name = c.identifier
            slots.append ((slot_name, slot_type))
        return c_sequence (name, slots)

    def constraint_get_max_size (self, ob):
        if isinstance (ob, SizeConstraint):
            return self.constraint_get_max_size (ob.nested)
        elif isinstance (ob, SingleValueConstraint):
            return int (ob.value)
        elif isinstance (ob, ValueRangeConstraint):
            return int (ob.max_value)
        else:
            raise NotImplementedError ("testing")

    def gen_SequenceOfType (self, ob):
        max_size = self.constraint_get_max_size (ob.size_constraint)
        array_type = self.gen_dispatch (ob.type_decl)
        return c_sequence_of (array_type, max_size)

    def gen_TaggedType (self, ob):
        # XXX for now, only support [APPLICATION X] SEQUENCE {}
        #assert (isinstance (ob.type_decl, SequenceType))
        raise NotImplementedError ('put your tags inside the SEQUENCE definition')

    def gen_TypeAssignment (self, ob):
        type_name, type_decl = ob.type_name, ob.type_decl
        # strip (and record) tag information if present
        if isinstance (type_decl, TaggedType):
            tag = type_decl.class_number, type_decl.implicit
            type_decl = type_decl.type_decl
            self.tag_assignments[type_name] = tag
        if isinstance (type_decl, ChoiceType):
            node = self.gen_ChoiceType (type_decl, name=type_name)
        elif isinstance (type_decl, SequenceType):
            node = self.gen_SequenceType (type_decl, name=type_name)
        else:
            node = self.gen_dispatch (type_decl)
        self.defined_types.append ((type_name, node, type_decl))

    def gen_SimpleType (self, ob):
        if ob.constraint:
            max_size = self.constraint_get_max_size (ob.constraint)
        else:
            max_size = None
        return c_base_type (ob.type_name, max_size)

    def gen_ValueListType (self, ob):
        alts = []
        for sub in ob.named_values:
            if sub.value is not None:
                alts.append ((sub.identifier, sub.value))
            else:
                alts.append ((sub.identifier, None))
        return c_enumerated (alts)

    def gen_DefinedType (self, ob):
        return c_defined (ob.type_name)

    def gen_dispatch (self, ob):
        name = ob.__class__.__name__
        probe = getattr (self, 'gen_%s' % (name,), None)
        if not probe:
            raise KeyError ("unhandled node type %r" % (name,))
        else:
            return probe (ob)

    def gen_decoder (self, type_name, type_decl, node):
        # generate a decoder for a type assignment.
        out = self.out
        out.writelines (
            'int',
            'decode_%s (%s_t * dst, buf_t * src)' % (type_name, type_name),
            '{',
        )
        with self.out.indent():
            out.writelines (
                'asn1raw_t tlv;',
                'asn1int_t intval;'
            )
            node.emit_decode (out, 'dst', 'src')
            out.writelines ('return 0;')
        out.writelines ('}')
        
    def gen_codec_funs (self, type_name, type_decl, node):
        self.gen_decoder (type_name, type_decl, node)
        #self.gen_encoder (type_name, type_decl, node)

    def generate_code(self):
        self.decls = []
        self.tag_assignments = {}
        self.defined_types = []
        W = self.out.writelines
        W ('', '// generated by %r' % sys.argv, '// *** do not edit ***'  '')
        W ('#include <stdint.h>')
        W ('#include <string.h>')
        W ('#include "tinyber.h"', '')
        W ('#define CHECK(x) if (-1 == (x)) { return -1; }', '')
        
        assignment_components = dependency_sort (self.sema_module.assignments)
        for component in assignment_components:
            for assignment in component:
                self.gen_dispatch (assignment)
        out = self.out
        for (type_name, node, type_decl) in self.defined_types:
            if isinstance (node, c_choice):
                node.emit_enum (out)
            out.write ('typedef ')
            node.emit (self.out)
            out.writelines (' %s_t;' % (type_name,), '')
        for (type_name, node, type_decl) in self.defined_types:
            self.gen_codec_funs (type_name, type_decl, node)
            W ('\n')
        return self.decls

def generate_tinyber (sema_module, out_stream):
    backend = TinyBERBackend (sema_module, out_stream)
    decls = backend.generate_code()
    return decls

def main(args):
    with open(args[0]) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)

    modules = build_semantic_model(parse_tree)

    assert (len(modules) == 1)

    decls = generate_tinyber (modules[0], sys.stdout)

    from pprint import pprint as pp
    for node in decls:
        #pp (node.dump())
        #node.emit (sys.stdout)
        #print ('----------')
        print()

    return modules[0], decls

if __name__ == '__main__':
    m, d = main (sys.argv[1:])
