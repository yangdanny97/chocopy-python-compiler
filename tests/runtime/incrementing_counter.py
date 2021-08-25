class Counter(object):
  n : int = 0
  def __init__(self : Counter):
    pass
  def inc(self : Counter):
    self.n = self.n + 1

c : Counter = None
i : int = 0
c = Counter()
c.inc()
__assert__(c.n == 1)
c.inc()
__assert__(c.n == 2)
c.inc()
c.inc()
__assert__(c.n == 4)

# for i in [9,9,9,9,9,9]:
#     c.inc()
# __assert__(c.n == 10)
