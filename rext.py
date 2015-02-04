#!/usr/bin/env python3

#Router EXploitation Toolkit
#rext.py - Startup script
#Author: Ján Trenčanský
#License: ADD LATER

import interface.cmdui

if __name__ == "__main__":
    interpreter = interface.cmdui.Interpreter()
    interpreter.cmdloop()

