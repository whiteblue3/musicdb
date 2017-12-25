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
"""
This is the main module to run the MusicDB Websocket Server.

To start and run the server, the following sequence of function calls is necessary:

    .. code-block:: python

        Initialize(mdbconfig, musicdatabase)
        StartWebSocketServer()
        Run()

MusicDB Server handles the following system signals:

    * USR1: :meth:`~mdbapi.server.SIGUSR1_Handler` - Update server caches and inform clients to update their caches
    * TERM: :meth:`~mdbapi.server.SIGTERM_Handler` - Shut down the server

Further more does this module maintain global instances of the following classes.
Those objects can be used inside the thread the server runs. 
Usually the main thread.
Using these objects saves a lot of memory.
If the server is not started, the objects are all ``None``.

    * :class:`lib.db.musicdb.MusicDatabase` as ``database``
    * :class:`mdbapi.mise.MusicDBMicroSearchEngine` as ``mise``
    * :class:`lib.cfg.musicdb.MusicDBConfig` as ``cfg``
    * :class:`lib.cfg.mdbstate.MDBState` as ``mdbstate``

The signals can be triggered using ``kill``:

    .. code-block:: bash

        # Update caches
        kill -USR1 $( cat /data/musicdb/musicdb.pid )

        # Terminate server
        kill -TERM $( cat /data/musicdb/musicdb.pid )

"""

import traceback
import random
import time
import signal
from threading          import Thread
from lib.cfg.musicdb    import MusicDBConfig
from lib.cfg.mdbstate   import MDBState
from lib.db.musicdb     import MusicDatabase
from lib.pidfile        import *
from lib.ws.server      import MusicDBWebSocketServer
from mdbapi.mise        import MusicDBMicroSearchEngine
from mdbapi.randy       import StartRandy, StopRandy
from mdbapi.tracker     import StartTracker, StopTracker
import mdbapi.mpd as mpd
import logging

# Global objects
# This is the server environment that needs to be accessed by many objects like the RPC-Server instances
# Instances
database    = None  # music.db object
mise        = None  # micre searche engine object
cfg         = None  # overall configuration file
mdbstate    = None  # ini file holding the state like selected genres and EoQ-Event
# Threadhandler
mpdthread   = None
# WS Server
tlswsserver = None
shutdown    = False

def SignalHandler(signum, stack):
    """
    This is the general signal handle for the MusicDB Server.
    This function reacts on system signals and calls the handler of a specific signal.

    Args:
        signum: signal number
        stack: current stack frame
    
    Returns: Nothing
    """
    if signum == signal.SIGUSR1:
        logging.debug("Got signal USR1")
        SIGUSR1_Handler()
    elif signum == signal.SIGTERM:
        logging.debug("Got signal TERM")
        SIGTERM_Handler()
    else:
        logging.warning("Got unexpected signal %s"%str(signum))


# Update Caches
def SIGUSR1_Handler():
    """
    The USR1 signal handler handles the USR1 system signal.
    Its task is to trigger updating the servers cache and to inform the clients to update.

    On server side:
    
        * The MiSE Cache gets updated by calling :meth:`mdbapi.mise.MusicDBMicroSearchEngine.UpdateCache`
        * The MPD database gets updated by calling :meth:`mdbapi.mpd.Update`


    To inform the clients a broadcast packet get sent with the following content: ``{method:"broadcast", fncname:"SIGUSR1", fncsig:"UpdateCaches", arguments:null, pass:null}``
    """
    global mise
    global tlswsserver
    logging.info("\033[1;36mSIGUSR1:\033[1;34m Updating caches …\033[0m")

    try:
        mise.UpdateCache()
    except Exception as e:
        logging.warning("Unexpected error updating MiSE cache: %s \033[0;33m(will be ignored)\033[0m", str(e))

    try:
        mpd.Update()
    except Exception as e:
        logging.warning("Unexpected error updating MPD cache: %s \033[0;33m(will be ignored)\033[0m", str(e))

    try:
        packet = {}
        packet["method"]      = "broadcast"
        packet["fncname"]     = "SIGUSR1"
        packet["fncsig"]      = "UpdateCaches"
        packet["arguments"]   = None
        packet["pass"]        = None
        tlswsserver.factory.BroadcastPacket(packet)
    except Exception as e:
        logging.warning("Unexpected error broadcasting a tags-update: %s \033[0;33m(will be ignored)\033[0m", str(e))


# Initiate Shutdown
def SIGTERM_Handler():
    """
    This function is the handler for the system signal TERM.
    It signals the server to shut down.
    """
    logging.info("\033[1;36mSIGTERM:\033[1;34m Initiate Shutdown …\033[0m")
    global shutdown
    shutdown = True



