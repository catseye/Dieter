#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""
scanner.py -- lexical scanner for the Dieter programming language.
$Id: scanner.py 382 2010-01-28 23:40:43Z cpressey $
"""

class Scanner(object):
    """
    A lexical scanner.
    """

    def __init__(self, input):
        """
        Create a new Scanner object that will consume the given
        UTF-8 encoded input string.
        """
        self._input = unicode(input, 'utf-8')
        self._token = None
        self.scan()

    def scan(self):
        """
        Consume a token from the input.
        """
        self._token = ""
        if len(self._input) == 0:
            self.toktype = "eof"
            return
        while self._input[0].isspace():
            self._input = self._input[1:]
            if len(self._input) == 0:
                self.toktype = "eof"
                return
        if self._input[0].isalpha():
            while self._input[0].isalnum() or self._input[0] == '_':
                self._token += self._input[0]
                self._input = self._input[1:]
            self.toktype = "ident"
        elif self._input[0].isdigit():
            while self._input[0].isdigit():
                self._token += self._input[0]
                self._input = self._input[1:]
            self.toktype = "int"
            self.tokval = int(self._token)
        elif self._input[:1] == "\"":
            st = ""
            self._input = self._input[1:]
            while self._input[:1] != "\"":
                st += self._input[:1]
                self._input = self._input[1:]
            self._input = self._input[1:]
            self.toktype = "string"
            self.tokval = st
        elif self._input[:2] == ':=':
            self._token = ':='
            self._input = self._input[2:]
            self.toktype = "op"
        elif self._input[:2] == '/*':
            while self._input[:2] != '*/':
                self._input = self._input[1:]
            self._input = self._input[2:]
            return self.scan()
        elif self._input[:1] == u"♥":
            self._token = self._input[:1]
            self._input = self._input[1:]
            self.toktype = "op"
        else:
            self._token = self._input[0]
            self._input = self._input[1:]
            self.toktype = "op"
        #print "scanned: '" + str(self._token) + "'"
    
    def get_token(self):
        """
        Return the current token as a string.  Using the read-only
        token property is preferred for readability.
        """
        return self._token
    
    token = property(get_token)

    def grab(self):
        """
        Return the current token as a string, and advance.
        """
        t = self._token
        self.scan()
        return t

    def expect(self, str):
        """
        Expect a certain token to be in the input, and complain
        if it is not.
        """
        if self._token == str:
            self.scan()
        else:
            self.error("expected " + str + ", found " + self._token)

    def error(self, str):
        """
        Log the given scan error.
        """
        print "error: " + str
        self.scan()
