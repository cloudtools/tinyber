# -*- Mode: Python -*-

class IndentContext:

    def __init__ (self, writer, scope=False):
        self.writer = writer
        self.scope = scope

    def __enter__ (self):
        if self.scope:
            self.writer.writelines ('{')
        self.writer.indent_level += 1

    def __exit__ (self, t, v, tb):
        self.writer.indent_level -= 1
        if self.scope:
            self.writer.writelines ('}')

class Writer:

    def __init__ (self, stream, indent_size=2):
        self.stream = stream
        self.indent_level = 0
        self.base_indent = ' ' * indent_size

    def indent (self):
        return IndentContext (self, False)

    def scope (self):
        return IndentContext (self, True)

    def writelines (self, *lines):
        for line in lines:
            self.stream.write (self.base_indent * self.indent_level)
            self.stream.write (line)
            self.stream.write ('\n')

    def newline (self):
        self.stream.write ('\n')

    def write (self, s, indent=False):
        if indent:
            self.stream.write (self.base_indent * self.indent_level)
        self.stream.write (s)

    def close (self):
        self.stream.close()
