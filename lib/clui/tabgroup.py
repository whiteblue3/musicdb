# MusicDB,  a music manager with web-bases UI that focus on music.
# Copyright (C) 2017  Ralf Stemmer <ralf.stemmer@gmx.net>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lib.clui.frame import Frame

class TabGroup(object):
    def __init__(self):
        self.panes = []
        self.index = 0 # index of the current selected pane

    def AddPane(self, pane):
        self.panes.append(pane)

        # select first pane
        if len(self.panes) == 1:
            self.panes[0].SetLineStyle(Frame.LINESTYLE_BOLD)
            self.panes[0].Draw()

    def HandleKey(self, key):
        if not self.panes:
            return

        if key == "\t":
            self.panes[self.index].SetLineStyle(Frame.LINESTYLE_NORMAL)
            self.panes[self.index].Draw()
            self.index = (self.index + 1) % len(self.panes)
            self.panes[self.index].SetLineStyle(Frame.LINESTYLE_BOLD)
            self.panes[self.index].Draw()
            return

        self.panes[self.index].HandleKey(key)
        return



# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

