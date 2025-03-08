import tkinter as tk
from tkinter import ttk

class DarkTheme:
    @staticmethod
    def apply_dark_theme(root):
        root.configure(bg='#2d2d2d')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#2d2d2d', foreground='white')
        style.configure('TFrame', background='#2d2d2d')
        style.configure('TLabel', background='#2d2d2d', foreground='white')
        style.configure('TButton', background='#404040', foreground='white',
                        borderwidth=1, focusthickness=3, focuscolor='none')
        style.map('TButton', background=[('active', '#4d4d4d')])
        style.configure('Treeview', background='#404040', foreground='white',
                        fieldbackground='#404040')
        style.map('Treeview', background=[('selected', '#4d4d4d')])
        style.configure('Treeview.Heading', background='#404040', foreground='white')
        style.configure('TCombobox', fieldbackground='#404040', background='#404040',
                        foreground='white')
        style.configure('TEntry', fieldbackground='#404040', foreground='white')

    @staticmethod
    def apply_light_theme(root):
        root.configure(bg='#f0f0f0')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#f0f0f0', foreground='black')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', foreground='black')
        style.configure('TButton', background='#e0e0e0', foreground='black',
                        borderwidth=1, focusthickness=3, focuscolor='none')
        style.map('TButton', background=[('active', '#d0d0d0')])
        style.configure('Treeview', background='white', foreground='black',
                        fieldbackground='white')
        style.map('Treeview', background=[('selected', '#d0d0d0')])
        style.configure('Treeview.Heading', background='#e0e0e0', foreground='black')
        style.configure('TCombobox', fieldbackground='white', background='white',
                        foreground='black')
        style.configure('TEntry', fieldbackground='white', foreground='black')