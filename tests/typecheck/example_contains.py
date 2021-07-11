# Search in a list
def contains(items:[int], x:int) -> bool:
    i:int = 0
    while i < len(items):
        if items[i] == x:
            return True
        i = i + 1
    return False

if contains([4, 8, 15, 16, 23], 15):
  print("Item found!")    # Prints this
else:
  print("Item not found.")
