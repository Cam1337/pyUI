#screen = x,y area of screen that has methods attached to it
#area   = x,y,n n screens within a certain area

import curses, time



class ScreenDelimiter(object):
    """
    Parent class for all delimiter objects that will be used.
    """
    def __init__(self, delim="-"):
        self.delim = delim

    def populate(self):
        """
        Easily populate the entire delimiter with data to act as a line split (think <hr> in HTML)
        """
        self.set(self.delim * (self.width))

class ScreenBar(object):
    """
    Parent class for all status bar objects that only contain one line and one value at any given time.
    """
    def set(self, data):
        """
        Set the value of the bar and display it immediately
        @data -> string -> value to replace the current value with. Will be sanitized into a string in this method.
        """
        self.value = data
        self.window.erase()
        self.window.addstr(str(data)[:self.width - 1])
        self.window.refresh()

    def deleteChar(self, optn = 1):
        """
        Simple method to remove a single character (for [DELETE] key)
        @optn -> int -> OPTIONAL, number of characters to delete

        [BUG] Currently the delete character (ord 127) prints 2 extra characters, so I added optn to delete those + 1 more.
        """
        for i in range(optn):
            y, x = self.window.getyx()
            self.window.move(y, x-1)
            self.window.delch()

class ScreenItem(object):
    def __init__(self, name, child=False):
        self.children = [{},None][child]
        self.name   = name
        self.window = None

        self.base_window = None # main window

        self.x_width, self.y_height = None, None
        self.x_offset, self.y_offset = None, None

        self.newline_delim = 1 # add \n to each write or not

        self.data_buffer = []

    def initialize(self, height, width, w_offset, h_offset, child=False, parent=None):
        self.x_width = width
        self.y_height = height

        self.x_offset = w_offset
        self.y_offset = h_offset


        if child and parent:
            self.window = parent.derwin(width, height, h_offset, 0)
        else:
            self.window = curses.newwin(self.y_height,self.x_width, self.y_offset, self.x_offset)

        self.window.leaveok(1)

    def add_child(self, obj, height, width, h_offset):
        obj.initialize(width, height, 0, h_offset, child=True, parent=self.window)
        self.children[obj.name] = obj

    def child(self, name):
        return self.children.get(name, None)

    def truncate(self, data, width):
        return [data[:width]]

    def slicen(self, l, n):
        if n<1:
            n=1
        return [l[i:i+n] for i in range(0, len(l), n)]

    def write(self, data):
        #if len(data) > self.y_height:
        #   data = data[-self.y_height:] # trim the entries we won't even see
        for i, i_data in enumerate(data):
            delim = "\n" if self.newline_delim else "" # don't \n if not set
            delim = delim if len(data)-1 == i else "" # don't \n any non-last items

            s_data = "{0}{1}".format(i_data, delim)
            self.window.addstr(s_data)

    def write_s(self, data, wrap=True): # write silently with no refresh
        if self.window == None: raise ValueError("Writing to uninitialized ScreenItem `{0}`",format(self.name))
        wrap = [self.truncate, self.slicen][wrap]
        data = wrap(data, self.x_width + self.newline_delim)
        self.write(data)

    def write_r(self, data, wrap=True): # write and refresh
        self.write_s(data, wrap)
        self.window.refresh()

    def delnlines(self, n):
        cy, cx = self.window.getyx()
        self.window.move(cy-n, 0)
        self.window.clrtobot()

class BaseScreen(object):
    def __init__(self, max_win=0):
        self.screens = {}
        self.lock    = 0

        self.main_window = None

    def init(self):
        self.main_window = curses.initscr()
        self.main_window.keypad(1)
        curses.noecho()

    def uninit(self):
        self.main_window.keypad(0)
        curses.echo()
        curses.endwin()

    def mainloop(self, n=0):
        if n:
            time.sleep(n)
            return
        self.lock = 1
        while True:
            pass

    def lock(self):
        self.lock = abs(self.lock - 1)
        return self.lock

    def get(self, name):
        return self.screens.get(name, None)

    def add(self, layers):
        if self.lock == 0:
            height_offset = 0
            for layer in layers:
                width_offset = 0
                for screen in layer:
                    self.screens[screen["object"].name] = screen["object"]
                    screen["object"].base_window = self.main_window
                    screen["object"].initialize(screen["height"], screen["width"], width_offset, height_offset)
                    if screen.has_key("children"):
                        c_offset = 0
                        for child in screen["children"]:
                            screen["object"].add_child(child["object"], child["height"], child["width"], c_offset)
                            child["object"].base_window = self.main_window
                            c_offset += child["height"]
                    width_offset += screen["width"]
                height_offset += screen["height"]


        return self.lock

layers = [
    [ # layer 1 heights must all be the same
        {
            "height":10,
            "width":20,
            "object":ScreenItem("screen_1")
        },
        {
            "height":10,
            "width":100,
            "object":ScreenItem("screen_2"),
            "children":[
                {
                    "height":5,
                    "width":100,
                    "object":ScreenItem("screen_2_1", child=True)
                },
                {
                    "height":5,
                    "width":10,
                    "object":ScreenItem("screen_2_2", child=True)
                }
            ]

        }
    ]
]

def main():

    bs = BaseScreen()
    bs.init()
    bs.add(layers)

    s = bs.get("screen_1")
    s.write_r("cameroncameroncameroncameroncameroncameroncameroncameroncameroncameroncameroncameron")
    time.sleep(1)
    s.delnlines(2)
    s.write_r("testing")
    s.window.refresh()
    bs.mainloop(1)
    bs.uninit()

main()