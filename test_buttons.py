import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.geometry('600x400')
root.configure(bg='#1a1a2e')

f = tk.Frame(root, bg='#16213e')
f.pack(fill='x', padx=20, pady=10)

# 使用 Radiobuttons 替代 Button
selected = [None]

for i in range(4):
    rb = tk.Radiobutton(f, text=f'Option {i}', font=('Microsoft YaHei', 12),
                       bg='#16213e', fg='#eee', selectcolor='#1a3a6e',
                       activebackground='#16213e', activeforeground='#fff',
                       anchor='w', justify='left', cursor='hand2',
                       variable=selected, value=i,
                       command=lambda idx=i: print('SELECTED', idx))
    rb.pack(fill='x', padx=14, pady=2)

root.mainloop()