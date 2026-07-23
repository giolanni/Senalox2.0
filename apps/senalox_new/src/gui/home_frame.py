import tkinter as tk
from tkinter import ttk
from src.core.state_manager import ApplicationState, AppMode

class HomeFrame(ttk.Frame):
    def __init__(self, parent, app_state: ApplicationState, on_mode_selected):
        super().__init__(parent)
        self.app_state = app_state
        self.on_mode_selected = on_mode_selected
        self.create_widgets()
        
    def create_widgets(self):
        ttk.Label(self, text="Seleziona modalità:", font=('Arial', 14)).pack(pady=20)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="FULL", 
                 command=lambda: self.set_mode(AppMode.FULL)).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="2009+", 
                 command=lambda: self.set_mode(AppMode.POST_2009)).pack(side=tk.LEFT, padx=10)
    
    def set_mode(self, mode):
        self.app_state.set_mode(mode)
        self.on_mode_selected()
