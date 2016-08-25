from unittest.mock import patch
import src.circular.template.expression as exp
from src.circular.template.context import Context



def test_parse_number():
    assert exp.parse_number(" 123.5.6",1) == (123.5,6)
    assert exp.parse_number(" 123.5z",1) == (123.5,6)
    assert exp.parse_number(" -123.5z",1) == (-123.5,7)

def test_parse_string():
    assert exp.parse_string("'ahoj\\''",0) == ("ahoj\'",8)
    assert exp.parse_string('"123456"',0) == ("123456",8)
    assert exp.parse_string('"\\\\3456"',0) == ("\\3456",8)

def test_tokenize():
    tl = list(exp.tokenize("a - b"))
    assert tl == [
        (exp.T_IDENTIFIER,"a",1),
        (exp.T_OPERATOR,"-",3),
        (exp.T_IDENTIFIER,"b",5),
    ]
    tl = list(exp.tokenize("'123'+123.5==[ahoj]"))
    assert  tl == [
           (exp.T_STRING,"123",5),
           (exp.T_OPERATOR,"+",6),
           (exp.T_NUMBER,123.5,11),
           (exp.T_OPERATOR,'==',13),
           (exp.T_LBRACKET,'[',14),
           (exp.T_IDENTIFIER,'ahoj',18),
           (exp.T_RBRACKET,']',19)
    ]
    tl = list(exp.tokenize("a is   not b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_OPERATOR,"is not",10),
           (exp.T_IDENTIFIER,'b',12),
    ]
    tl = list(exp.tokenize("a is       b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_OPERATOR,"is",4),
           (exp.T_IDENTIFIER,'b',12),
    ]
    tl = list(exp.tokenize("a !=       b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_OPERATOR,"!=",4),
           (exp.T_IDENTIFIER,'b',12),
    ]
    tl = list(exp.tokenize("a <=       b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_OPERATOR,"<=",4),
           (exp.T_IDENTIFIER,'b',12),
    ]
    tl = list(exp.tokenize("a =       b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_EQUAL,"=",3),
           (exp.T_IDENTIFIER,'b',11),
    ]
    tl = list(exp.tokenize("a <       b"))
    assert  tl == [
           (exp.T_IDENTIFIER,"a",1),
           (exp.T_OPERATOR,"<",3),
           (exp.T_IDENTIFIER,'b',11),
    ]
    tl = list(exp.tokenize("for a in lst"))
    assert  tl == [
           (exp.T_KEYWORD,"for",3),
           (exp.T_IDENTIFIER,"a",5),
           (exp.T_KEYWORD,'in',8),
           (exp.T_IDENTIFIER,'lst',12),
    ]

def parse_mock(token_stream,end_tokens=[]):
    if len(token_stream) == 0:
        raise Exception("End of stream")
    tok,val,pos = token_stream.pop(0)
    if tok == exp.T_COLON:
        return exp.IdentNode('None'), tok, 0
    elif tok == exp.T_RBRACKET:
        return None, tok, 0
    if tok == exp.T_IDENTIFIER:
        return exp.IdentNode(val),token_stream.pop(0)[0],0
    else:
        return exp.ConstNode(val),token_stream.pop(0)[0],0

@patch('src.circular.template.expression._parse',parse_mock)
def test_parse_args():
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COMMA,',',0),
        (exp.T_IDENTIFIER,'b',0),
        (exp.T_COMMA,',',0),
        (exp.T_IDENTIFIER,'c',0),
        (exp.T_EQUAL,'=',0),
        (exp.T_NUMBER,123,0),
        (exp.T_RPAREN,')',0)
    ]
    assert str(exp.parse_args(token_stream)) ==  "([a, b], {'c': 123})"
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COMMA,',',0),
        (exp.T_IDENTIFIER,'b',0),
        (exp.T_RPAREN,')',0)
    ]
    assert str(exp.parse_args(token_stream)) ==  "([a, b], {})"
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_EQUAL,'=',0),
        (exp.T_IDENTIFIER,'b',0),
        (exp.T_RPAREN,')',0)
    ]
    assert str(exp.parse_args(token_stream)) ==  "([], {'a': b})"

@patch('src.circular.template.expression._parse',parse_mock)
def test_parse_lst():
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COMMA,',',0),
        (exp.T_NUMBER,123,0),
        (exp.T_COMMA,',',0),
        (exp.T_STRING,'ahoj',0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_lst(token_stream)) == "[a, 123, 'ahoj']"
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_KEYWORD,'for',0),
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_KEYWORD,'in',0),
        (exp.T_IDENTIFIER,'lst',0),
        (exp.T_RBRACKET,']',0)
    ]
    c=exp.parse_lst(token_stream)
    assert str(c) ==  "[a for a in lst]"
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_KEYWORD,'for',0),
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_KEYWORD,'in',0),
        (exp.T_IDENTIFIER,'lst',0),
        (exp.T_KEYWORD,'if',0),
        (exp.T_IDENTIFIER,'True',0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_lst(token_stream)) ==  "[a for a in lst if True]"

