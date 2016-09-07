import inspect
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jinja2 import Template

tpl = Template(open('tests/selenium/template.tpl', 'r').read())


class TObserver(object):
    def __init__(self, observer):
        self.events = []
        observer.bind('change', self.handler)

    def handler(self, event):
        self.events.append(event)


def wait_for_script(selenium):
    frame = inspect.stack()[1]
    mod = inspect.getmodule(frame[0])
    fname = frame[3]
    out_file = mod.__name__ + '-' + fname[5:]
    selenium.get('http://localhost:7000/tests/%s.html' % out_file)
    WebDriverWait(selenium, 2).until(
        EC.presence_of_element_located((By.ID, "finished"))
    )
    return selenium.find_element_by_id("test")


def selenium_setup_helper(func):
    mod = inspect.getmodule(func)
    script = getattr(mod, 'script_'+func.__name__[5:])
    out_file = mod.__name__+'-'+func.__name__[5:]
    script_src = "\n".join(inspect.getsource(script).split('\n')[1:])
    script_src = script_src.replace('    ', '')
    html = inspect.getdoc(script)
    test_dir = os.path.dirname(inspect.getfile(selenium_setup_helper))+'/selenium/webroot/tests'

    out = open('%s/%s.html' % (test_dir, out_file), 'w')
    out.write(tpl.render({
        'test': script_src,
        'title': out_file,
        'content': html
    }))
    out.close()
