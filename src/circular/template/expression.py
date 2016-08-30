"""
    Parse (most) python expressions into an AST

    Notable differences:

      - chaining bool operators, e.g. `1 <= 2 < 3` is not supported

      - Tuples are not supported

      - dict constants are not supported
"""

ET_EXPRESSION = 0
ET_INTERPOLATED_STRING = 1

from circular.utils.events import EventMixin

from .observer import observe

T_SPACE = 0
T_NUMBER = 1            # A number immediately preceded by '-' is a negative number, the '-' is not taken as an operator, so 10-11 is not a valid expression
T_LBRACKET = 2
T_RBRACKET = 3
T_LPAREN = 4
T_RPAREN = 5
T_LBRACE = 6
T_RBRACE = 7
T_DOT=8
T_COMMA=9
T_COLON=10
T_OPERATOR = 11
T_STRING = 12           # Started by " or '; there is NO distinction between backslash escaping between the two; """,''' and modifiers (e.g. r,b) not implemented"
T_IDENTIFIER = 13       # Including True, False, None, an identifier starts by alphabetical character and is followed by alphanumeric characters and/or _$
T_LBRACKET_INDEX = 14   # Bracket starting a list slice
T_LBRACKET_LIST = 15    # Bracket starting a list
T_LPAREN_FUNCTION = 16  # Parenthesis starting a function call
T_LPAREN_EXPR = 17      # Parenthesis starting a subexpression
T_EQUAL = 18
T_KEYWORD = 19          # Warning: This does not include True,False,None; these fall in the T_IDENTIFIER category, also this includes 'in' which can, in certain context, be an operator
T_UNKNOWN = 20

OP_PRIORITY = {
    '(':-2,    # Parenthesis have lowest priority so that we always stop partial evaluation when
               # reaching a parenthesis
    '==':0,
    'and':0,
    'or':0,
    'is':0,
    'is not':0,
    'in':0,
    'not':1,   # not has higher priority then other boolean operations so that 'a and not b' is interpreted as 'a and (not b)'
    '+':2,
    '-':2,
    '*':3,
    '/':3,
    '//':3,
    '%':3,
    '-unary':4,
    '**':4,
    '[]':5,    # Array slicing/indexing
    '()':5,    # Function calling
    '.':5      # Attribute access has highest priority (e.g. a.c**2 is not a.(c**2), and a.func(b) is not a.(func(b)))
}

#match_token_res = [
    #(T_SPACE,re.compile('\s.*')),
    #(T_NUMBER,re.compile('[0-9].*')),
    #(T_LBRACKET,re.compile('\[.*')),
    #(T_RBRACKET,re.compile('\].*')),
    #(T_LPAREN,re.compile('\(.*')),
    #(T_RPAREN,re.compile('\).*')),
    #(T_LBRACE,re.compile('{')),
    #(T_RBRACE,re.compile('}')),
    #(T_DOT,re.compile('\..*')),
    #(T_COMMA,re.compile(',.*')),
    #(T_COLON,re.compile(':.*')),
    #(T_EQUAL,re.compile('=[^=].*')),
    #(T_OPERATOR,re.compile('([-+*/<>%].*)|(==.*)|(!=.*)|(<=.*)|(>=.*)|(or[^a-z_$])|(and[^a-z_$])|(is[^a-z_$])|(not[^a-z_$])')),
    #(T_STRING,re.compile('["\'].*')),
    #(T_KEYWORD,re.compile('(for[^a-z_$])|(if[^a-z_$].*)|(in[^a-z_$].*)')),
    #(T_IDENTIFIER,re.compile('[a-z_$].*',re.IGNORECASE)),
#]
def token_type(start_chars):
    """ Identifies the next token type based on the
        next four characters """
    first_char = start_chars[0]
    if first_char == ' ' or first_char == "\t" or first_char == "\n":
        return T_SPACE
    elif first_char == '[':
        return T_LBRACKET
    elif first_char == ']':
        return T_RBRACKET
    elif first_char == '(':
        return T_LPAREN
    elif first_char == ')':
        return T_RPAREN
    elif first_char == '{':
        return T_LBRACE
    elif first_char == '}':
        return T_RBRACE
    elif first_char == '.':
        return T_DOT
    elif first_char == ',':
        return T_COMMA
    elif first_char == ':':
        return T_COLON
    elif first_char == '=' and start_chars[1] != '=':
        return T_EQUAL
    elif first_char == "'" or first_char == '"':
        return T_STRING
    fo=ord(first_char)
    if fo >= 48 and fo <=57:
        return T_NUMBER
    l = len(start_chars)
    if ( l >= 2):
        twochars = start_chars[:2]
        if first_char in "-+*/<>%" or twochars in ['==','!=','<=','>=']:
            return T_OPERATOR
        if l>=3:
            o=ord(start_chars[2])
            if (twochars == 'or' or twochars == 'is') and (o > 122 or o < 65 or o == 91):
                return T_OPERATOR
            elif (twochars == 'in' or twochars == 'if') and (o > 122 or o < 65 or o == 91):
                return T_KEYWORD
            if (l >= 4):
                o=ord(start_chars[3])
                threechars = start_chars[:3]
                if (threechars == 'and' or threechars == 'not') and (o > 122 or o < 65 or o == 91):
                    return T_OPERATOR
                elif (threechars == 'for') and (o > 122 or o < 65 or o == 91):
                    return T_KEYWORD
    if (fo >= 65 and fo <=90) or (fo>=97 and fo<=122) or first_char == '_' or first_char == '$':
        return T_IDENTIFIER
    else:
        return T_UNKNOWN

    # Turns out that the following was too slow in javascript
    # due to using regular expressions
    #
    # for tp,pat in match_token_res:
    #    if pat.match(start_chars):
    #            return tp

