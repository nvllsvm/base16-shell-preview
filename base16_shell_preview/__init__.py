import curses
import os
import subprocess

CURRENT_THEME = os.readlink(os.path.expanduser('~/.base16_theme'))
BASE16_SCRIPTS_DIR = os.path.split(CURRENT_THEME)[0]

NUM_COLORS = 22


def get_themes(scripts_dir):
    return [Theme(os.path.join(scripts_dir, f))
            for f in sorted(os.listdir(scripts_dir))]


class Theme(object):
    def __init__(self, path):
        self.path = path
        filename = os.path.split(self.path)[1]
        self.name = filename.replace('base16-', '', 1)[:-3]

    def apply(self):
        subprocess.Popen(['sh', self.path])


class PreviewWindow(object):
    def __init__(self, lines, cols, *args, **kwargs):
        self.lines = lines
        self.cols = cols
        self.window = curses.newwin(lines, cols, *args, **kwargs)

    def render(self):
        for i in range(NUM_COLORS):
            curses.init_pair(i, i, -1)
            text = 'color{:02d} '.format(i)
            spaces = self.cols - len(text) - 1

            self.window.addstr(i, len(text), spaces*' ',
                               curses.color_pair(i) + curses.A_REVERSE)
            self.window.addstr(i, 0, text, curses.color_pair(i))

        self.window.refresh()


class ScrollListWindow(object):
    def __init__(self, lines, cols, *args, **kwargs):
        self.lines = lines
        self.cols = cols

        self.offset = 0
        self.selected = 0
        self.window = curses.newwin(lines, cols, **kwargs)
        self.data = []

    def set_data(self, data):
        self.data = data

    def up(self):
        if self.selected > 0:
            self.selected -= 1
        elif self.offset != 0:
            self.offset -= 1
        self.render()

    def down(self):
        if (self.offset + self.selected) > (len(self.data) - 2):
            pass
        elif self.selected == (self.lines - 1):
            self.offset += 1
        else:
            self.selected += 1
        self.render()

    def render(self):
        end = self.offset + self.lines

        line = 0
        for i, value in enumerate(self.data):
            if i < self.offset:
                continue
            elif i == end:
                break

            if line == self.selected:
                self.value = value
                attrs = curses.A_REVERSE
            else:
                attrs = 0

            self.window.addstr(line, 0, (self.cols - 1) * ' ', attrs)
            self.window.addstr(line, 0, value[:self.cols-1], attrs)
            line += 1

        self.window.refresh()


def main():
    stdscr = curses.initscr()
    stdscr.refresh()
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)
    curses.noecho()

    themes = {s.name: s for s in get_themes(BASE16_SCRIPTS_DIR)}

    scroll_list_cols = 35
    preview_cols = 42

    total_cols = scroll_list_cols + preview_cols

    scroll_list_win = ScrollListWindow(NUM_COLORS, scroll_list_cols)
    preview_win = PreviewWindow(NUM_COLORS, preview_cols, 0, scroll_list_cols)

    preview_win.render()

    scroll_list_win.set_data(sorted(themes.keys()))
    scroll_list_win.render()

    themes[scroll_list_win.value].apply()

    while True:
        scroll_list_win.render()
        preview_win.render()
        c = stdscr.getch()

        if c == curses.KEY_DOWN:
            scroll_list_win.down()
            themes[scroll_list_win.value].apply()
        elif c == curses.KEY_UP:
            scroll_list_win.up()
            themes[scroll_list_win.value].apply()
        elif c == ord('q'):
            end_run()
        elif c == curses.KEY_RESIZE:
            if curses.LINES < NUM_COLORS:
                raise ValueError('Terminal has less than 22 lines.')
            elif curses.COLS < total_cols:
                raise ValueError('Terminal has less than {} cols.'.format(
                    total_cols))


def end_run():
    try:
        curses.endwin()
        Theme(CURRENT_THEME).apply()
        exit()
    except KeyboardInterrupt:
        end_run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        end_run()
