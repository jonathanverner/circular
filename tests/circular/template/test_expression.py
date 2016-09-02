from unittest.mock import patch
from pytest import raises
from tests.utils import TObserver

import src.circular.template.expression as exp
from src.circular.template.context import Context


def test_parse_number():
    assert exp.parse_number(" 123.5.6", 1) == (123.5, 6)
    assert exp.parse_number(" 123.5z", 1) == (123.5, 6)
    assert exp.parse_number(" -123.5z", 1) == (-123.5, 7)


def test_parse_string():
    assert exp.parse_string("'ahoj\\''", 0) == ("ahoj\'", 8)
    assert exp.parse_string('"123456"', 0) == ("123456", 8)
    assert exp.parse_string('"\\\\3456"', 0) == ("\\3456", 8)


def test_tokenize():
    tl = list(exp.tokenize("a - b"))
    assert tl == [
        (exp.T_IDENTIFIER, "a", 1),
        (exp.T_OPERATOR, "-", 3),
        (exp.T_IDENTIFIER, "b", 5),
    ]
    tl = list(exp.tokenize("'123'+123.5==[ahoj]"))
    assert tl == [
           (exp.T_STRING, "123", 5),
           (exp.T_OPERATOR, "+", 6),
           (exp.T_NUMBER, 123.5, 11),
           (exp.T_OPERATOR, '==', 13),
           (exp.T_LBRACKET, '[', 14),
           (exp.T_IDENTIFIER, 'ahoj', 18),
           (exp.T_RBRACKET, ']', 19)
    ]
    tl = list(exp.tokenize("a is   not b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_OPERATOR, "is not", 10),
           (exp.T_IDENTIFIER, 'b', 12),
    ]
    tl = list(exp.tokenize("a is       b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_OPERATOR, "is", 4),
           (exp.T_IDENTIFIER, 'b', 12),
    ]
    tl = list(exp.tokenize("a !=       b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_OPERATOR, "!=", 4),
           (exp.T_IDENTIFIER, 'b', 12),
    ]
    tl = list(exp.tokenize("a <=       b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_OPERATOR, "<=", 4),
           (exp.T_IDENTIFIER, 'b', 12),
    ]
    tl = list(exp.tokenize("a =       b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_EQUAL, "=", 3),
           (exp.T_IDENTIFIER, 'b', 11),
    ]
    tl = list(exp.tokenize("a <       b"))
    assert tl == [
           (exp.T_IDENTIFIER, "a", 1),
           (exp.T_OPERATOR, "<", 3),
           (exp.T_IDENTIFIER, 'b', 11),
    ]
    tl = list(exp.tokenize("for a in lst"))
    assert tl == [
           (exp.T_KEYWORD, "for", 3),
           (exp.T_IDENTIFIER, "a", 5),
           (exp.T_KEYWORD, 'in', 8),
           (exp.T_IDENTIFIER, 'lst', 12),
    ]


def parse_mock(token_stream, end_tokens=[]):
    if len(token_stream) == 0:
        raise Exception("End of stream")
    tok, val, pos = token_stream.pop(0)
    if tok == exp.T_COLON:
        return exp.IdentNode('None'), tok, 0
    elif tok == exp.T_RBRACKET:
        return None, tok, 0
    if tok == exp.T_IDENTIFIER:
        return exp.IdentNode(val), token_stream.pop(0)[0], 0
    else:
        return exp.ConstNode(val), token_stream.pop(0)[0], 0


@patch('src.circular.template.expression._parse', parse_mock)
def test_parse_args():
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COMMA, ',', 0),
        (exp.T_IDENTIFIER, 'b', 0),
        (exp.T_COMMA, ',', 0),
        (exp.T_IDENTIFIER, 'c', 0),
        (exp.T_EQUAL, '=', 0),
        (exp.T_NUMBER, 123, 0),
        (exp.T_RPAREN, ')', 0)
    ]
    assert str(exp.parse_args(token_stream)) == "([a, b], {'c': 123})"
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COMMA, ',', 0),
        (exp.T_IDENTIFIER, 'b', 0),
        (exp.T_RPAREN, ')', 0)
    ]
    assert str(exp.parse_args(token_stream)) == "([a, b], {})"
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_EQUAL, '=', 0),
        (exp.T_IDENTIFIER, 'b', 0),
        (exp.T_RPAREN, ')', 0)
    ]
    assert str(exp.parse_args(token_stream)) == "([], {'a': b})"