def parse_number(expr,pos):
    """ Parses a number """
    if expr[pos] == '-':
        negative=True
        pos = pos + 1
    else:
        negative = False
    ret = int(expr[pos])
    pos = pos + 1
    decimal_part = True
    div = 10
    while pos < len(expr) and ((expr[pos] in ['0','1','2','3','4','5','6','7','8','9']) or ( decimal_part and expr[pos]=='.' )):
        if expr[pos] == '.':
            decimal_part = False
        else:
            if decimal_part:
                ret *= 10
                ret += int(expr[pos])
            else:
                ret += int(expr[pos])/div
                div = div*10
        pos = pos + 1
    if negative:
        return -ret,pos
    else:
        return ret,pos

def parse_string(expr,pos):
    """ Parses a string, properly interpretting backslashes. """
    end_quote=expr[pos]
    backslash=False
    ret = ""
    pos = pos + 1
    while pos < len(expr) and (backslash or expr[pos] != end_quote):
        if not backslash:
            if expr[pos] == '\\':
                backslash = True
            else:
                ret += expr[pos]
        else:
            if expr[pos] == '\\':
                ret += '\\'
            elif expr[pos] == '"':
                ret += '"'
            elif expr[pos] == "'":
                ret += "'"
            elif expr[pos] == "n":
                ret += "\n"
            elif expr[pos] == "r":
                ret += "\r"
            elif expr[pos] == "t":
                ret += "\t"
            backslash = False
        pos = pos + 1
    if pos >= len(expr):
        raise Exception("String is missing end quote: "+end_quote)
    return ret, pos+1

#IDENTIFIER_INNERCHAR_RE = re.compile('[a-z_$0-9]',re.IGNORECASE)
def parse_identifier(expr,pos):
    """ Parses an identifier. """
    ret = expr[pos]
    pos = pos + 1
    # while pos < len(expr) and IDENTIFIER_INNERCHAR_RE.match(expr[pos]):
    while pos < len(expr):
        o = ord(expr[pos])
        if not ((o >=48 and o <=57) or (o>=65 and o <=90) or (o>=97 and o <=122) or o==36 or o == 95):
            break
        ret += expr[pos]
        pos = pos + 1
    return ret, pos

