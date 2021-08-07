class Link(object):
  val : int = 0
  next : "Link" = None
  def __init__(self : "Link"):
    pass
  def new(self : "Link", val : int, next : "Link") -> "Link":
    self.val = val
    self.next = next
    return self

class LinkedList(object):
  head : Link = None
  def __init(self : "LinkedList"):
    pass
  def is_empty(self : "LinkedList") -> bool:
    return self.head is None
  def length(self : "LinkedList") -> int:
    cur : Link = None
    length : int = 0
    cur = self.head
    while not (cur is None):
      length = length + 1
      cur = cur.next
    return length
  def add(self : "LinkedList", val : int):
    self.head = Link().new(val, self.head)

x:LinkedList = None

x = LinkedList()
__assert__(x.is_empty())
__assert__(x.length() == 0)
x.add(1)
__assert__(not x.is_empty())
__assert__(x.length() == 1)
__assert__(x.head.val == 1)
x.add(100)
__assert__(not x.is_empty())
__assert__(x.length() == 2)
__assert__(x.head.val == 100)
__assert__(x.head.next.val == 1)