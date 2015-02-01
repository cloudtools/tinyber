# -*- Mode: Python -*-

from tinyber import nodes

def psafe (s):
    return s.replace ('-', '_')

class c_base_type (nodes.c_base_type):

    def emit (self, out):
        pass

    def emit_decode (self, out):
        type_name, min_size, max_size = self.attrs
        if type_name == 'INTEGER':
            out.writelines ('v = src.next_INTEGER (%s,%s)' % (min_size, max_size),)
        elif type_name == 'OCTET STRING':
            out.writelines ('v = src.next_OCTET_STRING (%s,%s)' % (min_size, max_size),)
        elif type_name == 'BOOLEAN':
            out.writelines ('v = src.next_BOOLEAN()')
        else:
            import pdb; pdb.set_trace()

    def emit_encode (self, out, val):
        type_name, min_size, max_size = self.attrs
        if type_name == 'INTEGER':
            out.writelines ('dst.emit_INTEGER (%s)' % (val,))
        elif type_name == 'OCTET STRING':
            out.writelines ('dst.emit_OCTET_STRING (%s)' % (val,))
        elif type_name == 'BOOLEAN':
            out.writelines ('dst.emit_BOOLEAN (%s)' % (val,))
        else:
            import pdb; pdb.set_trace()

class c_sequence (nodes.c_sequence):

    def emit (self, out):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('__slots__ = (%s)' % (', '.join ("'%s'" % x for x in slots)))

    def emit_decode (self, out):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('src = src.next (TAG.SEQUENCE)')
        for i in range (len (slots)):
            slot_name = slots[i]
            slot_type = types[i]
            slot_type.emit_decode (out)
            out.writelines ('self.%s = v' % (slot_name,))

    def emit_encode (self, out, val):
        name, slots = self.attrs
        types = self.subs
        out.writelines ('with dst.TLV (TAG.SEQUENCE):')
        with out.indent():
            for i in reversed (range (len (types))):
                types[i].emit_encode (out, 'self.%s' % (slots[i],))

class c_sequence_of (nodes.c_sequence_of):

    def emit (self, out):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs

    def emit_decode (self, out):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines (
            'src, save = src.next (TAG.SEQUENCE), src',
            'a = []',
            'while not src.done():'
            )
        with out.indent():
            seq_type.emit_decode (out)
            out.writelines ('a.append (v)')
        out.writelines ("# check constraints")
        out.writelines ('v, src = a, save')

    def emit_encode (self, out, val):
        min_size, max_size, = self.attrs
        [seq_type] = self.subs
        out.writelines ('with dst.TLV (TAG.SEQUENCE):')
        with out.indent():
            out.writelines ('for v in reversed (%s):' % (val,))
            with out.indent():
                seq_type.emit_encode (out, 'v')

class c_choice (nodes.c_choice):

    def emit (self, out):
        name, slots, tags = self.attrs
        
    def emit_enum (self, out):
        name, slots, tags = self.attrs
        
    def emit_decode (self, out):
        name, slots, tags = self.attrs
        types = self.subs
        out.writelines (
            'tag, src = src.next_APPLICATION()'
            )
        for i in range (len (tags)):
            out.writelines ('if tag == %s:' % (tags[i],))
            with out.indent():
                types[i].emit_decode (out)
            
    def emit_encode (self, out, val):
        name, slots, tags = self.attrs
        types = self.subs
        

class c_enumerated (nodes.c_enumerated):

    def emit (self, out):
        alts, = self.attrs
        out.writelines ('# emit test?')

    def emit_decode (self, out):
        alts, = self.attrs
        out.writelines (
            'v = src.next_ENUMERATED()',
            'if v not in self.valid_enums:',
            )
        with out.indent():
            out.writelines ('raise BadEnum (v)')

    def emit_encode (self, out, val):
        alts, = self.attrs

class c_defined (nodes.c_defined):

    def emit (self, out):
        name, max_size = self.attrs

    def emit_decode (self, out):
        type_name, max_size = self.attrs
        out.writelines (
            'v = %s()' % (type_name,),
            'v.decode(src)',
            )

    def emit_encode (self, out, val):
        type_name, max_size = self.attrs
        