def tokenize(expr):
    """ A generator which takes a string and converts it to a
        stream of tokens, yielding the triples (token, its value, next position in the string)
        one by one.  """
    pos = 0
    while pos < len(expr):
        tokentype = token_type(expr[pos:pos+4])
        if tokentype == T_SPACE:
            pos = pos + 1
            pass
        elif tokentype == T_NUMBER:
            number,pos = parse_number(expr,pos)
            yield (T_NUMBER,number,pos)
        elif tokentype == T_STRING:
            string,pos = parse_string(expr,pos)
            yield (T_STRING,string,pos)
        elif tokentype == T_IDENTIFIER:
            identifier,pos = parse_identifier(expr,pos)
            yield (T_IDENTIFIER, identifier, pos)
        elif tokentype == T_OPERATOR:
            if expr[pos] == '*' and pos+1 < len(expr) and expr[pos+1] == '*':
                yield (T_OPERATOR,'**',pos+2)
                pos = pos + 2
            elif expr[pos] == '/' and pos+1 < len(expr) and expr[pos+1] == '/':
                yield (T_OPERATOR,'//',pos+2)
                pos = pos + 2
            elif expr[pos] == '=' and pos+1 < len(expr) and expr[pos+1] == '=':
                yield (T_OPERATOR,'==',pos+2)
                pos = pos + 2
            elif expr[pos] == '<' and pos+1 < len(expr) and expr[pos+1] == '=':
                yield (T_OPERATOR,'<=',pos+2)
                pos = pos + 2
            elif expr[pos] == '>' and pos+1 < len(expr) and expr[pos+1] == '=':
                yield (T_OPERATOR,'>=',pos+2)
                pos = pos + 2
            elif expr[pos] == '!':
                yield (T_OPERATOR,'!=',pos+2)
                pos = pos + 2
            elif expr[pos] == 'o':
                yield (T_OPERATOR,'or',pos+2)
                pos = pos + 2
            elif expr[pos] == 'i' and expr[pos+1]=='s':
                p=pos+2
                l=len(expr)
                while p<l and expr[p] == ' ' or expr[p] == '\t' or expr[p] == '\n':
                    p+=1
                if expr[p:p+3] == 'not':
                    if p+3 > l:
                        yield (T_OPERATOR,'is not',p+3)
                        pos = p+3
                    else:
                        o = ord(expr[p+3])
                        if ((o < 48 or o >57) and (o<65 or o >90) and (o<97 or o >122)):
                            yield (T_OPERATOR,'is not',p+3)
                            pos = p+3
                        else:
                            yield (T_OPERATOR,'is',pos+2)
                            pos = pos + 2
                else:
                    yield (T_OPERATOR,'is',pos+2)
                    pos = pos + 2
            elif expr[pos] == 'a':
                yield (T_OPERATOR,'and',pos+3)
                pos = pos + 3
            elif expr[pos] == 'n':
                yield (T_OPERATOR,'not',pos+3)
                pos = pos + 3
            else:
                yield (T_OPERATOR,expr[pos],pos+1)
                pos = pos + 1
        elif tokentype == T_KEYWORD:
            # KEYWORD_RE = re.compile('(for)[^a-z_$].*|(if)[^a-z_$].*|(in)[^a-z_$].*')
            # Regular expressions are too slow and here they are overkill
            #
            # match = KEYWORD_RE.match(expr[pos:pos+4])
            # kwd = match.groups()[0] or match.groups()[1] or match.groups()[2]
            # yield (tokentype,kwd,pos+len(kwd))
            # pos = pos + len(kwd)
            if expr[pos] == 'f':
                yield (tokentype,'for',pos+3)
                pos += 3
            elif expr[pos+1] == 'f':
                yield (tokentype,'if',pos+2)
                pos += 2
            else:
                yield (tokentype,'in',pos+2)
                pos += 2

        else:
            yield (tokentype,expr[pos],pos+1)
            pos = pos+1


class ExpNode(EventMixin):
    """ Base class for nodes in the AST tree """

    def __init__(self):
        super().__init__()
        self._dirty = True
        self._cached_val = None

    def evaluate(self,context,use_cache=False):
        """
            Evaluates the node looking up identifiers in @context.

            Note: If the expression watches a context, you can
            pass the parameter `use_cache=True` which returns
            a cached value if there were no changes to the context
            affecting the expression.
        """
        if not self._dirty and use_cache:
            return self._cached_val
        self._dirty = False
        return None

    def evaluate_assignment(self,context,value):
        """
            Computes the expression and assigns value to the result.
            E.g. if the expression is `ob[1]` and `ctx` is
            `{ob:[1,2,3,4]}` then `evaluate_assignment(ctx,20)`
            executes `ctx.ob[1]=20`.

            Note: The methods in general assume that the assignment
            succeeds, i.e. that a next call to evaluate should return
            value. In particular, the evaluate_assignment caches the
            value `value` without actually computing the value of the
            expression.
        """
        raise Exception("Assigning to "+str(self)+" not supported")

    def watch(self,ctx):
        """
            Watches ctx for changes which have effect on the expression value
            and emits the 'change' event when the expression changes.

            Note: any changes to an expression which does not have a cached
            value (which are dirty) will not fire a change event. In particular,
            after parsing an expression, one must first evaluate it, before
            it will fire any change events.
        """
        pass

    def clone(self):
        """
            Returns a clone of this node which can watch a diffrent context.
        """
        return ExpNode()

    def is_function_call(self):
        """
            Returns true if the expression is a function call.
        """
        return isinstance(self,OpNode) and self._opstr == '()'

    def is_assignable(self):
        """
            Returns true if the expression can be assigned to
            using :func:`evaluate_assignment`.
        """
        ret = isinstance(self,IdentNode) and not self._const
        ret = ret or isinstance(self,AttrAccessNode)
        ret = ret or isinstance(self,OpNode) and self._opstr == '[]' and isinstance(self._rarg,ListSliceNode) and not self._rarg._slice
        return ret

    def _change_handler(self,event):
        if self._dirty:
            return
        self.emit('change',{})

    def __repr__(self):
        return "<AST Node>"

class ConstNode(ExpNode):
    """ Node representing a string or number constant """
    def __init__(self,val):
        super().__init__()
        self._dirty = False
        self._cached_val = val

    def name(self):
        return self._cached_val

    def evaluate(self,context,use_cache=False):
        return self._cached_val

    def evaluate_assignment(self, context, value):
        raise Exception("Cannot assign value to constants" )
    
    def clone(self):
        # Const Nodes can't change, so clone's can be identical
        return self

    def __repr__(self):
        return repr(self._last_val)


