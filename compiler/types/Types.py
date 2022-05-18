from .classvaluetype import ClassValueType

# factories for types


def ObjectType():
    return ClassValueType("object")


def IntType():
    return ClassValueType("int")


def StrType():
    return ClassValueType("str")


def BoolType():
    return ClassValueType("bool")


def NoneType():
    return ClassValueType("<None>")


def EmptyType():
    return ClassValueType("<Empty>")