@patch('src.circular.template.expression._parse', parse_mock)
def test_parse_lst():
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COMMA, ',', 0),
        (exp.T_NUMBER, 123, 0),
        (exp.T_COMMA, ',', 0),
        (exp.T_STRING, 'ahoj', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_lst(token_stream)) == "[a, 123, 'ahoj']"
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_KEYWORD, 'for', 0),
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_KEYWORD, 'in', 0),
        (exp.T_IDENTIFIER, 'lst', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    c = exp.parse_lst(token_stream)
    assert str(c) == "[a for a in lst]"
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_KEYWORD, 'for', 0),
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_KEYWORD, 'in', 0),
        (exp.T_IDENTIFIER, 'lst', 0),
        (exp.T_KEYWORD, 'if', 0),
        (exp.T_IDENTIFIER, 'True', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_lst(token_stream)) == "[a for a in lst if True]"


@patch('src.circular.template.expression._parse', parse_mock)
def test_parse_slice():
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_slice(token_stream)) == '(False, a, None, None)'
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COLON, ':', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_slice(token_stream)) == '(True, a, None, None)'
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COLON, ':', 0),
        (exp.T_NUMBER, 123, 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_slice(token_stream)) == '(True, a, 123, None)'
    token_stream = [
        (exp.T_COLON, ':', 0),
        (exp.T_NUMBER, 123, 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_slice(token_stream)) == '(True, None, 123, None)'
    token_stream = [
        (exp.T_IDENTIFIER, 'a', 0),
        (exp.T_COLON, ':', 0),
        (exp.T_NUMBER, 123, 0),
        (exp.T_COLON, ':', 0),
        (exp.T_IDENTIFIER, 'b', 0),
        (exp.T_RBRACKET, ']', 0)
    ]
    assert str(exp.parse_slice(token_stream)) == '(True, a, 123, b)'


def test_parse_interpolated_string():
    ctx = Context()
    ctx.name = 'Name'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ "ahoj" }} final text.')
    val = "".join([ast.evalctx(ctx) for ast in asts])
    assert val == 'Test text 4 other text ahoj final text.'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ name }} final text.')
    val = "".join([ast.evalctx(ctx) for ast in asts])
    assert val == 'Test text 4 other text Name final text.'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ len(name) }} final text.')
    val = "".join([ast.evalctx(ctx) for ast in asts])
    assert val == 'Test text 4 other text 4 final text.'

    asts = exp.parse_interpolated_str('Test text {{ "{{{{}}{}{}}}" }} other }}')
    val = "".join([ast.evalctx(ctx) for ast in asts])
    assert val == 'Test text {{{{}}{}{}}} other }}'