class IdentNode(ExpNode):
    """ Node representing an identifier or one of the predefined constants True, False, None, str, int, len.
        (we don't allow overriding str, int and len)
    """
    CONSTANTS = {
        'True':True,
        'False':False,
        'None':None,
        'str':str,
        'int':int,
        'len':len
    }
    BUILTINS = {
        'str':str,
        'int':int,
        'len':len
    }
    def __init__(self,identifier):
        super().__init__()
        self._ident = identifier
        if self._ident in self.CONSTANTS:
            self._const = True
            self._cached_val= self.CONSTANTS[self._ident]
        else:
            self._const = False

    def name(self):
        return self._ident

    def clone(self):
        if self._const:
            return self
        else:
            return IdentNode(self._ident)

    def watch(self, context):
        if not self._const:
            self._watched_ctx = context
            self._ctx_observer = observe(context)
            self._ctx_observer.bind('change',self._context_change)
            try:
                self._value_observer = observe(self.evaluate(context),ignore_errors=True)
                self._value_observer.bind('change',self._value_change)
            except:
                self._value_observer = None

    def evaluate(self,context,use_cache=False):
        if (not self._dirty and use_cache) or self._const:
            return self._cached_val
        try:
            self._cached_val = context._get(self._ident)
        except KeyError:
            self._cached_val = self.BUILTINS[self._ident]
        self._dirty = False
        return self._cached_val

    def evaluate_assignment(self, context, value):
        if self._const:
            raise Exception("Cannot assign to the constant"+self._cached_val)
        else:
            setattr(context,self._ident,value)

    def _context_change(self,event):
        if self._dirty:
            return
        if event.data['key'] == self._ident:
            if self._value_observer:
                self._value_observer.unbind()
            if 'value' in event.data['key']:
                self._cached_val = event.data['value']
                self._value_observer=observe(event.data['value'],ignore_errors=True)
                self.emit('change',{'value':self._cached_val})
            else:
                self._dirty = True
                self.emit('change',{})

    def _value_change(self,event):
        if self._dirty:
            return
        if 'value' in event.data:
            self._cached_val = event.data['value']
            self.emit('change',{'value':self._cached_val})
        else:
            self._dirty = True
            self.emit('change',{})

    def __repr__(self):
        return self.name()


class MultiChildNode(ExpNode):
    def __init__(self, children):
        super().__init__()
        self._children = children
        self._cached_vals = []
        self._dirty_children = True
        for ch_index in range(len(self._children)):
            ch = self._children[ch_index]
            if ch is not None:
                ch.bind('change',lambda ev:self._child_changed(ev, ch_index))

    def clone(self):
        """
            Since MultiChildNode is an abstract node which is never instantiated,
            the clone method doesn't return the MultiChildNode but a list of cloned
            children so that it can be used by subclasses.
        """
        clones=[]
        for ch in self._children:
            if ch is not None:
                clones.append(ch.clone())
            else:
                clones.append(None)
        return clones

    def evaluate(self, context,use_cache=False):
        if not self._dirty_children and use_cache:
            return self._cached_vals
        self._cached_vals = []
        for ch in self._children:
            if ch is not None:
                self._last_val.append(ch.evaluate(context,use_cache=use_cache))
            else:
                self._last_val.append(None)
        return self._last_val

    def watch(self,context):
        for ch in self._children:
            if ch is not None:
                ch.watch(context)

    def _child_changed(self,event,child_index):
        if self._dirty_children:
            return
        if 'value' in event.data:
            self._cached_vals[child_index] = event.data['value']
        else:
            self._dirty_children = True
        if not self._dirty:
            self._dirty = True
            self.emit('change')


class FuncArgsNode(MultiChildNode):
    def __init__(self, args, kwargs):
        super().__init__(args)
        self._kwargs = kwargs
        self._cached_kwargs = {}
        self._dirty_kwargs = False
        for (k,v) in self._kwargs.items():
            v.bind('change',lambda ev:self._kwarg_change(self,k))

    def clone(self):
        cloned_args = super().clone()
        cloned_kwargs = {}
        for (k,v) in self._kwargs.items():
            cloned_kwargs[k] = v.clone()
        return FuncArgsNode(cloned_args,cloned_kwargs)

    def evaluate(self,context,use_cache=False):
        args = super().evaluate(context,use_cache=use_cache)
        if not self._dirty_kwargs and use_cache:
            kwargs = self._kwargs
        else:
            for (k,v) in self._kwargs.items():
                kwargs[k] = v.evaluate(context)
        self._cached_val = args,kwargs
        return self._cached_val

    def watch(self, context):
        super().watch(context)
        for (k,v) in self._kwargs.items():
            v.watch(context)

    def _kwarg_change(self, ev, k):
        if self._dirty_kwargs:
            return
        if 'value' in ev.data:
            self._cached_kwargs[k] = ev.data['value']
        else:
            self._dirty_kwargs = True
        if not self._dirty:
            self._dirty = True
            self.emit('change')

    def __repr__(self):
        return ','.join([repr(ch) for ch in self._children]+[k+'='+repr(v) for (k,v) in self._kwargs])


