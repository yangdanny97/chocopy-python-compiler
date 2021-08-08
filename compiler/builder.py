class Builder:
    def __init__(self, name:str):
        self.name = name
        self.lines = []
        self.indentation = 0

    def newLine(self, line=""):
        self.lines.append((self.indentation*"    ") + line)
        return self

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

    def emit(self)->str:
        return "\n".join(self.lines)