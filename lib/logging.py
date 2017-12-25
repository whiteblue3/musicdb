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

import logging
import sys

class MBDLogFormatter(logging.Formatter):

    start_fmt= "\033[1;34m LOG[\033[0;34m%(asctime)s\033[1;34m|"
    file_fmt = "\033[0;35m%(filename)s\033[0;34m:\033[0;35m%(funcName)s\033[0;34m.\033[0;31m%(lineno)d\033[1;34m: "
    short    = "\033[0;35m%(filename)s\033[1;34m: "

    #debug_format    = "\033[1;34m LOG[\033[0;35mDEBUG\033[1;34m] " + file_format + "\033[1;30m%(message)s [%(module)s]"
    debug_format    = start_fmt + "\033[0;35mDEBUG\033[1;34m] " + file_fmt + "\033[1;30m%(message)s"
    info_format     = start_fmt + "\033[0;36mINFO \033[1;34m] " + short    + "\033[1;34m%(message)s"
    warning_format  = start_fmt + "\033[0;33mWARN \033[1;34m] " + file_fmt + "\033[1;33m%(message)s"
    error_format    = start_fmt + "\033[0;31mERROR\033[1;34m] " + file_fmt + "\033[1;31m%(message)s"
    critical_format = start_fmt + "\033[1;31mFATAL\033[1;34m] " + file_fmt + "\033[1;31m%(message)s"
    # %(asctime)s


    def __init__(self, ignorelist):
        logging.Formatter.__init__(self, datefmt="%Y-%m-%d %H:%M:%S")
        # reduce spam from third party libraries
        for entry in ignorelist:
            logging.getLogger(entry).setLevel(logging.WARNING)
        logging.root.setLevel(logging.DEBUG)


    # source: http://stackoverflow.com/questions/1343227/can-pythons-logging-format-be-modified-depending-on-the-message-log-level
    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = MBDLogFormatter.debug_format
        elif record.levelno == logging.INFO:
            self._style._fmt = MBDLogFormatter.info_format
        elif record.levelno == logging.WARNING:
            self._style._fmt = MBDLogFormatter.warning_format
        elif record.levelno == logging.ERROR:
            self._style._fmt = MBDLogFormatter.error_format
        elif record.levelno == logging.CRITICAL:
            self._style._fmt = MBDLogFormatter.critical_format

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result


class MusicDBLogger():
    def __init__(self, path="stderr", loglevelname="INFO", debugpath=None, config=None):
        # configure loglevel
        loglevelname = loglevelname.upper()
        loglevelmap = {}
        loglevelmap["DEBUG"]    = logging.DEBUG
        loglevelmap["INFO"]     = logging.INFO
        loglevelmap["WARNING"]  = logging.WARNING
        loglevelmap["ERROR"]    = logging.ERROR
        loglevelmap["CRITICAL"] = logging.CRITICAL
        loglevel = loglevelmap[loglevelname]


        # create output handler
        self.handler = []   # list of handler, at least one: stderr. maybe a file for more details

        # primary handler
        if path == "stdout":
            phandler = logging.StreamHandler(sys.stdout)
        elif path == "stderr":
            phandler = logging.StreamHandler(sys.stderr)
        else:
            phandler = logging.FileHandler(filename=path, mode="a")
        phandler.setLevel(loglevel)
        self.handler.append(phandler)


        # secondary handler
        if debugpath:
            shandler = logging.FileHandler(debugpath)
            shandler.setLevel(logging.DEBUG)
        else:
            shandler = None

        if shandler:
            self.handler.append(shandler)


        # configure formatter
        if config:
            self.formatter = MBDLogFormatter(config.log.ignore)
        else:
            self.formatter = MBDLogFormatter([])

        for h in self.handler:
            h.setFormatter(self.formatter)


        # Add handler
        for h in self.handler:
            logging.root.addHandler(h)


        # Show the user where to find the debugging infos
        if debugpath:
            logging.debug("logging debugging info in %s", debugpath)
        logging.debug("setting display-loglevel to \033[1;36m%s", loglevelname)



    def Reconfigure(self, path="stderr", loglevelname="DEBUG", debugpath=None, config=None):
        logging.debug("Reconfiguring logging behaviour")
        # configure loglevel
        loglevelname = loglevelname.upper()
        loglevelmap = {}
        loglevelmap["DEBUG"]    = logging.DEBUG
        loglevelmap["INFO"]     = logging.INFO
        loglevelmap["WARNING"]  = logging.WARNING
        loglevelmap["ERROR"]    = logging.ERROR
        loglevelmap["CRITICAL"] = logging.CRITICAL
        loglevel = loglevelmap[loglevelname]

        # remove old handlers
        for h in self.handler:
            logging.root.removeHandler(h)
            h.flush()
            h.close()
        self.handler = []

        # primary handler
        if path == "stdout":
            phandler = logging.StreamHandler(sys.stdout)
        elif path == "stderr":
            phandler = logging.StreamHandler(sys.stderr)
        else:
            phandler = logging.FileHandler(filename=path, mode="a")
        phandler.setLevel(loglevel)
        self.handler.append(phandler)

        # secondary handler
        if debugpath:
            shandler = logging.FileHandler(debugpath)
            shandler.setLevel(logging.DEBUG)
        else:
            shandler = None
        self.handler.append(shandler)


        # configure formatter
        if config:
            self.formatter = MBDLogFormatter(config.log.ignore)
        else:
            self.formatter = MBDLogFormatter([])

        for h in self.handler:
            h.setFormatter(self.formatter)


        # Add handler
        for h in self.handler:
            logging.root.addHandler(h)


        # Show the user where to find the debugging infos
        if debugpath:
            logging.debug("logging debugging info in %s", debugpath)
        logging.debug("setting display-loglevel to \033[1;36m%s", loglevelname)

        return self


    def GetLogger(self, name):
        logger = logging.getLogger(name)
        return logger


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