class ListSliceNode(MultiChildNode):
    def __init__(self,slice,start,end,step):
        super().__init__([start,end,step])
        self._slice = slice

    def clone(self):
        start_c,end_c,step_c = super().clone()
        return ListSliceNode(self._slice,start_c,end_c,step_c)

    def evaluate(self, context,use_cache=False):
        start,end,step = super().evaluate(context,use_cache=use_cache)
        if self._slice:
            return slice(start,end,step)
        else:
            return start

    def __repr__(self):
        start,end,step=self._children
        if self._slice:
            ret = ''
            if start is None:
                ret = ':'
            else:
                ret = repr(start)+':'
            if end is not None:
                ret += repr(end)
            if step is not None:
                ret += ':'+repr(step)
            return ret
        else:
            return repr(start)


class AttrAccessNode(ExpNode):
    """ Node representing attribute access, e.g. obj.prop """
    def __init__(self, obj, attribute):
        super().__init__()
        self._obj = obj
        self._attr = attribute
        self._observer = None
        self._obj.bind('change',self._change_handler)

    def clone(self):
        return AttrAccessNode(self._obj.clone(),self._attr.clone())

    def evaluate(self,context,use_cache=False):
        """
           Note that this function expects the AST of the attr access to
           be rooted at the rightmost element of the attr access chain !!
        """
        if self._dirty or not use_cache:
            if self._observer:
                self._observer.unbind()
            obj_val = self._obj.evaluate(context)
            self._cached_val = getattr(self._obj_val,self._attr.name())
            self._observer = observe(self._cached_val,self._change_attr_handler,ignore_errors=True)
        return self._cached_val

    def evaluate_assignment(self, context, value):
        obj_val = self._obj.evaluate(context)
        setattr(obj_val,self._attr.name(),value)
        if self._observer:
            self._observer.unbind()
        self._observer = observe(self._cached_val,self._change_attr_handler,ignore_errors=True)
        self._cached_val = value

    def watch(self,context):
        if self._observer is not None:
            self._observer.unbind()
        self._obj.watch(context)

    def _change_attr_handler(self,event):
        """
            Handles changes to the value of the attribute.
        """
        if self._dirty:
            return
        if 'value' in event.data:
            self._cached_val = event['value']
            self.emit('change',{'value':self._cached_val})
        else:
            self._dirty = True
            self.emit('change',{})

    def __repr__(self):
        return repr(self._obj)+'.'+repr(self._attr)


class ListComprNode(ExpNode):
    """ Node representing comprehension, e.g. [ x+10 for x in lst if x//2 == 0 ] """
    def __init__(self,expr, var, lst, cond):
        super().__init__()
        self._expr = expr
        self._var = var
        self._lst = lst
        self._cond = cond
        self._expr.bind('exp_change',self,'exp_change')
        self._lst.bind('exp_change',self,'exp_change')
        if self._cond is not None:
            self._cond.bind('exp_change',self,'exp_change')

    def clone(self):
        expr_c = self._expr.clone()
        var_c = self._var.clone()
        lst_c = self._lst.clone()
        if self._cond is None:
            cond_c = None
        else:
            cond_c = self._cond.clone()
        return ListComprNode(expr_c,var_c,lst_c,cond_c)

    def evaluate(self,context):
        lst = self._lst.evaluate(context)
        ret = []
        var_name = self._var.name()
        context._save(var_name)
        for elem in lst:
            context._set(var_name,elem)
            if self._cond is None or self._cond.evaluate(context):
                ret.append(self._expr.evaluate(context))

        context._restore(var_name)
        self._last_val = ret
        return self._last_val

    def evaluate_assignment(self):
        raise Exception("Assigning to a list comprehension does not make sense.")

    def watch(self,context):
        self._lst.watch(context)
        self._cond.watch(context)
        self._expr.watch(context)

    def __repr__(self):
        if self._cond is None:
            return '['+repr(self._expr)+' for '+repr(self._var)+' in ' + repr(self._lst) + ']'
        else:
            return '['+repr(self._expr)+' for '+repr(self._var)+' in ' + repr(self._lst) + ' if '+repr(self._cond)+']'


