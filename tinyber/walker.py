# -*- Mode: Python -*-

from asn1ate.sema import (
    ChoiceType, ExtensionMarker, SequenceType, SetOfType, SizeConstraint,
    SingleValueConstraint, TaggedType, ValueRangeConstraint, ValueListType,
    dependency_sort
)

class Walker (object):

    def __init__(self, sema_module, nodes):
        self.sema_module = sema_module
        self.tag_assignments = {}
        self.defined_types = []
        self.nodes = nodes

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
        return self.nodes.c_choice (name, alts)

    def gen_SequenceType (self, ob, name=None):
        slots = []
        for c in ob.components:
            slot_type = self.gen_dispatch (c.type_decl)
            slot_name = c.identifier
            slots.append ((slot_name, slot_type))
        return self.nodes.c_sequence (name, slots)

    def constraint_get_min_max_size (self, ob):
        if isinstance (ob, SizeConstraint):
            return self.constraint_get_min_max_size (ob.nested)
        elif isinstance (ob, SingleValueConstraint):
            return int (ob.value), int (ob.value)
        elif isinstance (ob, ValueRangeConstraint):
            return int (ob.min_value), int (ob.max_value)
        else:
            raise NotImplementedError ("testing")

    def gen_SequenceOfType (self, ob):
        min_size, max_size = self.constraint_get_min_max_size (ob.size_constraint)
        array_type = self.gen_dispatch (ob.type_decl)
        return self.nodes.c_sequence_of (array_type, min_size, max_size)

    def gen_TaggedType (self, ob):
        # XXX for now, only support [APPLICATION X] SEQUENCE {}
        # assert (isinstance (ob.type_decl, SequenceType))
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
        elif isinstance (type_decl, SetOfType):
            node = self.gen_SetOfType (type_decl, name=type_name)
        elif isinstance (type_decl, ValueListType):
            node = self.gen_ValueListType (type_decl, name=type_name)
        else:
            node = self.gen_dispatch (type_decl)
        self.defined_types.append ((type_name, node, type_decl))

    def gen_SimpleType (self, ob):
        if ob.constraint:
            min_size, max_size = self.constraint_get_min_max_size (ob.constraint)
        else:
            min_size, max_size = None, None
        return self.nodes.c_base_type (ob.type_name, min_size, max_size)

    def gen_ValueListType (self, ob, name=None):
        alts = []
        for sub in ob.named_values:
            if sub.value is not None:
                alts.append ((sub.identifier, sub.value))
            else:
                alts.append ((sub.identifier, None))
        return self.nodes.c_enumerated (name, alts)

    def gen_DefinedType (self, ob):
        for type_name, node, type_decl in self.defined_types:
            if ob.type_name == type_name:
                return self.nodes.c_defined (ob.type_name, node.max_size())
        raise ValueError (ob.type_name)

    def gen_SetOfType (self, ob):
        min_size, max_size = self.constraint_get_min_max_size (ob.size_constraint)
        item_type = self.gen_dispatch (ob.type_decl)
        return self.nodes.c_set_of (item_type, min_size, max_size)

    def gen_dispatch (self, ob):
        name = ob.__class__.__name__
        probe = getattr (self, 'gen_%s' % (name,), None)
        if not probe:
            raise KeyError ("unhandled node type %r" % (name,))
        else:
            return probe (ob)

    def walk (self):
        assignment_components = dependency_sort (self.sema_module.assignments)
        for component in assignment_components:
            for assignment in component:
                self.gen_dispatch (assignment)
