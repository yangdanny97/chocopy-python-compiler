def foo() -> bool:
    assert False
    return True


print(True or foo())
print(False and foo())
