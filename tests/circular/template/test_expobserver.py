from src.circular.template.expobserver import ExpObserver
from src.circular.template.expression import ET_EXPRESSION, ET_INTERPOLATED_STRING
from src.circular.template.context import Context
from tests.utils import TObserver


class MockObject(object):
    def __init__(self,depth=0):
        if depth > 0:
            self.child = MockObject(depth-1)
        else:
            self.leaf = True


class TestExpObserver(object):

    def setup_method(self,method):
        self.ctx = Context()
        self.ctx._clear()

    def prepare(self,exp, et = ET_EXPRESSION):
        self.obs = ExpObserver(exp,expression_type=et)
        self.obs.watch(self.ctx)
        self.obs.evaluate()
        self.t = TObserver(self.obs)

    def exec_test(self,old,new):
        data = self.t.events.pop().data
        if old is not None:
            assert 'old' in data
            assert data['old'] == old
        else:
            assert 'old' not in data

        if new is not None:
            assert self.obs.have_value() == True
            assert self.obs.value == new
            assert 'new' in data
            assert data['new'] == new
        else:
            assert 'new' not in data
            assert self.obs.have_value() == False

    def test_clone(self):
        self.prepare("x**2 + x")
        clone = self.obs.clone()
        ctx = Context()
        clone.watch(ctx)
        clone.evaluate()
        ctx.x=0
        self.ctx.x=1
        assert clone.value == 0
        assert self.obs.value == 2

    def test_arithmetic_exp(self):
        self.ctx.a = 1
        self.ctx.b = -2
        self.ctx.c = 0.5

        self.prepare("a*x**2 + b*x + c*x")
        assert self.obs.have_value() == False

        self.ctx.d=10
        assert len(self.t.events) == 0

        self.ctx.x = 0
        self.exec_test(None,0)

        self.ctx.x = 1
        self.exec_test(0,-0.5)

    def test_comprehension(self):
        self.ctx.lst = [-4,-3,-2,-1,0,1,2,3,4]
        self.prepare("[p+1 for p in lst if p%2 == 0]")
        assert self.obs.have_value() == True

        self.ctx.lst.append(4)
        self.exec_test([-3,-1,1,3,5],[-3,-1,1,3,5,5])

        self.ctx.lst.remove(4)
        self.exec_test([-3,-1,1,3,5,5],[-3,-1,1,3,5])

        self.ctx.lst.clear()
        self.exec_test([-3,-1,1,3,5],[])


    def test_attr_acces(self):
        self.ctx.root = MockObject(depth=3)
        self.prepare("root.child.child.child.leaf and True")
        assert self.obs.value == True

        self.ctx.root.child.child.child.leaf = False
        self.exec_test(True,False)

        self.ctx.root.child = None
        self.exec_test(False,None)

    def test_func(self):
        self.ctx.func = lambda x,y:x+y
        self.prepare("func(a,b)")
        assert self.obs.have_value() == False

        self.ctx.a = 10
        assert self.obs.have_value() == False

        self.ctx.b = 20
        self.exec_test(None,30)

        self.ctx.b = 30
        self.exec_test(30,40)


        self.ctx.func = lambda x,y:x*y
        self.exec_test(40,300)

        del self.ctx.a
        self.exec_test(300,None)

    def test_array_index(self):
        self.ctx.lst = [[1,2,3],2,3,4,5]
        self.ctx.a = 0
        self.prepare("lst[0][a]")
        self.obs.have_value() == True
        assert self.obs.value == 1

        self.ctx.lst[1]=2
        self.exec_test(1,1)
        self.ctx.a=2
        self.exec_test(1,3)
        self.ctx.a=3
        self.exec_test(3,None)
        self.ctx.lst[0].append(4)
        self.exec_test(None,4)
        self.ctx.lst.pop()
        self.exec_test(4,4)

    def test_string_interp(self):
        self.ctx.name = "James"
        self.prepare("My name is {{ surname }}, {{name}} {{ surname}}.",et=ET_INTERPOLATED_STRING)
        self.obs.have_value() == True
        assert self.obs.value == "My name is , James ."

        self.ctx.surname = "Bond"
        self.exec_test("My name is , James .","My name is Bond, James Bond.")









