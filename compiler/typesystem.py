from .types import *
from typing import List, Dict, Tuple, Any, Optional, cast, Union


class ClassInfo:
    orderedAttrs: List[str]
    attrs: Dict[str, Tuple[ValueType, Any]]
    methods: Dict[str, FuncType]

    def __init__(self, name: str, superclass: Optional[str] = None):
        self.name = name
        self.superclass = superclass
        self.attrs = {}  # (attr type, init value)
        self.methods = {}  # type of method
        self.orderedAttrs = []

    def __str__(self):
        return F"class {self.name}({self.superclass}): {self.attrs} {self.methods}"


class TypeSystem:
    classes: Dict[str, ClassInfo]

    def __init__(self):
        # information for each class
        self.classes = {}

        objectInfo = ClassInfo("object")
        objectInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        intInfo = ClassInfo("int", "object")
        intInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        boolInfo = ClassInfo("bool", "object")
        boolInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        strInfo = ClassInfo("str", "object")
        strInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        self.classes["object"] = objectInfo
        self.classes["int"] = intInfo
        self.classes["bool"] = boolInfo
        self.classes["str"] = strInfo
        self.classes["<None>"] = ClassInfo("<None>", "object")
        self.classes["<Empty>"] = ClassInfo("<Empty>", "object")

    def getMethodHelper(self, className: str, methodName: str) -> Tuple[Optional[FuncType], str]:
        # requires className to be the name of a valid class
        classInfo = self.classes[className]
        if methodName not in classInfo.methods:
            if classInfo.superclass is None:
                return (None, "")
            return self.getMethodHelper(classInfo.superclass, methodName)
        return (classInfo.methods[methodName], className)

    def getMethod(self, className: str, methodName: str) -> Optional[FuncType]:
        # requires className to be the name of a valid class
        return self.getMethodHelper(className, methodName)[0]

    def getMethodDefClass(self, className: str, methodName: str) -> str:
        # returns the class that the method was originally defined in
        # requires className to be the name of a valid class
        return self.getMethodHelper(className, methodName)[1]

    def getAttrHelper(self, className: str, attrName: str) -> Tuple[Optional[ValueType], Any]:
        # requires className to be the name of a valid class
        classInfo = self.classes[className]
        if attrName not in classInfo.attrs:
            if classInfo.superclass is None:
                return (None, None)
            return self.getAttrHelper(classInfo.superclass, attrName)
        return classInfo.attrs[attrName]

    def getAttr(self, className: str, attrName: str) -> Optional[ValueType]:
        # returns type of attribute
        # requires className to be the name of a valid class
        return self.getAttrHelper(className, attrName)[0]

    def getAttrInit(self, className: str, attrName: str) -> Any:
        # returns initial value of attribute
        # requires className to be the name of a valid class
        return self.getAttrHelper(className, attrName)[1]

    def getAttrOrMethod(self, className: str, name: str) -> Optional[SymbolType]:
        # returns type of attribute or method
        # requires className to be the name of a valid class
        classInfo = self.classes[className]
        if name in classInfo.methods:
            return classInfo.methods[name]
        elif name in classInfo.attrs:
            return classInfo.attrs[name][0]
        else:
            if classInfo.superclass is None:
                return None
            return self.getAttrOrMethod(classInfo.superclass, name)

    def classExists(self, className: str) -> bool:
        # we cannot check for None because it is a defaultdict
        return className in self.classes

    def isSubClass(self, a: str, b: str) -> bool:
        # requires a and b to be the names of valid classes
        # return if a is the same class or subclass of b
        curr = a
        # pyrefly: ignore [bad-assignment]
        while curr is not None:
            if curr == b:
                return True
            else:
                curr = self.classes[curr].superclass
        return False

    def isSubtype(self, a: Optional[Union[ValueType, FuncType]], b: ValueType) -> bool:
        # return if a is a subtype of b
        if b == ObjectType():
            return True
        if isinstance(a, ClassValueType) and isinstance(b, ClassValueType):
            return self.isSubClass(a.className, b.className)
        return a == b

    def canAssign(self, a: Optional[Union[ValueType, FuncType]], b: ValueType) -> bool:
        # return if value of type a can be assigned/passed to type b (ex: b = a)
        if self.isSubtype(a, b):
            return True
        if a == NoneType() and b not in [IntType(), StrType(), BoolType()]:
            return True
        if isinstance(b, ListValueType) and a == EmptyType():
            return True
        if (isinstance(b, ListValueType) and isinstance(a, ListValueType) and a.elementType == NoneType()):
            return self.canAssign(a.elementType, b.elementType)
        return False

    def join(self, a: ValueType, b: ValueType) -> ValueType:
        # return closest mutual ancestor on typing tree
        if self.canAssign(a, b):
            return b
        if self.canAssign(b, a):
            return a
        if isinstance(b, ListValueType) and isinstance(a, ListValueType):
            return ListValueType(self.join(b.elementType, a.elementType))
        # if only 1 of the types is a list then the closest ancestor is object
        if isinstance(b, ListValueType) or isinstance(a, ListValueType):
            return ObjectType()
        # for 2 classes that aren't related by subtyping
        # find paths from A & B to root of typing tree
        aCls, bCls = cast(ClassValueType, a).className, cast(
            ClassValueType, b).className
        aAncestors = []
        bAncestors = []
        curr = aCls
        while curr is not None and self.classes[curr].superclass is not None:
            if curr != aCls:
                aAncestors.append(self.classes[curr].superclass)
            curr = self.classes[curr].superclass
        curr = bCls
        while curr is not None and self.classes[curr].superclass is not None:
            if curr != bCls:
                bAncestors.append(self.classes[curr].superclass)
            curr = self.classes[curr].superclass
        # reverse lists to find lowest common ancestor
        aAncestors = aAncestors[::-1]
        bAncestors = bAncestors[::-1]
        for i in range(min(len(aAncestors), len(bAncestors))):
            if aAncestors[i] != bAncestors[i]:
                return ClassValueType(self.classes[aAncestors[i - 1]].name)
        # this really shouldn't be returned
        return ObjectType()

    def getOrderedMethods(self, className: str) -> List[Tuple[str, FuncType, str]]:
        # (name, signature, defined in class)
        methods = []
        classInfo = self.classes[className]
        if classInfo.superclass is not None:
            methods = self.getOrderedMethods(classInfo.superclass)
        for name in classInfo.methods:
            hasExisting = False
            for i in range(len(methods)):
                # pyrefly: ignore [bad-index]
                if methods[i][0] == name:
                    # pyrefly: ignore [unsupported-operation]
                    methods[i] = (
                        name, classInfo.methods[name], className)
                    hasExisting = True
                    break
            if not hasExisting:
                # pyrefly: ignore [missing-attribute]
                methods.append(
                    (name, classInfo.methods[name], className))
        # pyrefly: ignore [bad-return]
        return methods

    def getMappedMethods(self, className: str) -> Dict[str, Tuple[FuncType, str]]:
        # map of name -> signature, defined in class
        ordered = self.getOrderedMethods(className)
        return {x: (y, z) for x, y, z in ordered}

    def getOrderedAttrs(self, className: str) -> List[Tuple[str, ValueType, Any]]:
        # return list of (name, type, init value) triples
        attrs = []
        classInfo = self.classes[className]
        if classInfo.superclass is not None:
            attrs = self.getOrderedAttrs(classInfo.superclass)
        for attr in classInfo.orderedAttrs:
            attrType, attrInit = classInfo.attrs[attr]
            attrs.append((attr, attrType, attrInit))
        return attrs

    def getMappedAttrs(self, className: str) -> Dict[str, Tuple[ValueType, Any]]:
        # map of name -> type, init value tuples
        ordered = self.getOrderedAttrs(className)
        return {x: (y, z) for x, y, z in ordered}
