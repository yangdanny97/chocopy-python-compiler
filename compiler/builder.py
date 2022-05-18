from unicodedata import name


class Builder:
    def __init__(self, name: str):
        self.name = name
        self.lines = []  # list of strings or children builders
        self.indentation = 0

    def newLine(self, line=""):
        self.lines.append((self.indentation*"    ") + line)
        return self

    # returns a reference to the child builder
    def newBlock(self):
        child = Builder(self.name)
        child.indentation = self.indentation
        self.lines.append(child)
        return child

    def addText(self, text=""):
        if len(self.lines) == 0:
            self.newLine()
        self.lines[-1] = self.lines[-1] + text
        return self

    def indent(self):
        self.indentation += 1
        return self

    def unindent(self):
        self.indentation -= 1
        return self

    def emit(self) -> str:
        lines = []
        for l in self.lines:
            if isinstance(l, str):
                lines.append(l)
            else:
                lines.append(l.emit())
        return "\n".join(lines)
