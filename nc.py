#!/usr/bin/env python

import sys
import socket
import SocketServer as socketserver
import shlex
import os
import threading
import optparse

_VERSION = '0.0.4b'

_DEFAULT_PORT = 7642
_DEFAULT_HOST = '127.0.0.1'
_DEFAULT_READ_SIZE = 1024

_CMD_LIST = 'ls'
_CMD_GET = 'pull'
_CMD_PUT = 'push'
_CMD_EXIT = 'exit'

_RESPONSE_ERROR = 'err'
_RESPONSE_OKAY = 'ok'

_RERR_TEXT = _RESPONSE_ERROR + " %s"

_config = {}
_KEY_DIR = 'dir'

_running = True

class NcsrHandler(socketserver.StreamRequestHandler):
    """
    'Net Cat (like) Server Request Handler'
    This defines the request handler for NcServer.
    It will always try to read the command, and
    then do as specified.
    """
    
    _ERR_NO_CMD = "There was no command sent."
    _ERR_UNKNOWN_FILE = "This file was not listed '%s'"
    _ERR_NO_FILE = "Missing file argument for command get."
    _ERR_UNKNOWN_CMD = "Unknown command '%s'."
    _ERR_PATH_EXISTS = ("The path '%s' already exists. " +
                        "Overwrite is not allowed.")
    _ERR_NOT_IN_DIR = "Path (%s) tries to leave source dir '%s'."
    
    def setup(self):
        
        if _config.has_key(_KEY_DIR):
            self.__dir = _config[_KEY_DIR]
        else:
            self.__dir = '.'
        
        socketserver.StreamRequestHandler.setup(self)
    
    def handle(self):
        
        cmdline = self.rfile.readline()
        self.__check_cmd(cmdline.strip('\n'))
    
    def __check_cmd(self, cmdline):
        
        args = shlex.split(cmdline)
        if len(args) >= 1:
            if args[0] == _CMD_LIST:
                self.__exec_list()
            elif args[0] == _CMD_GET:
                self.__exec_get(args[1:])
            elif args[0] == _CMD_PUT:
                self.__exec_put(args[1:])
            elif args[0] == _CMD_EXIT:
                global _running
                print "exit"
                self.__response_okay()
                _running = False
            else:
                self.__response_error(NcsrHandler._ERR_UNKNOWN_CMD
                    % cmdline)
        else:
            self.__response_error(NcsrHandler._ERR_NO_CMD)
    
    def __response_error(self, message):
        
        msg = ' '.join(message.split('\n'))
        self.wfile.write((_RERR_TEXT % msg) + '\n')
    
    def __response_okay(self):
        self.wfile.write(_RESPONSE_OKAY + '\n')
    
    def __exec_list(self):
        
        print "ls"
        files = self.__list_available_files()
        self.__response_okay()
        for file in files:
            self.wfile.write(file + '\n')
        self.wfile.write('\n')
        self.wfile.flush()
    
    def __exec_get(self, args):
        
        print "pull %s" % (" ".join(args))
        if len(args) >= 1:
            files = self.__list_available_files()
            fname = args[0]
            if fname in files:
                self.__response_okay()
                self.__send_file(fname)
            else:
                self.__response_error(
                    NcsrHandler._ERR_UNKNOWN_FILE
                    % fname)
        else:
            self.__response_error(NcsrHandler._ERR_NO_FILE)
    
    def __do_path(self, path):
        
        src = os.path.realpath(self.__dir)
        dst = os.path.realpath(path)
        
        if os.path.exists(dst):
            self.__response_error(NcsrHandler._ERR_PATH_EXISTS
                 % dst)
        
        if dst.startswith(src):
            self.__response_okay()
            return True
        else:
            self.__response_error(NcsrHandler._ERR_NOT_IN_DIR
             % (dst, src))
            return False
    
    def __exec_put(self, args):
        
        print "push %s" % (" ".join(args))
        if len(args) > 0:
            fname = args[0]
            path = os.path.join(self.__dir, fname)
            if self.__do_path(path):
                self.__receive_file(path)
    
    def __send_file(self, name):
        
        path = os.path.join(self.__dir, name)
        file_size = os.path.getsize(path)
        f = open(path, 'rb')
        try:
            self.wfile.write("%d\n" % file_size)
            self.wfile.flush()
            running = True
            while running:
                buffer = f.read(_DEFAULT_READ_SIZE)
                if len(buffer) > 0:
                    self.wfile.write(buffer)
                else:
                    running = False
            
            for i in xrange(_DEFAULT_READ_SIZE):
                self.wfile.write('\n\n\n')
            self.wfile.flush()
        finally:
            f.close()
    
    def __receive_file(self, path):
        
        f = open(path, 'wb')
        try:
            running = True
            while running:
                buffer = self.rfile.read(_DEFAULT_READ_SIZE)
                if len(buffer) > 0:
                    f.write(buffer)
                else:
                    running = False
        finally:
            f.close()
    
    def __list_available_files(self):
        
        files = []
        
        for file in os.listdir(self.__dir):
            path = os.path.join(self.__dir, file)
            if os.path.isfile(path):
                files.append(file)
        
        return files