class ListNode(MultiChildNode):
    """ Node representing a list constant, e.g. [1,2,"ahoj",3,None] """
    def __init__(self,lst):
        super().__init__(lst)

    def clone(self):
        return ListNode(super().clone())

    def evaluate_assignment(self, context, value):
        raise Exception("Assigning to a list constant has no effect!")

    def __repr__(self):
        return repr(self._children)


class OpNode(ExpNode):
    """ Node representing an operation, e.g. a is None, a**5, a[10], a.b or func(x,y)"""
    UNARY= ['-unary','not']
    OPS = {
        '+':lambda x,y:x+y,
        '-':lambda x,y:x-y,
        '-unary': lambda y:-y,
        '*':lambda x,y:x*y,
        '/':lambda x,y:x/y,
        '//':lambda x,y:x//y,
        '%':lambda x,y:x%y,
        '**':lambda x,y:x**y,
        '==':lambda x,y:x==y,
        '!=':lambda x,y:x!=y,
        '<':lambda x,y:x<y,
        '>':lambda x,y:x>y,
        '<=':lambda x,y:x<=y,
        '>=':lambda x,y:x>=y,
        'and':lambda x,y:x and y,
        'or':lambda x,y:x or y,
        'not':lambda y:not y,
        'is':lambda x,y:x is y,
        'in':lambda x,y:x in y,
        'is not':lambda x,y: x is not y,
        '[]':lambda x,y: x[y],
        '()':lambda func,args:func(*args[0],**args[1])
    }

    def __init__(self,operator,l_exp,r_exp):
        super().__init__()
        self._opstr = operator
        self._op = OpNode.OPS[operator]
        self._larg = l_exp
        self._rarg = r_exp
        if l_exp is not None: # The unary operator 'not' does not have a left argument
            l_exp.bind('exp_change',self,'exp_change')
        r_exp.bind('exp_change',self,'exp_change')
        self.bind('exp_change',self._change_handler)

    def clone(self):
        if self._larg is None:
            l_exp = None
        else:
            l_exp = self._larg.clone()
        r_exp = self._rarg.clone()
        return OpNode(self._opstr,l_exp,r_exp)

    def evaluate(self,context):
        if self._opstr in self.UNARY:
            self._last_val = self._op(self._rarg.evaluate(context))
        else:
            l = self._larg.evaluate(context)
            r = self._rarg.evaluate(context)
            self._last_val = self._op(l,r)
        return self._last_val

    def evaluate_assignment(self, context, value):
        if self._opstr != '[]':
            raise Exception("Assigning to "+repr(self)+" does not make sense.")
        lst = self._larg.evaluate(context)
        index = self._rarg.evaluate(context)
        lst[index] = value

    def watch(self,context):
        self.stop_forwarding(only_event='change')
        self._watched_ctx = context
        if self._opstr not in self.UNARY:
            self._larg.watch(context)
            if self._opstr in ['[]','()']:
                try:
                    self.evaluate(context)
                    observe(self._last_val,observer=self)
                except:
                    pass
        self._rarg.watch(context)

    def _observe_val(self,context):
        try:
            self.evaluate(context)
            observe(self._last_val,observer=self)
            self._observing_val = self._last_val
        except:
            pass

    def _change_handler(self,event):
        if event.name == 'exp_change':
            self.stop_forwarding(only_event='change')
            self._observe_val(self._watched_ctx)
        else:
            self.emit('exp_change',{'source_id':event.eventid,'change':event.data})



    def __repr__(self):
        if self._opstr == '-unary':
            return '-'+repr(self._rarg)
        elif self._opstr == 'not':
            return '(not '+repr(self._rarg)+')'
        elif self._opstr == '[]':
            return repr(self._larg)+'['+repr(self._rarg)+']'
        elif self._opstr == '()':
            return repr(self._larg)+'('+repr(self._rarg)+')'
        elif self._opstr == '**':
            return repr(self._larg)+'**'+repr(self._rarg)
        else:
            if isinstance(self._larg,OpNode) and OP_PRIORITY[self._larg._opstr] < OP_PRIORITY[self._opstr]:
                    l_repr = '('+repr(self._larg)+')'
            else:
                l_repr = repr(self._larg)

            if isinstance(self._rarg,OpNode) and OP_PRIORITY[self._rarg._opstr] <= OP_PRIORITY[self._opstr]:
                    r_repr = '('+repr(self._rarg)+')'
            else:
                r_repr = repr(self._rarg)

            return l_repr+' '+self._opstr+' '+r_repr


def partial_eval(arg_stack,op_stack,pri=-1):
    """ Partially evaluates the stack, i.e. while the operators in @op_stack have strictly
        higher priority then @pri, they are converted to OpNodes/AttrAccessNodes with
        arguments taken from the @arg_stack. The result is always placed back on the @arg_stack"""
    while len(op_stack) > 0 and pri <= OP_PRIORITY[op_stack[-1][1]]:
        token,op = op_stack.pop()
        try:
            ar = arg_stack.pop()
            if op in OpNode.UNARY:
                al = None
            else:
                al=arg_stack.pop()
            if op == '.':
                arg_stack.append(AttrAccessNode(al,ar))
            else:
                arg_stack.append(OpNode(op,al,ar))
        except IndexError:
            raise Exception("Not enough arguments for operator '"+op+"'")

