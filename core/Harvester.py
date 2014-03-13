import cmd

class RextHarvester(cmd.Cmd):
    def __init__(self):
        print(self)
        self.prompt = ">"
        self.cmdloop()
        cmd.Cmd.__init__(self)
    def do_exit(self,e):
        return True
    def do_harvest(self):
        pass
        
