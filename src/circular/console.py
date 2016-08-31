from browser import DOMNode, window
import sys
import traceback

from .utils.logger import Logger
logger = Logger(__name__)


class Console:
    _credits = """    Thanks to CWI, CNRI, BeOpen.com, Zope Corporation and a cast of thousands
    for supporting Python development.  See www.python.org for more information.
"""

    _copyright = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All Rights Reserved.

Copyright (c) 2001-2013 Python Software Foundation.
All Rights Reserved.

Copyright (c) 2000 BeOpen.com.
All Rights Reserved.

Copyright (c) 1995-2001 Corporation for National Research Initiatives.
All Rights Reserved.

Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam.
All Rights Reserved.
"""

    _license = """Copyright (c) 2012, Pierre Quentel pierre.quentel@gmail.com
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. Redistributions in binary
form must reproduce the above copyright notice, this list of conditions and
the following disclaimer in the documentation and/or other materials provided
with the distribution.
Neither the name of the <ORGANIZATION> nor the names of its contributors may
be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

    def __init__(self, elem):
        self._elem = elem

        self.credits.__repr__ = lambda: Console._credits
        self.copyright.__repr__ = lambda: Console._copyright
        self.license.__repr__ = lambda: Console._license

        self._redirected = False
        self._oldstdout = None
        self._oldstderr = None

        self.history = []
        self.current = 0
        self._status = "main"  # or "block" if typing inside a block

        # execution namespace
        self.editor_ns = {
            'credits': self.credits,
            'copyright': self.copyright,
            'license': self.license,
            '__name__': '__console__',
        }

        self._elem.bind('keypress', self.myKeyPress)
        self._elem.bind('keydown', self.myKeyDown)
        self._elem.bind('click', self.cursorToEnd)
        v = sys.implementation.version
        self._elem.value = "Brython %s.%s.%s on %s %s\n%s\n>>> " % (v[0],
                                                                    v[1],
                                                                    v[2],
                                                                    window.navigator.appName,
                                                                    window.navigator.appVersion,
                                                                    'Type "copyright()", "credits()" or "license()" for more information.')
        self._elem.focus()
        self.cursorToEnd()

    def add_to_ns(self, key, value):
        self.editor_ns[key] = value

    def _redirectOut(self):
        if self._redirected:
            sys.__console__ = False
            sys.stdout = self._oldstdout
            sys.stderr = self._oldstderr
            self._redirected = False
        else:
            sys.__console__ = True
            self._oldstdout = sys.stdout
            self._oldstderr = sys.stderr
            sys.stdout = self
            sys.stderr = self
            self._redirected = True

    def credits(self):
        self.write(self._credits)

    def copyright(self):
        self.write(self._copyright)

    def license(self):
        self.write(self._license)

    def write(self, data):
        self._elem.value += str(data)

    def cursorToEnd(self, *args):
        pos = len(self._elem.value)
        self._elem.setSelectionRange(pos, pos)
        self._elem.scrollTop = self._elem.scrollHeight

    def get_col(self, area):
        # returns the column num of cursor
        sel = self._elem.selectionStart
        lines = self._elem.value.split('\n')
        for line in lines[:-1]:
            sel -= len(line) + 1
        return sel

    def myKeyPress(self, event):
        if event.keyCode == 9:  # tab key
            event.preventDefault()
            self._elem.value += "    "
        elif event.keyCode == 13:  # return
            src = self._elem.value
            if self._status == "main":
                self.currentLine = src[src.rfind('>>>') + 4:]
            elif self._status == "3string":
                self.currentLine = src[src.rfind('>>>') + 4:]
                self.currentLine = self.currentLine.replace('\n... ', '\n')
            else:
                self.currentLine = src[src.rfind('...') + 4:]
            if self._status == 'main' and not self.currentLine.strip():
                self._elem.value += '\n>>> '
                event.preventDefault()
                return
            self._elem.value += '\n'
            self.history.append(self.currentLine)
            self.current = len(self.history)
            if self._status == "main" or self._status == "3string":
                try:
                    self._redirectOut()
                    _ = self.editor_ns['_'] = eval(self.currentLine, self.editor_ns)
                    if _ is not None:
                        self.write(repr(_) + '\n')
                    self._elem.value += '>>> '
                    self._status = "main"
                except IndentationError:
                    self._elem.value += '... '
                    self._status = "block"
                except SyntaxError as msg:
                    if str(msg) == 'invalid syntax : triple string end not found' or \
                            str(msg).startswith('Unbalanced bracket'):
                        self._elem.value += '... '
                        self._status = "3string"
                    elif str(msg) == 'eval() argument must be an expression':
                        try:
                            self._redirectOut()
                            exec(self.currentLine, self.editor_ns)
                        except:
                            traceback.print_exc(self)
                        finally:
                            self._redirectOut()
                        self._elem.value += '>>> '
                        self._status = "main"
                    elif str(msg) == 'decorator expects function':
                        self._elem.value += '... '
                        self._status = "block"
                    else:
                        traceback.print_exc(self)
                        self._elem.value += '>>> '
                        self._status = "main"
                except:
                    traceback.print_exc(self)
                    self._elem.value += '>>> '
                    self._status = "main"
                finally:
                    self._redirectOut()
            elif self.currentLine == "":  # end of block
                block = src[src.rfind('>>>') + 4:].splitlines()
                block = [block[0]] + [b[4:] for b in block[1:]]
                block_src = '\n'.join(block)
                # status must be set before executing code in globals()
                self._status = "main"
                try:
                    self._redirectOut()
                    _ = exec(block_src, self.editor_ns)
                    if _ is not None:
                        print(repr(_))
                except:
                    traceback.print_exc(self)
                finally:
                    self._redirectOut()
                self._elem.value += '>>> '
            else:
                self._elem.value += '... '
            self.cursorToEnd()
            event.preventDefault()

    def myKeyDown(self, event):
        if event.keyCode == 37:  # left arrow
            sel = self.get_col(self._elem)
            if sel < 5:
                event.preventDefault()
                event.stopPropagation()
        elif event.keyCode == 36:  # line start
            pos = self._elem.selectionStart
            col = self.get_col(self._elem)
            self._elem.setSelectionRange(pos - col + 4, pos - col + 4)
            event.preventDefault()
        elif event.keyCode == 38:  # up
            if self.current > 0:
                pos = self._elem.selectionStart
                col = self.get_col(self._elem)
                # remove self.current line
                self._elem.value = self._elem.value[:pos - col + 4]
                self.current -= 1
                self._elem.value += self.history[self.current]
            event.preventDefault()
        elif event.keyCode == 40:  # down
            if self.current < len(self.history) - 1:
                pos = self._elem.selectionStart
                col = self.get_col(self._elem)
                # remove self.current line
                self._elem.value = self._elem.value[:pos - col + 4]
                self.current += 1
                self._elem.value += self.history[self.current]
            event.preventDefault()
        elif event.keyCode == 8:  # backspace
            src = self._elem.value
            lstart = src.rfind('\n')
            if (lstart == -1 and len(src) < 5) or (len(src) - lstart < 6):
                event.preventDefault()
                event.stopPropagation()
