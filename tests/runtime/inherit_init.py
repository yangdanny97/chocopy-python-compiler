# this is the same as linked_list.py except LinkedList.__init__ is inherited

class Link(object):
    val: int = 0
    next: "Link" = None

    def __init__(self: "Link"):
        pass

    def new(self: "Link", val: int, next: "Link") -> "Link":
        self.val = val
        self.next = next
        return self


class LinkedList(object):
    head: Link = None

    def __init(self: "LinkedList"):
        pass

    def is_empty(self: "LinkedList") -> bool:
        return self.head is None

    def length(self: "LinkedList") -> int:
        cur: Link = None
        length: int = 0
        cur = self.head
        while not (cur is None):
            length = length + 1
            cur = cur.next
        return length

    def add(self: "LinkedList", val: int):
        self.head = Link().new(val, self.head)


x: LinkedList = None

x = LinkedList()
assert x.is_empty()
assert x.length() == 0
x.add(1)
assert not x.is_empty()
assert x.length() == 1
assert x.head.val == 1
x.add(100)
assert not x.is_empty()
assert x.length() == 2
assert x.head.val == 100
assert x.head.next.val == 1