def Initialize(configobj, databaseobj):
    """
    This function initializes the whole server.
    It initializes lots of global objects that get shared between multiple connections.

    The following things happen when this method gets called:

        #. Assign the *configobj* and *databaseobj* to global variables ``cfg`` and ``database`` to share them between multiple connections
        #. Seed Python's randomizer *Randy* (See MDBAPI documentation :doc:`/mdbapi/randy`)
        #. Load the last state of MusicDB via :meth:`lib.cfg.mdbstate.MDBState` class
        #. Instantiate a global :meth:`mdbapi.mise.MusicDBMicroSearchEngine` object
        #. Start the song Tracker via :meth:`mdbapi.Tracker.StartTracker`
        #. Connect to MPD (Music Playing Daemon) and start Observer thread (see :doc:`/mdbapi/mpd` and :doc:`/mdbapi/tracker`)
        #. Update MiSE cache via :meth:`mdbapi.mise.MusicDBMicroSearchEngine.UpdateCache`
        #. Start the randomizer Randy via :meth:`mdbapi.Randy.StartRandy`
        #. Register the signals USR1 and TERM

    Args:
        configobj: :class:`~lib.cfg.musicdb.MusicDBConfig` that gets shared between connections
        databaseobj: :class:`~lib.db.musicdb.MusicDatabase` that gets shared between connections

    Returns:
        ``None``

    Raises:
        TypeError: When *configobj* is not of type :class:`~lib.cfg.musicdb.MusicDBConfig`
        TypeError: When *databaseobj* is not of type :class:`~lib.cfg.musicdb.MusicDatabase`
    """

    global cfg
    global database
    if type(configobj) != MusicDBConfig:
        logging.critical("Config-class of unknown type!")
        raise TypeError("configobj must be a valid MusicDBConfig object!")
    if type(databaseobj) != MusicDatabase:
        logging.critical("Database-class of unknown type!")
        raise TypeError("databaseobj must be a valid MusicDatabase object")

    cfg      = configobj
    database = databaseobj

    random.seed()

    # load MusicDBState file
    global mdbstate
    mdbstate    = MDBState(cfg.server.statefile, database)

    # Initialize all interfaces
    logging.debug("Initializing MicroSearchEngine…")
    global mise
    mise   = MusicDBMicroSearchEngine(database)

    # Start/Connect all interfaces
    logging.debug("Starting Tracker…")
    StartTracker(cfg)
    
    logging.debug("Starting MDP Client")
    mpd.StartMPDClient(cfg)
    
    logging.debug("Updateing MiSE Cache…")
    mise.UpdateCache()
    
    logging.debug("Starting Randy…")
    StartRandy(cfg)

    # Signal Handler
    logging.info("Register signals \033[0;36m(" + cfg.server.pidfile + ")\033[0m")
    logging.info("\t\033[1;36mUSR1:\033[1;34m Update Caches\033[0m")
    signal.signal(signal.SIGUSR1, SignalHandler)
    logging.info("\t\033[1;36mTERM:\033[1;34m Shutdown Server\033[0m")
    signal.signal(signal.SIGTERM, SignalHandler)

    return None



def StartWebSocketServer():
    """
    This function creates and starts a the actual MusicDB Websocket Server.

    Returns:
        ``True`` on success, otherwise ``False``
    """
    global tlswsserver
    tlswsserver = MusicDBWebSocketServer()
    
    retval = tlswsserver.Setup(cfg.websocket.address, cfg.websocket.port
            , cfg.tls.cert, cfg.tls.key)
    if retval == False:
        logging.critical("Setup for websocket server failed!")
        return False

    retval = tlswsserver.Start()
    if retval == False:
        logging.critical("Starting websocket server failed!")
        return False

    return True



def Shutdown():
    """
    This function stops the server and all its dependent threads.

    The following things happen when this function gets called:

        #. Stop the randomizer Randy via :meth:`mdbapi.randy.StopRandy`
        #. Stop the song Tracker via :meth:`mdbapi.tracker.StopTracker`
        #. Disconnect from MPD and stop the observer Thread via :meth:`mdbapi.mpd.StopObserver`
        #. Stop the websocket server

    At the end, the program gets terminated. So, this function gets never left.
    
    The exit code will be ``0`` if this was a regular shutdown.
    If the shutdown got forced, for example due to a critical error, the exit code is ``1``.

    This function should also be called when :meth:`~mdpapi.server.Initialize` fails or when it raises an exception.
    """
    logging.info("Shutting down MusicDB-Server")
    global tlswsserver

    if tlswsserver:
        logging.debug("Disconnect from clients…")
        tlswsserver.factory.CloseConnections()
    
    logging.debug("Stopping Randy…")
    StopRandy()

    logging.debug("Stopping Tracker…")
    StopTracker()

    logging.debug("Disconnecting from MPD…")
    mpd.StopObserver()
    
    if tlswsserver:
        logging.debug("Stopping TLS WS Server…")
        tlswsserver.Stop()

    # dead end
    global shutdown
    if shutdown:
        exit(0)
    else:
        exit(1)



def Run():
    """
    This is the servers main loop.

    Inside the loop all MusicDB Websocket Server events get handled by calling :meth:`lib.ws.server.MusicDBWebSocketServer.HandleEvents`.
    When a shutdown gets triggered the :meth:`~mdbapi.server.Shutdown` function gets called and the server stops.

    The :meth:`~mdbapi.server.Shutdown` gets also called the user presses *Ctrl-C* This leads to a regular shutdown.

    In as an exception occurs the :meth:`~mdbapi.server.Shutdown` gets called, too. In this case the exit-code will be ``1``.
    """
    logging.info("Setup complete. \033[1;37mExecuting server.\033[1;34m")
    # enter event loop
    global tlswsserver
    if not tlswsserver:
        logging.critical("TLS Websocket Server was not started!")
        return

    try:
        global shutdown
        while True:
            tlswsserver.HandleEvents()
            if shutdown:
                Shutdown()
            time.sleep(.1)  # Avoid high CPU load

    except KeyboardInterrupt:
        logging.warning("user initiated server shutdown");
        shutdown = True     # signal that this is a correct shutdown and no crash
        Shutdown()

    except Exception as e:
        logging.critical("FATAL ERROR (shutting down server!!):");
        logging.critical(e)
        traceback.print_exc()
        Shutdown()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
