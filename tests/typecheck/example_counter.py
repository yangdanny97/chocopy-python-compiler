class Counter(object):
  n : int = 0
  def __init__(self : Counter):
    pass
  def inc(self : Counter):
    self.n = self.n + 1

c : Counter = None
c = Counter()
c.inc()
print(c.n)
c.inc()
print(c.n)