@patch('src.circular.template.expression._parse',parse_mock)
def test_parse_slice():
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_slice(token_stream)) ==  '(False, a, None, None)'
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COLON,':',0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_slice(token_stream)) ==  '(True, a, None, None)'
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COLON,':',0),
        (exp.T_NUMBER,123,0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_slice(token_stream)) ==  '(True, a, 123, None)'
    token_stream = [
        (exp.T_COLON,':',0),
        (exp.T_NUMBER,123,0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_slice(token_stream)) ==  '(True, None, 123, None)'
    token_stream = [
        (exp.T_IDENTIFIER,'a',0),
        (exp.T_COLON,':',0),
        (exp.T_NUMBER,123,0),
        (exp.T_COLON,':',0),
        (exp.T_IDENTIFIER,'b',0),
        (exp.T_RBRACKET,']',0)
    ]
    assert str(exp.parse_slice(token_stream)) ==  '(True, a, 123, b)'

def test_parse_interpolated_string():
    ctx = Context()
    ctx.name = 'Name'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ "ahoj" }} final text.')
    val = "".join([ast.evaluate(ctx) for ast in asts])
    assert val == 'Test text 4 other text ahoj final text.'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ name }} final text.')
    val = "".join([ast.evaluate(ctx) for ast in asts])
    assert val == 'Test text 4 other text Name final text.'

    asts = exp.parse_interpolated_str('Test text {{ 1+3 }} other text {{ len(name) }} final text.')
    val = "".join([ast.evaluate(ctx) for ast in asts])
    assert val == 'Test text 4 other text 4 final text.'

    asts = exp.parse_interpolated_str('Test text {{ "{{{{}}{}{}}}" }} other }}')
    val = "".join([ast.evaluate(ctx) for ast in asts])
    assert val == 'Test text {{{{}}{}{}}} other }}'


def test_parse():
    ctx = Context()

    # Test Simple Arithmetic Expressions
    ast = exp.parse('(1+1*8)*9')
    assert ast.evaluate(ctx) is 81

    # Test Simple Arithmetic Expressions
    ast = exp.parse('(1-1)')
    assert ast.evaluate(ctx) is 0

    # Test Simple Arithmetic Expressions
    ast = exp.parse('(-1)')
    assert ast.evaluate(ctx) is -1

    # Test Boolean Expressions
    ast = exp.parse('True and False')
    assert ast.evaluate(ctx) is False

    ast = exp.parse('True and not False')
    assert ast.evaluate(ctx) is True

    # Test is
    ast = exp.parse("1 is None")
    assert ast.evaluate(ctx) is False

    ast = exp.parse("None is None")
    assert ast.evaluate(ctx) is True

    ast = exp.parse("False is not None")
    assert ast.evaluate(ctx) is True

    # Test Slices
    ctx.s="abcde"
    ast = exp.parse('s[-1]')
    assert ast.evaluate(ctx) == 'e'
    ast = exp.parse('s[0]')
    assert ast.evaluate(ctx) == 'a'
    ast = exp.parse('s[1:3]')
    assert ast.evaluate(ctx) == 'bc'
    ast = exp.parse('s[0:-1:2]')
    assert ast.evaluate(ctx) == 'ac'
    ast = exp.parse('s[1:]')
    assert ast.evaluate(ctx) == 'bcde'
    ast = exp.parse('s[:-1]')
    assert ast.evaluate(ctx) == 'abcd'

    # Test Lists
    ast = exp.parse('[1,2,3,4]')
    assert ast.evaluate(ctx) == [1,2,3,4]

    # Test Comprehension
    ast = exp.parse('[p+1 for p in [1,2,3,4]]')
    assert ast.evaluate(ctx) == [2,3,4,5]

    ast = exp.parse('[p+1 for p in [1,2,3,4] if p%2==0]')
    assert ast.evaluate(ctx) == [3,5]

    # Test Builtins
    ast = exp.parse("str(10)")
    assert ast.evaluate(ctx) == "10"

    ast = exp.parse("int('21')")
    assert ast.evaluate(ctx) == 21

    ast = exp.parse("len([1,2,3])")
    assert ast.evaluate(ctx) == 3

    ctx.str=lambda x:"str("+str(x)+")"
    ast = exp.parse("str(10)") == "str(10)"
    del ctx.str


    # Test Object Access
    ctx.obj = Context()
    ctx.obj.a=10
    ctx.obj.b=Context()
    ctx.obj.b.c=20
    ctx.obj.d = [Context({'a':30})]

    ast = exp.parse('obj.a')
    assert ast.evaluate(ctx) == 10

    ast = exp.parse('obj.b.c')
    assert ast.evaluate(ctx) == 20

    ast = exp.parse('obj.d[0].a')
    assert ast.evaluate(ctx) == 30

    # Test Array Access
    ast = exp.parse('mylst[0][1][2]')
    ctx.mylst = [[None,[None,None,"Ahoj"]]]
    assert ast.evaluate(ctx) == "Ahoj"

    # Test String slices
    ast = exp.parse('"ahoj"[1:]')
    assert ast.evaluate(ctx) == "hoj"
    ast = exp.parse('"ahoj"[:1]')
    assert ast.evaluate(ctx) == "a"
    ast = exp.parse('"ahoj"[-1]')
    assert ast.evaluate(ctx) == "j"

    # Test array concatenation
    ast = exp.parse('([0]+["mixin"])[1]')
    assert ast.evaluate(ctx)  == "mixin"

    # Test Function Calls
    ast = exp.parse('"a,b,c,d".split(",")')
    assert ast.evaluate(ctx) == ['a', 'b', 'c', 'd']


    # Test Complex Expressions
    expr = '(1+2*obj.a - 10)'
    ast = exp.parse(expr)
    assert ast.evaluate(ctx) == 11

    expr = '[(1+2*a[1+3] - 10) for a in [[2,1,2,3,4,5],[1,2],[2,2,2,2,2,2,2]] if a[0] % 2 == 0]'
    ast = exp.parse(expr)
    assert ast.evaluate(ctx) == [-1,-5]

    # Test parse cache
    for i in range(10):
        expr = '[(1+2*a[1+3] - 10) for a in [[2,1,2,3,4,5],[1,2],[2,2,2,2,2,2,2]] if a[0] % 2 == 0]'
        ast = exp.parse(expr)
        assert ast.evaluate(ctx) == [-1,-5]