class NcClient(object):
    
    _ERR_UNKNOWN = "Unknown error '%s'."
    _FILE_NOT_EXIST = "The file '%s' doesn't exists."
    
    def __init__(self, host=_DEFAULT_HOST, port=_DEFAULT_PORT):
        self._addr = (host, port)
        self.error = None
        self._conn = None
        self._rfile = None
        self._wfile = None
    
    def _start_cmd(self, cmd, args_line):
        
        cmdline = cmd + ' ' + args_line
        
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect(self._addr)
        
        self._wfile = self._conn.makefile('wb')
        self._rfile = self._conn.makefile('rb')
        
        self._wfile.write(cmdline + '\n')
        self._wfile.flush()
        line = self._rfile.readline().rstrip('\n')
        print "fetched line", line
        
        if line.startswith(_RESPONSE_OKAY):
            self.error = None
            return True
        elif line.startswith(_RESPONSE_ERROR):
            self.error = line
        else:
            self.error = NcClient._ERR_UNKNOWN % cmdline
        self._clean_up()
        return False
    
    def _clean_up(self):
        
        if not (self._rfile is None):
            self._rfile.close()
            self._rfile = None
        
        self._close_tx()
        
        if not (self._conn is None):
            self._conn.close()
            self._conn = None
    
    def _close_tx(self):
        
        if not (self._wfile is None):
            self._wfile.close()
            self._wfile = None
    
    def _get_size(self, infoline):
        return int(infoline)
    
    def put(self, filename, workdir):
        
        path = os.path.join(workdir, filename)
        if not os.path.exists(path):
            self.error = NcClient._FILE_NOT_EXIST % path
            return False
        
        fstring = '"%s"' % filename
        if self._start_cmd(_CMD_PUT, fstring):
            try:
                f = open(path, 'rb')
                try:
                    running = True
                    while running:
                        buffer = f.read(_DEFAULT_READ_SIZE)
                        if len(buffer) > 0:
                            self._wfile.write(buffer)
                        else:
                            running = False
                    return True
                finally:
                    f.close()
            finally:
                self._clean_up()
        else:
            return False
    
    def get(self, filename, workdir):
        
        fstring = '"%s"' % filename
        if self._start_cmd(_CMD_GET, fstring):
            try:
                self._close_tx()
                path = os.path.join(workdir, filename)
                f = open(path, 'wb')
                try:
                    running = True
                    info_line = self._rfile.readline().strip('\n')
                    total_size = self._get_size(info_line)
                    rx_count = 0
                    while True:
                        buffer = self._rfile.read(_DEFAULT_READ_SIZE)
                        write_cnt = len(buffer)
                        rx_count += write_cnt
                        
                        if rx_count > total_size:
                            write_cnt -= (rx_count - total_size)
                            f.write(buffer[0:write_cnt])
                            return True
                        else:
                            f.write(buffer)
                finally:
                    f.close()
            finally:
                self._clean_up()
        else:
            return False
    
    def list(self):
        
        lines = []
        if self._start_cmd(_CMD_LIST, ''):
            try:
                self._close_tx()
                running = True
                while running:
                    line = self._rfile.readline().strip('\n')
                    if len(line) > 0:
                        lines.append(line)
                    else:
                        running = False
                return (True, lines)
            finally:
                self._clean_up()
        else:
            return (False, lines)
    
    def exit(self):
        
        if self._start_cmd(_CMD_EXIT, ''):
            self._clean_up()
            return True
        else:
            return False


def server_main(host, port, workdir, verbose):
    
    _config[_KEY_DIR] = workdir
    if verbose:
        print "host ip: %s" % socket.gethostbyname(host)
    server = socketserver.TCPServer((host, port), NcsrHandler)
    while _running:
        server.handle_request()
    print "Bye from nc!"


if __name__ == "__main__":
    
    parser = optparse.OptionParser(
        usage = "usage: %prog [options]"
    )
    parser.add_option("-p", "--port", dest="port"
        , help="used port (default is %d)"
         % _DEFAULT_PORT
        , type='int'
    )
    parser.add_option("-a", "--address", dest="host",
        help="host src address (default is %s)"
         % _DEFAULT_HOST
    )
    parser.add_option("-w", "--work-dir", dest="work",
        help="the working directory (default is .)"
    )
    parser.add_option("-V", "--version", action="store_true",
        dest="version", help="shows version number only..."
    )
    
    parser.add_option("-v", "--verbose", action="store_true",
        dest="verbose", help="verbose output"
    )
    
    parser.set_defaults(port=_DEFAULT_PORT, host=_DEFAULT_HOST
        , work='.', version=False, verbose=False)
    
    options, args = parser.parse_args()
    
    if options.version:
        print _VERSION
    else:
        server_main(options.host, options.port, options.work
        		, options.verbose)
