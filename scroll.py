import tkinter as tk

# a take on one of several copy/pastes from s.o. that finally worked

class ScrolledFrame(tk.Frame):

    def __init__(self, parent, **kwargs):

        tk.Frame.__init__(self, parent, **kwargs)
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._xbar = tk.Scrollbar(self, orient='horizontal')
        self._xbar.grid(row=1, column=0, sticky='we')
        
        self._ybar = tk.Scrollbar(self, orient='vertical')
        self._ybar.grid(row=0, column=1, sticky='ns')
        
        self._canvas = tk.Canvas(self, xscrollcommand=self._xbar.set, yscrollcommand=self._ybar.set)
        self._canvas.grid(row=0, column=0, sticky='nswe')

        self._xbar.config(command=self._canvas.xview)
        self._ybar.config(command=self._canvas.yview)
        
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)
        
        self.interior = tk.Frame(self._canvas)
        
        self._window = self._canvas.create_window(0, 0, window=self.interior, anchor='nw')
        self.interior.bind('<Configure>', self.__configure_interior)
        self._canvas.bind('<Configure>', self.__configure_canvas)
        
        self._canvas.bind_all('<MouseWheel>', self.__mouse_wheel)

    def __configure_interior(self, *args):
        (size_x, size_y) = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        #print(f'CONFIG INTERIOR: {size_x}, {size_y}')
        self._canvas.config(scrollregion=f'0 0 {size_x} {size_y}')
        self.__configure_canvas(*args)
            
    def __configure_canvas(self, *args):
        #print('CONFIG CANVAS...')
        if self.interior.winfo_reqwidth() is not self._canvas.winfo_width():
            #print('  setting width')
            self._canvas.config(width=self.interior.winfo_reqwidth())
        if self.interior.winfo_reqheight() is not self._canvas.winfo_height():
            #print('  setting height')
            self._canvas.config(height=self.interior.winfo_reqheight())

    def __mouse_wheel(self, event):
        self._canvas.yview_scroll(-1 * (event.delta // 120), 'units')


        
        
        
        
        
        
        
        
        
        
        