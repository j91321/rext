#!/usr/bin/env python3

#Router EXploitation Toolkit
#rext.py - Startup script
#Author: Ján Trenčanský
#License: GNU GPL v3

import interface.cmdui

if __name__ == "__main__":
    interpreter = interface.cmdui.Interpreter()
    interpreter.cmdloop()

