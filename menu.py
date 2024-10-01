from msvcrt import getch

class MenuAction:
    def __init__(self, name, action, close_condition):
        self.action_name = name
        self.action = action
        self.close_condition = close_condition
         
class Menu:

    def __init__(self, name, close_action_name="Close"):
        self.name = name
        self.actions = []
        self.close_conditions = []
        self.startup_actions = []
        self.return_actions = []
        self.default_actions = [MenuAction(close_action_name, lambda: None, close_condition = lambda: True)]
    
    def add_action(self, name, action, close_condition = lambda: False):
        self.actions.append(MenuAction(name, action, close_condition))
        
    def add_startup_action(self, action):
        self.startup_actions.append(action)
        
    def add_return_action(self, action):
        self.return_actions.append(action)
        
    def add_submenu(self, name):
        new_menu = Menu(name, close_action_name = "Back")
        self.set_submenu(new_menu)
        return new_menu
        
    def set_submenu(self, menu, name = None):
        self.add_action(menu.name if name is None else name, lambda submenu=menu: submenu.open())
        
    def add_close_condition(self, condition):
        self.close_conditions.append(condition)
        
    def open(self):
        for startup_action in self.startup_actions:
            if startup_action():
                return
    
        menu = self.actions + self.default_actions
        close_menu = False
        while not close_menu:
            print("\n=== " + self.name + " ===")
            for idx, ma in enumerate(menu):
                print("( {0:0{1}} ) {2}".format(idx,len(str(len(menu)-1)),ma.action_name))
                
            try:
                if len(menu) > 10:
                    sel = input()
                    if sel == "exit":
                        return True
                else:
                    c = getch()
                    if c.decode() == chr(27):
                        return True
                    sel = c.decode('utf8')
                              
                selection = menu[int(sel.strip())]
            except:
                continue

            print("--> {0}".format(sel.strip()))
            selection.action()
            if selection.close_condition():
                close_menu = True
                
            for condition in self.close_conditions:
                if condition():
                    close_menu = True
                    
            if close_menu:
                for return_action in self.return_actions:
                    if return_action():
                       close_menu = False 