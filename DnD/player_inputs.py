from typing import Callable
import time

class _PlayerInputs:
    def __init__(self) -> None:
        self.registered_inputs : dict[str,list[Callable[[None],None]]] = {}

        # this is set at the beginning of run_game in main.py
        self.q = ... #UI_instance.player_input_queue
    
    def register_input(self, keysym : str, func : Callable[[None], None], persistent : bool = False) -> None:
        """keysym is the key used by Tcl (aka tkinter) when handling input events\n
        List of keys: https://www.tcl.tk/man/tcl8.4/TkCmd/keysyms.htm"""

        func.persistent = persistent

        if keysym in self.registered_inputs:
            self.registered_inputs[keysym].append(func)
        else:
            self.registered_inputs[keysym] = [func]
    
    def unregister_input(self, keysym : str) -> None:
        if keysym in self.registered_inputs:
            self.registered_inputs.pop(keysym)
    
    def unregister_all(self, include_persistent : bool = False) -> None:
        for key, func_list in self.registered_inputs.copy().items():
            # if we shouldnt delete persistent fucn and any of the functions connected to the current key are persistent:
            #   remove all non-persistent
            if not include_persistent and any(map(lambda func : func.persistent, func_list)):
                self.registered_inputs[key] = [func for func in func_list if func.persistent]
            
            # otherwise remove all
            else:
                self.registered_inputs.pop(key)

    def check_inputs(self) -> None:
        qsize = self.q.qsize()

        for _ in range(qsize):
            pressed_key = self.q.get()
            funcs_to_call = self.registered_inputs.get(pressed_key, [])
            [func() for func in funcs_to_call]
    
    def wait_for_key(self, keysym : str) -> None:
        while True:
            qsize = self.q.qsize()

            for _ in range(qsize):
                pressed_key = self.q.get()
                if pressed_key == "Return":
                    return
            
            time.sleep(1/20)


PlayerInputs = _PlayerInputs()