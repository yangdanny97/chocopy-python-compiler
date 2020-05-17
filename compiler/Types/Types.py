from .ClassValueType import ClassValueType

def ObjectType():
    return ClassValueType("object")

def IntType():
    return ClassValueType("int")

def StrType():
    return ClassValueType("str")

def BoolType():
    return ClassValueType("bool")

def NoneType():
    return ClassValueType("<none>")

def EmptyType():
    return ClassValueType("<empty>")