def test_parse():
    ctx = Context()

    # Test Simple Arithmetic Expressions
    ast, _ = exp.parse('(1+1*8)*9')
    assert ast.evalctx(ctx) is 81

    # Test Simple Arithmetic Expressions
    ast, _ = exp.parse('(1-1)')
    assert ast.evalctx(ctx) is 0

    # Test Simple Arithmetic Expressions
    ast, _ = exp.parse('(-1)')
    assert ast.evalctx(ctx) is -1

    # Test Boolean Expressions
    ast, _ = exp.parse('True and False')
    assert ast.evalctx(ctx) is False

    ast, _ = exp.parse('True and not False')
    assert ast.evalctx(ctx) is True

    # Test is
    ast, _ = exp.parse("1 is None")
    assert ast.evalctx(ctx) is False

    ast, _ = exp.parse("None is None")
    assert ast.evalctx(ctx) is True

    ast, _ = exp.parse("False is not None")
    assert ast.evalctx(ctx) is True

    # Test Slices
    ctx.s = "abcde"
    ast, _ = exp.parse('s[-1]')
    assert ast.evalctx(ctx) == 'e'
    ast, _ = exp.parse('s[0]')
    assert ast.evalctx(ctx) == 'a'
    ast, _ = exp.parse('s[1:3]')
    assert ast.evalctx(ctx) == 'bc'
    ast, _ = exp.parse('s[0:-1:2]')
    assert ast.evalctx(ctx) == 'ac'
    ast, _ = exp.parse('s[1:]')
    assert ast.evalctx(ctx) == 'bcde'
    ast, _ = exp.parse('s[:-1]')
    assert ast.evalctx(ctx) == 'abcd'

    # Test Lists
    ast, _ = exp.parse('[1,2,3,4]')
    assert ast.evalctx(ctx) == [1, 2, 3, 4]

    # Test Comprehension
    ast, _ = exp.parse('[p+1 for p in [1,2,3,4]]')
    assert ast.evalctx(ctx) == [2, 3, 4, 5]

    ast, _ = exp.parse('[p+1 for p in [1,2,3,4] if p%2==0]')
    assert ast.evalctx(ctx) == [3, 5]

    # Test Builtins
    ast, _ = exp.parse("str(10)")
    assert ast.evalctx(ctx) == "10"

    ast, _ = exp.parse("int('21')")
    assert ast.evalctx(ctx) == 21

    ast, _ = exp.parse("len([1,2,3])")
    assert ast.evalctx(ctx) == 3

    ctx.str = lambda x: "str("+str(x)+")"
    ast, _ = exp.parse("str(10)")
    assert str(ast) == "str(10)"
    del ctx.str

    # Test Object Access
    ctx.obj = Context()
    ctx.obj.a = 10
    ctx.obj.b = Context()
    ctx.obj.b.c = 20
    ctx.obj.d = [Context({'a': 30})]

    ast, _ = exp.parse('obj.a')
    assert ast.evalctx(ctx) == 10

    ast, _ = exp.parse('obj.b.c')
    assert ast.evalctx(ctx) == 20

    ast, _ = exp.parse('obj.d[0].a')
    assert ast.evalctx(ctx) == 30

    # Test Array Access
    ast, _ = exp.parse('mylst[0][1][2]')
    ctx.mylst = [[None, [None, None, "Ahoj"]]]
    assert ast.evalctx(ctx) == "Ahoj"

    # Test String slices
    ast, _ = exp.parse('"ahoj"[1:]')
    assert ast.evalctx(ctx) == "hoj"
    ast, _ = exp.parse('"ahoj"[:1]')
    assert ast.evalctx(ctx) == "a"
    ast, _ = exp.parse('"ahoj"[-1]')
    assert ast.evalctx(ctx) == "j"

    # Test array concatenation
    ast, _ = exp.parse('([0]+["mixin"])[1]')
    assert ast.evalctx(ctx) == "mixin"

    # Test Function Calls
    ast, _ = exp.parse('"a,b,c,d".split(",")')
    assert ast.evalctx(ctx) == ['a', 'b', 'c', 'd']

    ctx.func = lambda x, ev: str(x+10)+ev
    ctx.ch = 20
    ctx.s = 'Hi'
    ast, _ = exp.parse("func(ch,ev=s)")
    ast.bind_ctx(ctx)
    ctx.s = 'Hello'
    assert ast.eval() == '30Hello'
    assert ast.evalctx(ctx) == '30Hello'

    # Test Complex Expressions
    expr = '(1+2*obj.a - 10)'
    ast, _ = exp.parse(expr)
    assert ast.evalctx(ctx) == 11

    expr = '[(1+2*a[1+3] - 10) for a in [[2,1,2,3,4,5],[1,2],[2,2,2,2,2,2,2]] if a[0] % 2 == 0]'
    ast, _ = exp.parse(expr)
    assert ast.evalctx(ctx) == [-1, -5]

    # Test parse cache
    for i in range(10):
        expr = '[(1+2*a[1+3] - 10) for a in [[2,1,2,3,4,5],[1,2],[2,2,2,2,2,2,2]] if a[0] % 2 == 0]'
        ast, _ = exp.parse(expr)
        assert ast.evalctx(ctx) == [-1, -5]


def test_is_func():
    ast, _ = exp.parse('(1+1*x)*9')
    assert ast.is_function_call() is False

    ast, _ = exp.parse('x')
    assert ast.is_function_call() is False

    ast, _ = exp.parse('f(1+1*x)')
    assert ast.is_function_call() is True

    ast, _ = exp.parse('a.b[10].f(1+1*x)')
    assert ast.is_function_call() is True


def test_is_ident():
    ast, _ = exp.parse('(1+1*x)*9')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('f(1+1*x)')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('None')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('1')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('"ahoj"')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('[1,2,3]')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('x[1:2:3]')
    assert ast.is_assignable() is False

    ast, _ = exp.parse('a.b[10].f')
    assert ast.is_assignable() is True

    ast, _ = exp.parse('a.b[x].f')
    assert ast.is_assignable() is True

    ast, _ = exp.parse('a.b[x]')
    assert ast.is_assignable() is True

    ast, _ = exp.parse('a.b')
    assert ast.is_assignable() is True

    ast, _ = exp.parse('x')
    assert ast.is_assignable() is True


class TestCall(object):

    def setup_method(self, method):
        self.called = False
        self.ctx = Context()

    def test_call(self):
        self.obj = None
        self.event = None

        def handler(x, event):
            self.obj = x
            self.event = event
            self.called = True

        self.ctx.handler = handler
        self.ctx.ch = 10
        ast, _ = exp.parse("handler(ch)")
        ast.bind_ctx(self.ctx)
        assert self.called is False
        ast.call(event='Event')
        assert self.obj == 10
        assert self.event == 'Event'
        assert self.called is True
        self.called = False

        a = ast.clone()
        assert a.is_function_call()
        assert self.called is False


