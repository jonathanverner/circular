from src.circular.template.interpolatedstr import InterpolatedStr
from src.circular.template.context import Context
from tests.utils import TObserver




def test_string_interp():
    ctx = Context()
    ctx.name = "James"
    s = InterpolatedStr("My name is {{ surname }}, {{name}} {{ surname}}.")
    s.bind_ctx(ctx)
    t = TObserver(s)
    assert s.value == "My name is , James ."

    ctx.surname = "Bond"
    data = t.events.pop().data
    assert s.value == "My name is Bond, James Bond."

    # Should correctly interpolate two immediately succeeding expressions
    ctx.sur="B"
    s = InterpolatedStr('{{name}}{{sur}}')
    s.bind_ctx(ctx)
    assert s.value == "JamesB"









