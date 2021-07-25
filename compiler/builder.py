class Builder:
    def __init__(self):
        self.lines = []
        self.indentation = 0

    def newLine(self, line=""):
        self.lines.append((self.indentation*"    ") + line)

    def addText(self, text=""):
        if len(self.lines) == 0:
            self.newLine()
        self.lines[-1] = self.lines[-1] + text

    def indent(self):
        self.indentation += 1

    def unindent(self):
        self.indentation -= 1

    def emit(self)->str:
        return "\n".join(self.lines)