def test_eval_assignment():
    ctx = Context()

    # Do not allow assigning to non-trivial expressions
    ast, _ = exp.parse('(1+1*x)*9')
    with raises(Exception):
        ast.value = 10

    # Do not allow assigning to built-in constants
    ast, _ = exp.parse('True')
    with raises(Exception):
        ast.value = 10

    # Do not allow assigning to function calls
    ast, _ = exp.parse('f(1)')
    with raises(Exception):
        ast.value = 10

    # Do not allow assigning to constant lists
    ast, _ = exp.parse("[1,2,3,4]")
    with raises(Exception):
        ast.value = 10

    # Do not allow assigning to constants
    ast, _ = exp.parse("'ahoj'")
    with raises(Exception):
        ast.value = 10

    # Allow assigning to non-existing variables
    ast, _ = exp.parse('x')
    ast.bind_ctx(ctx)
    ast.value = 10
    assert ctx.x == 10

    # Allow assigning to existing variables
    ast.value = 20
    assert ctx.x == 20

    # Allow assigning to list elements
    ctx.lst = [1, 2, 3]
    ctx.x = 0
    ast, _ = exp.parse("lst[x]")
    ast.bind_ctx(ctx)
    ast.value = 20
    assert ctx.lst[0] == 20

    # Allow assigning to non-existing object attributes
    ctx.obj = Context()
    ast, _ = exp.parse('obj.test')
    ast.bind_ctx(ctx)
    ast.value = 30987
    assert ctx.obj.test == 30987

    # Allow assigning to existing object attributes
    ast.value = 40
    assert ctx.obj.test == 40


class MockObject(object):
    def __init__(self, depth=0):
        if depth > 0:
            self.child = MockObject(depth-1)
        else:
            self.leaf = True


class TestExpressionChanges(object):

    def setup_method(self, method):
        self.ctx = Context()
        self.ctx._clear()

    def prepare(self, expr):
        self.obs, _ = exp.parse(expr)
        self.obs.bind_ctx(self.ctx)
        try:
            self.obs.eval()
        except:
            pass
        self.t = TObserver(self.obs)

    def exec_test(self, new):
        data = self.t.events.pop().data

        if new is not None:
            assert self.obs.value == new
        else:
            assert self.obs.cache_status is False
            try:
                self.obs.eval()
            except:
                pass
            assert self.obs.defined is False
            assert 'value' not in data

    def test_clone(self):
        self.prepare("x**2 + x")
        clone = self.obs.clone()
        ctx = Context()
        ctx.x = 0
        clone.bind_ctx(ctx)
        self.ctx.x = 1
        assert clone.value == 0
        assert self.obs.value == 2

    def test_arithmetic_exp(self):
        self.ctx.a = 1
        self.ctx.b = -2
        self.ctx.c = 0.5

        self.prepare("a*x**2 + b*x + c*x")
        assert self.obs.cache_status is False
        assert self.obs.defined is False

        self.ctx.d = 10
        assert len(self.t.events) == 0

        self.ctx.x = 0
        self.exec_test(0)

        self.ctx.x = 1
        self.exec_test(-0.5)

    def test_comprehension(self):
        self.ctx.lst = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
        self.prepare("[p+1 for p in lst if p%2 == 0]")
        assert self.obs.cache_status is True

        self.ctx.lst.append(4)
        assert self.obs.cache_status is False
        self.exec_test([-3, -1, 1, 3, 5, 5])

        self.ctx.lst.remove(4)
        self.exec_test([-3, -1, 1, 3, 5])

        self.ctx.lst.clear()
        self.exec_test([])

    def test_attr_acces(self):
        self.ctx.root = MockObject(depth=3)
        self.prepare("root.child.child.child.leaf and True")
        assert self.obs.value is True
        assert self.obs.cache_status is True

        self.ctx.root.child.child.child.leaf = False
        assert self.obs.cache_status is False
        self.exec_test(False)

        self.ctx.root.child = None
        self.exec_test(None)

    def test_func(self):
        self.ctx.func = lambda x, y: x+y
        self.prepare("func(a,b)")
        assert self.obs.cache_status is False

        self.ctx.a = 10
        assert self.obs.cache_status is False

        self.ctx.b = 20
        assert self.obs.cache_status is False
        self.exec_test(30)

        self.ctx.b = 30
        self.exec_test(40)

        self.ctx.func = lambda x, y: x*y
        self.exec_test(300)

        del self.ctx.a
        self.exec_test(None)

    def test_array_index(self):
        self.ctx.lst = [[1, 2, 3], 2, 3, 4, 5]
        self.ctx.a = 0
        self.prepare("lst[0][a]")
        assert self.obs.cache_status is True
        assert self.obs.value == 1

        self.ctx.lst[1] = 2
        self.exec_test(1)
        self.ctx.a = 2
        self.exec_test(3)
        self.ctx.a = 3
        self.exec_test(None)
        self.ctx.lst[0].append(4)
        self.exec_test(4)
        self.ctx.lst.pop()
        self.exec_test(4)
