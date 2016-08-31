from src.circular.template.context import Context


def test_extension():
    base = Context()
    base.a = 10
    base.c = 30

    child = Context(base=base)

    # Child should have access to parent
    assert child.a == 10

    # The _get method should work for accessing parent
    assert child._get('a') == 10

    # Child should not be allowed to modify parent
    child.a = 20
    assert child.a == 20
    assert base.a == 10

    # Attributes should propagate recursively
    second_child = Context(base=child)
    assert second_child.c == 30
    assert second_child.a == 20