def parse_args(token_stream):
    """ Parses function arguments from the stream and returns them as a pair (args,kwargs)
        where the first is a list and the second a dict """
    args = []
    kwargs = {}
    state = 'args'
    while state == 'args':
        arg, endt, pos = _parse(token_stream,[T_COMMA,T_EQUAL,T_RPAREN])
        if endt == T_EQUAL:
            state = 'kwargs'
        elif endt == T_RPAREN:
            args.append(arg)
            return args, kwargs
        else:
            args.append(arg)
    val, endt, pos = _parse(token_stream,[T_COMMA,T_RPAREN])
    kwargs[arg._ident]=val
    while endt != T_RPAREN:
        arg,endt,pos = _parse(token_stream,[T_EQUAL])
        val,endt,pos = _parse(token_stream,[T_COMMA,T_RPAREN])
        kwargs[arg._ident] = val
    return args, kwargs

def parse_lst(token_stream):
    """ Parses a list constant or list comprehension from the token_stream
        and returns the appropriate node """
    elem, endt, pos = _parse(token_stream,[T_RBRACKET,T_COMMA,T_KEYWORD])
    if endt == T_KEYWORD:
        expr = elem
        var, endt, pos = _parse(token_stream,[T_KEYWORD])
        lst, endt, pos = _parse(token_stream,[T_KEYWORD,T_RBRACKET])
        if endt == T_KEYWORD:
            cond, endt, pos = _parse(token_stream,[T_RBRACKET])
        else:
            cond = None
        return ListComprNode(expr,var,lst,cond)
    else:
        lst = [elem]
        while endt != T_RBRACKET:
            elem, endt, pos = _parse(token_stream,[T_RBRACKET,T_COMMA, T_KEYWORD])
            lst.append(elem)
        return ListNode(lst)

def parse_slice(token_stream):
    """ Parses a slice (e.g. a:b:c) or index from the token_stream and returns the slice as a quadruple,
        the first element of which indicates whether it is a slice (True) or an index (False)
    """
    index_s, endt, pos = _parse(token_stream,[T_COLON,T_RBRACKET])
    if endt == T_COLON:
        slice = True
        index_e, endt, pos = _parse(token_stream,[T_RBRACKET,T_COLON])
        if endt == T_COLON:
            step, endt, pos = _parse(token_stream,[T_RBRACKET])
        else:
            step = None
    else:
        slice = False
        index_e = None
        step = None
    return slice, index_s, index_e, step



def parse_interpolated_str(tpl_expr):
    """ Parses a string of the form

          Test text {{ exp }} other text {{ exp2 }} final text.

        where `exp` and `exp2` are expressions and returns a list of asts
        representing the expressions:

          ["Test text ",str(exp)," other text ",str(exp2)," final text."]
    """
    last_pos=0
    abs_pos=tpl_expr.find("{{",0)
    token_stream = tokenize(tpl_expr[abs_pos+2:])
    ret = []
    while abs_pos > -1:
        ret.append(ConstNode(tpl_expr[last_pos:abs_pos]))               # Get string from last }} to current {{
        abs_pos += 2                                                    # Skip '{{'
        token_stream = tokenize(tpl_expr[abs_pos:])                     # Tokenize string from {{ to the ending }}
        ast,etok,rel_pos = _parse(token_stream,end_tokens=[T_RBRACE])
        abs_pos += rel_pos                                              # Move to the second ending brace of the expression
        if not tpl_expr[abs_pos] == "}":
            raise Exception("Invalid interpolated string, expecting '}' at "+str(abs_pos)+" got '"+str(tpl_expr[abs_pos])+"' instead.")
        else:
            abs_pos += 1                                                # Skip the ending '}'
        ret.append(OpNode("()",IdentNode("str"),FuncArgsNode([ast],{}))) # Wrap the expression in a str call and add it to the list
        last_pos = abs_pos
        abs_pos = tpl_expr.find("{{",last_pos)
    if len(tpl_expr) > last_pos:
        ret.append(ConstNode(tpl_expr[last_pos:]))
    return ret


_parse_cache = {}

def parse(expr,trailing_garbage_ok=False,use_cache=True):
    if (expr,trailing_garbage_ok) in _parse_cache and use_cache:
        if trailing_garbage_ok:
            ast,pos = _parse_cache[(expr,trailing_garbage_ok)]
            return ast.clone(), pos
        else:
            ast = _parse_cache[(expr,trailing_garbage_ok)]
            return ast.clone()
    token_stream = tokenize(expr)
    ast,etok,pos = _parse(token_stream,trailing_garbage_ok=trailing_garbage_ok)
    if trailing_garbage_ok:
        if use_cache:
            _parse_cache[(expr,True)]=ast,pos
        return ast,pos
    else:
        if use_cache:
            _parse_cache[(expr,False)]=ast
        return ast

