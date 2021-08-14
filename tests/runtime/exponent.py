# Compute x**y
def exp(x: int, y: int) -> int:
	a: int = 0
	def f(i: int) -> int:
		nonlocal a
		def geta() -> int:
			return a
		if i <= 0:
			return geta()
		else:
			a = a * x
			return f(i-1)
	a = 1
	return f(y)

# Input parameter
n:int = 42

# Run [0, n]
i:int = 0

# Crunch
while i <= n:
	print(exp(2, i % 31))
	i = i + 1

__assert__(exp(2,3) == 8)
__assert__(exp(3,3) == 27)
__assert__(exp(3,4) == 81)
__assert__(exp(4,4) == 256)
__assert__(exp(5,1) == 5)
__assert__(exp(1,99) == 1)