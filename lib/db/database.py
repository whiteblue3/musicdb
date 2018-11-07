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

import sqlite3
import logging
import gzip
import pymysql.cursors


class Database(object):
    """
    This is the base class for all database classes in MusicDB.
    It establishes the connection to the mariadb databases.

    Args:
        host (str): host url of database.
        port (int): database port.
        name (str): database name of using.
        user (str): database user id.
        password (str): database user password.
        charset (str): database character set.

    Raises:
        TypeError: When *path* is not a string
    """

    def __init__(self, host, port, name, user, password, charset):
        # check params
        if type(host) != str:
            raise TypeError("A valid database host is necessary")

        if type(port) != int:
            raise TypeError("A valid database port is necessary")

        if type(name) != str:
            raise TypeError("A valid database name is necessary")

        if type(user) != str:
            raise TypeError("A valid database user is necessary")

        if type(password) != str:
            raise TypeError("A valid database password is necessary")

        if type(charset) != str:
            raise TypeError("A valid database charset is necessary")

        # connect to database
        cursorclass = pymysql.cursors.DictCursor

        self.db_connection = pymysql.connect(host=host, user=user, password=password, db=name, port=port, charset=charset, cursorclass=cursorclass)
        self.db_cursor     = self.db_connection.cursor()

    def __del__(self):
        self.db_connection.close()

    def Compress(self, string):
        """
        This method can be used to compress a string before storing it into the database.

        To keep a consistent database, use only this method and the complementary method :meth:`~lib.db.database.Database.Decompress`.
        It uses *gzip* for compression.

        Args:
            string (str): A string to compress

        Returns:
            A byte blob with the compresses string
        """
        return gzip.compress(string.encode("utf-8"))

    def Decompress(self, blob):
        """
        This method can be used to decompress a compresses string after reading it from the database.

        To keep a consistent database, use only this method and the complementary method :meth:`~lib.db.database.Database.Compress`.
        It uses *gzip* for decompression.

        Args:
            blob: A byte blob with the compresses string

        Returns:
            The decompresses string
        """
        return gzip.decompress(blob).decode("utf-8")
        

    def Execute(self, sql, values=None):
        """
        This method executes a SQL command.
        When the command fails, the database gets rolled back.
        Otherwise the changes gets committed.

        *values* can be a single value, a list, a dictionary or a tuple.

        Args:
            sql (str): SQL command
            values: Optional arguments used in the command

        Returns:
            ``None``

        Raises:
            TypeError: When *sql* is not a string

        Examples:

            .. code-block:: python

                db = Database("test.db")

                sql    = "INSERT INTO valuetable (name, content) VALUES (?, ?)"
                values = ("Name", 1000)

                db.Execute(sql, values)

            .. code-block:: python

                db = Database("test.db")

                sql    = "UPDATE valuetable SET content = ? WHERE name = ?"
                values = (1000, "Name")

                db.Execute(sql, values)
                

        """
        if type(sql) != str:
            raise TypeError("Invalid sql-type. String expected!")

        if values:
            if type(values) != tuple and type(values) != list and type(values) != dict:
                values = [values]   # create a one element list because mariadb:execute expects one

        try:
            if values:
                self.db_cursor.execute(sql, values)
            else:
                self.db_cursor.execute(sql)

        except Exception as e:
            self.db_connection.rollback()
            raise e

        self.db_connection.commit()
        return None


    # get some data from the database
    def GetFromDatabase(self, sql, values=None):
        """
        This method gets values from the database by executing a SQL command and fetching the results.
        When the command fails, the database gets rolled back.

        values can be a single value, a list, a dictionary or a tuple.

        This method returns a list of tuples.
        Each list element corresponds to one returned row.
        Each row is represented by a tuple of values.

        If only one value is expected, it is ``[(x,)]``.

        Args:
            sql (str): SQL command
            values: Optional arguments used in the command

        Returns:
            The results of the SQL command

        Raises:
            TypeError: When *sql* is not a string

        Example:

            .. code-block:: python

                db = Database("test.db")

                sql = "SELECT name FROM valuetable WHERE content = ?"

                results = db.Execute(sql, 1000)
                if not results:
                    print("No entries with value 1000 in database")
                    return

                for entry in results:
                    print(entry[0])
                
        """
        if type(sql) != str:
            raise TypeError("Invalid sql-type. String expected!")

        if values:
            if type(values) != tuple and type(values) != list:
                values = [values]   # create a one element list because splite3:execute expects one

        try:
            if values:
                self.db_cursor.execute(sql, values)
            else:
                self.db_cursor.execute(sql)

            data = self.db_cursor.fetchall()

        except Exception as e:
            self.db_connection.rollback()
            raise e

        return data



# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

