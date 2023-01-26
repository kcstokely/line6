import json, os, subprocess, tkinter as tk

from config import config
from scroll import ScrolledFrame

CP_BTN_WIDTH = 3 if os.name == 'posix' else 5

############

device = 'USB Uno MIDI Interface MIDI'

def send_command(cc, value):
    subprocess.run(['sendmidi', 'dev', device, 'ch', '1', 'cc', str(cc), str(value)])

def send_var(which, var_name):
    value = variables[var_name].get()
    cc = config['cc'][which][var_name]
    if send_allowed:
        print(f'{var_name:<12} --> {value}')
        send_command(cc, value)
    
####################################

class LoadingZone(tk.Frame):
    
    def on_send(self):
        [ send_var(self.which, var) for var in config['cc'][self.which] ]
    
    ###
    
    def on_save(self):
        
        idx = self.select.get()
        if idx == -1:
            print('NOPE.')
            return
        
        print(f'SAVE: {self.which} #{idx}')
        print(f'FILE: {self.dpath}')
        
        self.data[str(idx)] = {'descr': '', 'values': {}}
        self.data[str(idx)]['descr'] = self.descrs[idx].get()
        for name in config['cc'][self.which]:
            print(f'SAVE: {name} - {value}')
            self.data[str(idx)]['values'][name] = variables[name].get()

        with open(self.dpath, 'w') as fp:
            json.dump(self.data, fp)

    ###
            
    def on_load(self):
        
        send_allowed = False
        
        idx = self.select.get()
        if idx == -1:
            print('NOPE.')
            return
        
        print(f'LOAD: {self.which} #{idx}')
        print(f'FILE: {self.dpath}')
        
        with open(self.dpath, 'r') as fp:
            data = json.load(fp)
            
        if not str(idx) in self.data:
            print(f'  ...FLOP!')
            return
        
        for name, value in self.data[str(idx)]['values'].items():
            try:
                variables[name].set(value)
                print(f'LOAD: {name} - {value}')
            except:
                print(f'WHAT: {name} - {value}')
        
        if self.which == 'amp':
            value = self.data[str(idx)]['values']['mic']
            var_mic_pos.set((value+1)  % 2)
            var_mic_mod.set((value+1) // 2)
            for name in ['gate_toggle', 'comp_toggle']:
                btn = buttons[name]
                if variables[name].get() < 64:
                    btn.config(relief='raised')
                else:
                    btn.config(relief='sunken')
                    
        if self.which == 'mod':
            value = list(config['name']['mod'].keys())[variables['mod_model'].get()]
            on_mod_select(value)
            value = list(config['name']['del'].keys())[variables['del_model'].get()]
            on_del_select(value)
            value = self.data[str(idx)]['values']['rev_model']
            var_rev_cls.set(value//3)
            var_rev_mod.set(value%3)
            on_type_select()
            for name in ['mod_toggle', 'del_toggle', 'rev_toggle']:
                btn = buttons[name]
                if variables[name].get() < 64:
                    btn.config(relief='raised')
                else:
                    btn.config(relief='sunken')
                    
        send_allowed = True
        
    ###
    
    def on_click(self, sdx=None):
        for btn, ent in zip(self.btns, self.ents):
            btn.config(relief='raised')
            ent.config(state='disabled')
        if sdx is not None:
            if not sdx == self.select.get():
                self.select.set(sdx)
                self.btns[sdx].configure(relief='sunken')
                self.ents[sdx].configure(state='normal')
            else:
                self.select.set(-1)

    ###
    
    def make(self, which):
        
        num = 8       
        self.which = which
        self.dpath = f'data_{which}.json'
        if os.path.exists(self.dpath):
            with open(self.dpath, 'r') as fp:
                self.data = json.load(fp)
        else:
            self.data = {}

        self.btns = []
        self.ents = []
        self.select = tk.IntVar()
        self.descrs = [ tk.StringVar() for _ in range(num) ]
        
        for idx in self.data:
            idx = int(idx)
            assert idx < num
            self.descrs[idx].set(self.data[str(idx)]['descr'])
        
        top = tk.Frame(self)
        top.grid(row=0, column=0, columnspan=2)
        b_l = tk.Frame(self, padx=6, pady=6)
        b_l.grid(row=1, column=0)
        b_r = tk.Frame(self)
        b_r.grid(row=1, column=1, padx=6, pady=6)
        
        send = tk.Button(top, text='SEND TO LINE6', command=self.on_send)
        send.grid(row=0, column=0, padx=36, pady=6)
        load = tk.Button(top, text='LOAD', command=self.on_load)
        load.grid(row=0, column=1, padx=36, pady=6)
        save = tk.Button(top, text='SAVE', command=self.on_save)
        save.grid(row=0, column=2, padx=36, pady=6)

        for cdx, bot in enumerate([b_l, b_r]):
            for rdx in range(num//2):
                sdx = cdx*(num//2)+rdx
                btn = tk.Button(bot, width=2, font='Helvetica 6 bold', command=lambda sdx=sdx: self.on_click(sdx))
                self.btns.append(btn)
                btn.grid(row=rdx, column=0, padx=3, pady=6)
                ent = tk.Entry(bot, width=36, textvariable=self.descrs[sdx])
                self.ents.append(ent)
                ent.grid(row=rdx, column=1, padx=3, pady=6)
                
        self.select.set(-1)
        self.on_load()
        self.on_click()

####################################

class ControlPanel(tk.Frame):
    
    exceptions = [
        'mod_param1_a',
        'mod_param1_b',
        'del_param1_a',
        'del_param1_b'
    ]
    
    def up(self, name):
        inc = 1 if name in ControlPanel.exceptions else delta.get()
        variables[name].set(min(127, variables[name].get() + inc))
        send_var(self.which, name)
        
    def down(self, name):
        inc = 1 if name in ControlPanel.exceptions else delta.get()
        variables[name].set(max(0, variables[name].get() - inc))
        send_var(self.which, name)
            
    def make(self, which, var_names, disp_names=None):
        self.which = which
        for ndx, name in enumerate(var_names):
            panel = tk.Frame(self)
            if disp_names:
                disp_name = disp_names[ndx]
                if isinstance(disp_name, str):
                    tk.Label(panel, text=disp_name, font='Helvetica 11 bold').grid(row=0, columnspan=2)
                else:
                    tk.Label(panel, textvariable=disp_name, font='Helvetica 11 bold').grid(row=0, columnspan=2)
            else:
                tk.Label(panel, text=name, font='Helvetica 12 bold').grid(row=0, columnspan=2)
            tk.Label(panel, textvariable=variables[name]).grid(row=1, columnspan=2)
            tk.Scale(panel, from_=0, to=127, resolution=1, showvalue=0, variable=variables[name], command=lambda x, which=self.which, name=name: send_var(which, name), orient='horizontal').grid(row=2, columnspan=2)
            tk.Button(panel, width=CP_BTN_WIDTH, text='\u2193', command=lambda name=name: self.down(name)).grid(row=3, column=0)
            tk.Button(panel, width=CP_BTN_WIDTH, text='\u2191', command=lambda name=name: self.up(name)).grid(row=3, column=1)
            panel.grid(row=1, column=ndx, padx=6, pady=6)

####################################

def toggle(which, name):
    if which:
        variables[name].set((variables[name].get()+64) % 128)
        send_var(which, name)
    btn = buttons[name]
    if btn.config('relief')[-1] == 'sunken':
        btn.config(relief='raised')
    else:
        btn.config(relief='sunken')

############

send_allowed = False

root = tk.Tk()
root.title("you know i'm gonna send it")
#root.geometry('1360x768')

def onkey(event):
    try:
        value = list('`12345').index(event.char)
    except ValueError:
        pass
    else:
        value = 2**value if not value == 5 else 5
        print(f'SET DELTA: {value}')
        delta.set(value)
        
delta = tk.IntVar(name='delta')
delta.set(1)
root.bind('<Key>', onkey)

buttons = {}
variables = { var: tk.IntVar(name=var) for which in config['cc'] for var in config['cc'][which] }
# keys must be unique, but we group them for sending

var_mod_names = [ tk.StringVar() for _ in range(6) ]
var_del_names = [ tk.StringVar() for _ in range(6) ]
var_rev_names = [ tk.StringVar() for _ in range(3) ]

var_mic_pos = tk.IntVar()
var_mic_mod = tk.IntVar()

var_rev_cls = tk.IntVar()
var_rev_mod = tk.IntVar()

###  MAIN

# why the fuck is the alignment perfect on windows, but not on linux?

scrolled_frame = ScrolledFrame(root)
scrolled_frame.pack(expand=True, fill='both')

amp_load = LoadingZone(scrolled_frame.interior, borderwidth=2, relief=tk.SOLID)
amp_load.make('amp')
amp_load.grid(row=0, column=0, sticky='e', padx=12, pady=(6, 0))

mod_load = LoadingZone(scrolled_frame.interior, borderwidth=2, relief=tk.SOLID)
mod_load.make('mod')
mod_load.grid(row=0, column=1, sticky='w', padx=12, pady=(6, 0))

gauche = tk.Frame(scrolled_frame.interior, padx=6, pady=6)
gauche.grid(row=1, column=0, sticky='ns')

droite = tk.Frame(scrolled_frame.interior, padx=6, pady=6)
droite.grid(row=1, column=1, sticky='ns')

### GAUCHE

var_names = ['volume', 'drive', 'bass', 'mids', 'treble', 'presence']
amp_control = ControlPanel(gauche, borderwidth=2, relief=tk.SOLID)
amp_control.make('amp', var_names)
amp_control.pack(padx=6, pady=6, anchor='e')

gac_control = tk.Frame(gauche)
gac_control.pack(padx=6, anchor='e')
gate = tk.Frame(gac_control, borderwidth=2, relief=tk.SOLID)
gate.grid(row=0, column=0, padx=(0,6), pady=6)
comp = tk.Frame(gac_control, borderwidth=2, relief=tk.SOLID)
comp.grid(row=0, column=1, padx=(6,0), pady=6)

amp_choose = tk.Frame(gauche, borderwidth=2, relief=tk.SOLID)
amp_choose.pack(padx=6, pady=6, anchor='e')

cab_choose = tk.Frame(gauche, borderwidth=2, relief=tk.SOLID)
cab_choose.pack(padx=6, pady=6, anchor='e')

mic_choose = tk.Frame(gauche, borderwidth=2, relief=tk.SOLID)
mic_choose.pack(padx=6, pady=6, anchor='e')

### DROITE

mod_control = tk.Frame(droite, borderwidth=2, relief=tk.SOLID)
mod_control.pack(padx=6, pady=6, anchor='w')

del_control = tk.Frame(droite, borderwidth=2, relief=tk.SOLID)
del_control.pack(padx=6, pady=6, anchor='w')

rev_control = tk.Frame(droite, borderwidth=2, relief=tk.SOLID)
rev_control.pack(padx=6, pady=6, anchor='w')

############
# AMP SELECT

for gdx, (grp_name, group) in enumerate(config['amp']['amp'].items()):
    column = tk.Frame(amp_choose)
    #label = tk.Label(column, text=grp_name, font='Helvetica 11 bold')
    #label.pack(anchor='w', pady=(0,6))
    for ndx, (name, item) in enumerate(group.items()):
        text = f"'{str(item['year'])[-2:]} " if 'year' in item else ''
        text = text + item['model']
        radio = tk.Radiobutton(column, text=text, variable=variables['amp'], value=item['value'], command=lambda: send_var('amp', 'amp'))
        radio.pack(anchor='w')
    column.pack(side='left', anchor='n', padx=6, pady=6)

############
# CAB SELECT

radio = tk.Radiobutton(cab_choose, text='no cab', variable=variables['cab'], value=0, command=lambda: send_var('amp', 'cab'))
radio.grid(row=0, column=0, padx=6, pady=6)

panel = tk.Frame(cab_choose)
panel.grid(row=0, column=1, padx=6, pady=6)

for gdx, (grp_name, group) in enumerate(config['amp']['cab'].items()):
    column = tk.Frame(panel)
    #label = tk.Label(column, text=grp_name, font='Helvetica 11 bold')
    #label.pack(anchor='w', pady=(0,6))
    for ndx, (name, item) in enumerate(group.items()):
        text = f"{item['size']} " if 'size' in item else ''
        text = text + item['model']
        radio = tk.Radiobutton(column, text=text, variable=variables['cab'], value=item['value'], command=lambda: send_var('amp', 'cab'))
        radio.pack(anchor='w')
    column.pack(side='left', anchor='n', padx=6, pady=6)

############
# MIC SELECT

def on_mic_select():
    if var_mic_mod.get():
        mic_model = 2 * var_mic_mod.get() - 1 + var_mic_pos.get()
    else:
        mic_model = 0
    variables['mic'].set(mic_model)
    send_var('amp', 'mic')

radio = tk.Radiobutton(mic_choose, text='no mic', variable=var_mic_mod, value=0, command=on_mic_select)
radio.grid(row=0, column=0, padx=6, pady=6)

panel = tk.Frame(mic_choose)
panel.grid(row=0, column=1, padx=6, pady=6)

pos_names = ['on axis', 'off axis']
row = tk.Frame(panel)
for value, name in enumerate(pos_names):
    tk.Radiobutton(row, text=name, variable=var_mic_pos, value=value, command=on_mic_select).pack(side='left')
row.pack(padx=6, pady=(6, 0))

mic_names = config['amp']['mic']
row = tk.Frame(panel)
for value, name in enumerate(mic_names):
    tk.Radiobutton(row, text=name, variable=var_mic_mod, value=value+1, command=on_mic_select).pack(side='left')
row.pack(padx=6, pady=(3,6))

############    
# GATE / COMP

btn = tk.Button(gate, text='Gate', command=lambda: toggle('amp', 'gate_toggle'), font='Helvetica 13 bold')
buttons.update({'gate_toggle': btn})
btn.grid(row=0, column=0, padx=6, pady=6, sticky='n')

var_names = ['gate_thresh', 'gate_decay']
disp_names = ['thresh', 'decay']
panel = ControlPanel(gate)
panel.make('amp', var_names, disp_names)
panel.grid(row=0, column=1, padx=6, pady=6)

btn = tk.Button(comp, text='Comp', command=lambda: toggle('amp', 'comp_toggle'), font='Helvetica 13 bold')
buttons.update({'comp_toggle': btn})
btn.grid(row=0, column=1, padx=6, pady=6, sticky='n')

var_names = ['comp_thresh', 'comp_gain']
disp_names = ['thresh', 'gain']
panel = ControlPanel(comp)
panel.make('amp', var_names, disp_names)
panel.grid(row=0, column=0, padx=6, pady=6)

############
# MODULATION

btn = tk.Button(mod_control, text='Modulation', command=lambda: toggle('mod', 'mod_toggle'), font='Helvetica 14 bold')
buttons.update({'mod_toggle': btn})
btn.grid(row=0, column=0, rowspan=2, padx=6, pady=6, sticky='w')

row = tk.Frame(mod_control)
tk.Radiobutton(row, text='pre', variable=variables['mod_pp'], value=0, command=lambda: send_var('mod', 'mod_pp')).pack(side='left')
tk.Radiobutton(row, text='post', variable=variables['mod_pp'], value=64, command=lambda: send_var('mod', 'mod_pp')).pack(side='left')
row.grid(row=0, column=1, padx=3, pady=(6,3))

def on_mod_select(mod_name):
    for ndx, name in enumerate(config['name']['mod'][mod_name]):
        var_mod_names[ndx].set(name)

row = tk.Frame(mod_control)
for value, mod_name in enumerate(config['name']['mod']):
    tk.Radiobutton(row, text=mod_name, variable=variables['mod_model'], value=value, command=lambda mod_name=mod_name: on_mod_select(mod_name)).pack(side='left')
row.grid(row=1, column=1, padx=3, pady=0)

var_names = ['mod_mix', 'mod_param1_a', 'mod_param1_b', 'mod_param2', 'mod_param3', 'mod_param4']
row = ControlPanel(mod_control)
row.make('mod', var_names, var_mod_names)
row.grid(row=2, column=0, columnspan=2, padx=3, pady=0)

current_mod = list(config['name']['mod'].keys())[variables['mod_model'].get()]
on_mod_select(current_mod)

############
# DELAY

btn = tk.Button(del_control, text='Delay', command=lambda: toggle('mod', 'del_toggle'), font='Helvetica 14 bold')
buttons.update({'del_toggle': btn})
btn.grid(row=0, column=0, rowspan=2, padx=6, pady=6, sticky='w')

row = tk.Frame(del_control)
tk.Radiobutton(row, text='pre', variable=variables['del_pp'], value=0, command=lambda: send_var('mod', 'del_pp')).pack(side='left')
tk.Radiobutton(row, text='post', variable=variables['del_pp'], value=64, command=lambda: send_var('mod', 'del_pp')).pack(side='left')
row.grid(row=0, column=1, padx=3, pady=(6,3))

def on_del_select(del_name):
    for ndx, name in enumerate(config['name']['del'][del_name]):
        var_del_names[ndx].set(name)

row = tk.Frame(del_control)
for value, del_name in enumerate(config['name']['del']):
    tk.Radiobutton(row, text=del_name, variable=variables['del_model'], value=value, command=lambda del_name=del_name: on_del_select(del_name)).pack(side='left')
row.grid(row=1, column=1, padx=3, pady=0)

var_names = ['del_mix', 'del_param1_a', 'del_param1_b', 'del_param2', 'del_param3', 'del_param4']
row = ControlPanel(del_control)
row.make('mod', var_names, var_del_names)
row.grid(row=2, column=0, columnspan=2, padx=3, pady=0)

current_del = list(config['name']['del'].keys())[variables['del_model'].get()]
on_del_select(current_del)

############
# REVERB

btn = tk.Button(rev_control, text='Reverb', command=lambda: toggle('mod', 'rev_toggle'), font='Helvetica 14 bold')
buttons.update({'rev_toggle': btn})
btn.grid(row=0, column=0, rowspan=2, padx=6, pady=6, sticky='w')

def on_type_select():
    type_name = list(config['name']['rev'].keys())[var_rev_cls.get()]
    rev_names = config['name']['rev'][type_name]
    for ndx, name in enumerate(rev_names):
        var_rev_names[ndx].set(name)
    on_rev_select()
        
row = tk.Frame(rev_control)
for value, rev_name in enumerate(config['name']['rev']):
    tk.Radiobutton(row, text=rev_name, variable=var_rev_cls, value=value, command=on_type_select).pack(side='left')
row.grid(row=0, column=1, padx=3, pady=(6,3))

def on_rev_select():
    rev_model = 3*var_rev_cls.get()+var_rev_mod.get()
    variables['rev_model'].set(rev_model)
    send_var('mod', 'rev_model')

row = tk.Frame(rev_control)
for value in range(3):
    tk.Radiobutton(row, textvariable=var_rev_names[value], variable=var_rev_mod, value=value, command=on_rev_select).pack(side='left')
row.grid(row=1, column=1, padx=3, pady=0)

var_names = ['level', 'pre-delay', 'decay', 'tone']
row = ControlPanel(rev_control)
row.make('mod', var_names)
row.grid(row=2, column=0, columnspan=2, padx=3, pady=0)

on_type_select()

############

if __name__ == '__main__':
    
    # only send midi from linux
    if os.name == 'posix':
        send_allowed = True
        
    root.mainloop()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    