def _parse(token_stream,end_tokens=[],trailing_garbage_ok=False):
    """
        Parses the token_stream, optionally stopping when an
        unconsumed token from end_tokens is found. Returns
        the parsed tree (or None if the token_stream is empty),
        the last token seen and the position corresponding to
        the next position in the source string
    """
    arg_stack = []
    op_stack = []
    prev_token = None
    prev_token_set = False
    for (token,val,pos) in token_stream:
        if token in end_tokens: # The token is unconsumed and in the stoplist, so we evaluate what we can and stop parsing
            partial_eval(arg_stack,op_stack)
            if len(arg_stack) == 0:
                return None, token, pos
            else:
                return arg_stack[0], token, pos
        elif token == T_IDENTIFIER:
            arg_stack.append(IdentNode(val))
        elif token in [T_NUMBER, T_STRING]:
            arg_stack.append(ConstNode(val))
        elif token == T_OPERATOR or token == T_DOT or (token == T_KEYWORD and val == 'in'):
            # NOTE: '.' and 'in' are, in this context, operators.
            # If the operator has lower priority than operators on the @op_stack
            # we need to evaluate all pending operations with higher priority
            if val == '-' and (prev_token == T_OPERATOR or prev_token is None or prev_token == T_LBRACKET_LIST or prev_token == T_LPAREN_EXPR):
                val = '-unary'
            pri = OP_PRIORITY[val]
            partial_eval(arg_stack,op_stack,pri)
            op_stack.append((token,val))
        elif token == T_LBRACKET:
            # '[' can either start a list constant/comprehension, e.g. [1,2,3] or list slice, e.g. ahoj[1:10];
            # We destinguish between the two cases by noticing that first case must either
            # be at the start of the expression or be directly preceded by an operator
            if prev_token == T_OPERATOR or prev_token is None or (token == T_KEYWORD and val == 'in') or prev_token == T_LBRACKET_LIST or prev_token == T_LPAREN_EXPR or prev_token== T_LPAREN_FUNCTION:
                arg_stack.append(parse_lst(token_stream))
                prev_token = T_LBRACKET_LIST
            else:
                slice, index_s, index_e, step = parse_slice(token_stream)
                pri = OP_PRIORITY['[]']
                partial_eval(arg_stack,op_stack,pri)
                arg_stack.append(ListSliceNode(slice,index_s,index_e,step))
                op_stack.append((T_OPERATOR,'[]'))
                prev_token = T_LBRACKET_INDEX
            prev_token_set = True
        elif token == T_LPAREN:
            # A '(' can either start a parenthesized expression or a function call.
            # We destinguish between the two cases by noticing that first case must either
            # be at the start of the expression or be directly preceded by an operator
            # TODO: Implement Tuples
            if prev_token == T_OPERATOR or prev_token is None or (token == T_KEYWORD and val == 'in') or prev_token == T_LBRACKET_LIST or prev_token == T_LBRACKET_INDEX or prev_token == T_LPAREN_EXPR or prev_token == T_LPAREN_FUNCTION:
                op_stack.append((T_LPAREN_EXPR,val))
                prev_token = T_LPAREN_EXPR
            else:
                prev_token = T_LPAREN_FUNCTION
                args, kwargs = parse_args(token_stream)
                pri = OP_PRIORITY['()']
                partial_eval(arg_stack,op_stack,pri)
                arg_stack.append(FuncArgsNode(args,kwargs))
                op_stack.append((T_OPERATOR,'()'))
            prev_token_set = True
        elif token == T_RPAREN:
            partial_eval(arg_stack,op_stack)
            if op_stack[-1][0] != T_LPAREN_EXPR:
                raise Exception("Expecting '(' at "+str(pos))
            op_stack.pop()
        else:
            if trailing_garbage_ok:
                partial_eval(arg_stack,op_stack)
                if len(arg_stack) > 2 or len(op_stack) > 0:
                    raise Exception("Invalid expression, leftovers: args:"+str(arg_stack)+"ops:"+str(op_stack))
                return arg_stack[0],None,pos
            else:
                raise Exception("Unexpected token "+str((token,val))+" at "+str(pos))
        if not prev_token_set:
            prev_token = token
        else:
            prev_token_set = False
    partial_eval(arg_stack,op_stack)
    if len(arg_stack) > 2 or len(op_stack) > 0:
        raise Exception("Invalid expression, leftovers: args:"+str(arg_stack)+"ops:"+str(op_stack))
    return arg_stack[0],None,pos
