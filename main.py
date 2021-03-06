# -*- coding: utf-8 -*-
try:
    from kivy_deps import sdl2, glew
except:
    pass
from kivy.config import Config
from kivy.utils import platform
Config.set('kivy', 'exit_on_escape', '0')
if platform != 'android':
    import ctypes
    user32 = ctypes.windll.user32
    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'left', int(user32.GetSystemMetrics(0)/2))
    Config.set('graphics', 'top',  50)
    from kivy.core.window import Window
    Window.size = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
from kivy.core.window import Window
from kivy.app import App
from mod_ddt import DDT
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.switch import Switch
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy import base
from kivy.graphics import Color, Rectangle
from mod_ddt_screen import DDTScreen
from kivy.clock import Clock
from mod_ddt_ecu import DDTECU
import os, sys, glob
import mod_globals, mod_db_manager, mod_ddt_utils, mod_ddt
if int(Window.size[1]) > int(Window.size[0]):
    fs = int(Window.size[1])/(int(Window.size[0])/9)
else:
    fs = int(Window.size[0])/(int(Window.size[1])/9)

__all__ = 'install_android'

mod_globals.os = platform

if mod_globals.os == 'android':
    try:
        from jnius import autoclass
        import glob
        AndroidPythonActivity = autoclass('org.renpy.android.PythonActivity')
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        AndroidActivityInfo = autoclass('android.content.pm.ActivityInfo')
        Environment = autoclass('android.os.Environment')
        Params = autoclass('android.view.WindowManager$LayoutParams')
        user_datadir = Environment.getExternalStorageDirectory().getAbsolutePath() + '/pyddt/'
        mod_globals.user_data_dir = user_datadir
        mod_globals.cache_dir = user_datadir + '/cache/'
        mod_globals.log_dir = user_datadir + '/logs/'
        mod_globals.dumps_dir = user_datadir + '/dumps/'
    except:
        mod_globals.ecu_root = '../'
        try:
            import serial
            from serial.tools import list_ports
        except:
            pass
elif mod_globals.os == 'nt':
    import pip
    try:
        import serial
    except ImportError:
        pip.main(['install', 'pyserial'])
    try:
        import colorama
    except ImportError:
        pip.main(['install', 'colorama'])
        try:
            import colorama
        except ImportError:
            sys.exit()
    colorama.init()
else:
    try:
        import serial
        from serial.tools import list_ports
    except:
        pass

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
argv_glob = sys.argv
sys.argv = sys.argv[0:1]
resizeFont = False

def set_orientation_landscape():
    if mod_globals.os == 'android':
        activity = AndroidPythonActivity.mActivity
        activity.setRequestedOrientation(AndroidActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)

def set_orientation_portrait():
    if mod_globals.os == 'android':
        activity = AndroidPythonActivity.mActivity
        activity.setRequestedOrientation(AndroidActivityInfo.SCREEN_ORIENTATION_PORTRAIT)

class MyGridLayout(GridLayout):
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.pos_hint={"top": 1, "left": 1}
        
        if 'bgcolor' in kwargs:
            self.bgcolor = kwargs['bgcolor']
        else:
            self.bgcolor =(1, 0, 0, 1)
    def on_size(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
            Rectangle(pos=(self.pos[0],self.pos[1]), size=(self.size[0], self.size[1]))

class MyLabel(Label):
    global fs
    def __init__(self, **kwargs):
        if 'bgcolor' in kwargs:
            self.bgcolor = kwargs['bgcolor']
        else:
            self.bgcolor = (0.5, 0.5, 0, 1)
        super(MyLabel, self).__init__(**kwargs)
        self.bind(size=self.setter('text_size'))
        if 'halign' not in kwargs:
            self.halign = 'center'
        if 'valign' not in kwargs:
            self.valign = 'middle'
        if 'font_size' not in kwargs:
            self.font_size = fs * 2
        if 'size_hint' not in kwargs:
            self.size_hint = (1, None)
        if 'height' not in kwargs:
            fmn = 1.7
            lines = len(self.text.split('\n'))
            simb = len(self.text) / 60
            if lines < simb: lines = simb
            if lines < 7: lines = 5
            if lines > 20: lines = 15
            if 1 > simb: lines = 1.5
            if fs > 20: 
                lines = lines * 1.05
                fmn = 1.5
            self.height = fmn * lines * fs
    
    def on_size(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
            Rectangle(pos=self.pos, size=self.size)

class PYDDT(App):
    
    def __init__(self):
        self.button = {}
        self.textInput = {}
        self.ptree = {}
        self.eculist = mod_ddt_utils.loadECUlist()
        super(PYDDT, self).__init__()
        Window.bind(on_keyboard=self.key_handler)

    def key_handler(self, window, keycode1, keycode2, text, modifiers):
        global resizeFont
        if resizeFont:
            return True
        if (keycode1 == 45 or keycode1 == 269) and mod_globals.fontSize > 10:
            mod_globals.fontSize = mod_globals.fontSize - 1
            resizeFont = True
            self.stop()
            return True
        if (keycode1 == 61 or keycode1 == 270) and mod_globals.fontSize < 40:
            mod_globals.fontSize = mod_globals.fontSize + 1
            resizeFont = True
            self.stop()
            return True
        if keycode1 == 27:
            exit()
        return False

    def build(self):
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(MyLabel(text='PyDDT', font_size=(fs*3, 'dp'), height=(fs*3, 'dp'), size_hint=(1, None)))
        try:
            self.archive = str(mod_globals.ddtroot).rpartition('/')[2]
        except:
            self.archive = str(mod_globals.ddtroot).rpartition('\\')[2]
        if self.archive == '.' or self.archive == '..': self.archive = 'NOT BASE DDT2000'
        layout.add_widget(MyLabel(text='DB archive : ' + self.archive, font_size=(fs*0.9,  'dp'), multiline=True, size_hint=(1, None)))
        layout.add_widget(Button(text= 'Scan ALL ECUs', id='scan', size_hint=(1, None), on_press=self.scanALLecus, height=(fs * 4,  'dp')))
        self.but_demo = Button(text= 'Open ECUs DEMO', id='demo', size_hint=(1, None), on_press=lambda bt:self.OpenEcu(bt), height=(fs * 4,  'dp'))
        layout.add_widget(self.but_demo)
        layout.add_widget(self.make_savedEcus())
        layout.add_widget(self.in_car())
        layout.add_widget(self.make_bt_device_entry())
        layout.add_widget(self.make_input_toggle('Generate logs', mod_globals.opt_log, 'down' if len(mod_globals.opt_log) > 0 else  'normal'))
        layout.add_widget(self.make_input('Font size', str(mod_globals.fontSize)))
        layout.add_widget(self.make_box_switch('DUMP', mod_globals.opt_dump))
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(layout)
        return root

    def scanALLecus(self, instance):
        self.finish(instance)
        label = Label(text='Not select car')
        popup = Popup(title='ERROR', content=label, size=(400, 400), size_hint=(None, None))
        if mod_globals.opt_car != 'ALL CARS':
            self.stop()
            mod_globals.opt_demo = False
            mod_globals.opt_scan = True
            Clock.schedule_once(mod_ddt.DDTLauncher(mod_globals.opt_car).run(), 1)
        else:
            popup.open()
            return
    
    def OpenEcu(self, instance):
        self.finish(instance.id)
        if instance.id == 'demo': 
            mod_globals.opt_demo = True
        label = Label(text='Not select car or savedCAR')
        popup = Popup(title='ERROR', content=label, size=(400, 400), size_hint=(None, None))
        if mod_globals.opt_car != 'ALL CARS' or mod_globals.savedCAR != 'Select':
            instance.background_color= (0,1,0,1)
            self.stop()
            if mod_globals.opt_demo:
                lbltxt = Label(text='Loading in DEMO', font_size=20)
            elif mod_globals.savedCAR != 'Select':
                lbltxt = Label(text='Loading savedCAR', font_size=20)
            else:
                lbltxt = Label(text='Scanning', font_size=20)
            popup_init = Popup(title='Loading', content=lbltxt, size=(400, 400), size_hint=(None, None))
            base.runTouchApp(slave=True)
            popup_init.open()
            base.EventLoop.idle()
            sys.stdout.flush()
            base.EventLoop.window.remove_widget(popup_init)
            popup_init.dismiss()
            base.stopTouchApp()
            base.EventLoop.window.canvas.clear()
            mod_ddt.DDT_START(mod_globals.opt_car)
        else:
            popup.open()
            return

    def make_savedEcus(self):
        ecus = sorted(glob.glob(os.path.join(mod_globals.user_data_dir, 'savedCAR_*.csv')))
        toggle = Button(text='Load savedCAR', id='open', size_hint=(1, None), height=(fs * 3,  'dp'), on_press=lambda bt:self.OpenEcu(bt))
        self.ecus_dropdown = DropDown(size_hint=(1, None), height=(fs,  'dp'))
        glay = MyGridLayout(cols=2, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        for s_ecus in ecus:
            s_ecus = os.path.split(s_ecus)[1]
            btn= Button(text=s_ecus, size_hint_y=None, height=(fs * 3,  'dp'))
            btn.bind(on_release=lambda btn: self.ecus_dropdown.select(btn.text))
            self.ecus_dropdown.add_widget(btn)
        self.ecusbutton = Button(text='Select', size_hint=(1, None), height=(fs * 3,  'dp'))
        self.ecusbutton.bind(on_release=self.ecus_dropdown.open)
        self.ecus_dropdown.bind(on_select=lambda instance, x: setattr(self.ecusbutton, 'text', x))
        glay.add_widget(toggle)
        glay.add_widget(self.ecusbutton)
        return glay

    def finish(self, instance):
        mod_globals.savedCAR = self.ecusbutton.text
        mod_globals.opt_dump = self.button['DUMP'].active
        if instance == 'demo': mod_globals.opt_demo = True
        else: mod_globals.opt_demo = False
        if self.button['Generate logs'].state == 'down':
            mod_globals.opt_log = 'log.txt' if self.textInput['Generate logs'].text == '' else self.textInput['Generate logs'].text
        else:
            mod_globals.opt_log = ''
        if 'wifi' in self.mainbutton.text.lower():
            mod_globals.opt_port = '192.168.0.10:35000'
        else:
            bt_device = self.mainbutton.text.rsplit('>', 1)
            if mod_globals.os != 'android':
                try:
                    mod_globals.opt_port = bt_device[1]
                except:
                    mod_globals.opt_port = bt_device[0]
            else:
                mod_globals.opt_port = bt_device[0]
            if len(bt_device) > 1:
                mod_globals.opt_dev_address = bt_device[-1]
            mod_globals.bt_dev = self.mainbutton.text
        try:
            mod_globals.fontSize = int(self.textInput['Font size'].text)
        except:
            mod_globals.fontSize = 20
        mod_globals.opt_car = self.carbutton.text
        if mod_globals.opt_car != 'ALL CARS'and mod_globals.savedCAR != 'Select':self.stop()

    def find_in_car(self, ins):
        glay = GridLayout(cols=1, spadding=20, size_hint=(1, 1))
        self.find = TextInput(text='', size_hint=(1, None), height=(fs * 3,  'dp'))
        glay.add_widget(self.find)
        glay.add_widget(Button(text='FIND', size_hint=(0.2, None), height=(fs * 3,  'dp'),on_release=lambda btn: self.popup_in_car(btn.text)))
        self.popup = Popup(title='FIND CAR', content=glay, size=(Window.size[0]*0.8, Window.size[1]*0.5), size_hint=(None, None), auto_dismiss=True)
        self.popup.open()

    def in_car(self):
        avtosd = self.avtos()
        glay = MyGridLayout(cols=3, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        label1 = MyLabel(text='Car', halign='left', size_hint=(1, None), height=(fs * 3,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay.add_widget(label1)
        self.dropdown = DropDown(size_hint=(1, None), height=(fs * 3,  'dp'))
        glay.add_widget(Button(text='FIND', size_hint=(0.5, None), height=(fs * 3,  'dp'), on_press=self.find_in_car))
        for avto in avtosd:
            btn = Button(text=avto, size_hint_y=None, height=(fs * 3,  'dp'))
            btn.bind(on_release=lambda btn: self.popup_in_car(btn.text))
            self.dropdown.add_widget(btn)
        self.carbutton = Button(text='ALL CARS', size_hint=(1, None), height=(fs * 3,  'dp'))
        self.carbutton.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.carbutton, 'text', x))
        glay.add_widget(self.carbutton)
        return glay

    def popup_in_car(self, instance):
        try:
            self.popup.dismiss()
        except:
            pass
        layout = MyGridLayout(cols=1, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        avtosd = self.avtos()
        for key in avtosd:
            if instance == 'FIND':
                for car in avtosd[key]:
                    if self.find.text.lower() in str(car).lower():
                        btn = Button(text=car[3]+' : '+car[4][0], height=(fs * 3,  'dp'), size_hint_y=None)
                        layout.add_widget(btn)
                        btn.bind(on_release=lambda btn: self.press_car(btn.text))
            if key == instance:
                for car in avtosd[key]:
                    btn = Button(text=car[3]+' : '+car[4][0], height=(fs * 3,  'dp'), size_hint_y=None)
                    layout.add_widget(btn)
                    btn.bind(on_release=lambda btn: self.press_car(btn.text))
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,'center_y': 0.5})
        root.add_widget(layout)
        self.popup = Popup(title=instance, content=root, size=(Window.size[0]*0.8, Window.size[1]*0.8), size_hint=(None, None), auto_dismiss=True)
        self.popup.open()

    def press_car(self, btn):
        self.popup.dismiss()
        self.dropdown.select(btn)
        
    def avtos(self):
        self.pl = mod_ddt_utils.ddtProjects()
        for m in self.pl.plist:
            self.ptree[m['name']] = []
            for c in m['list']:
                self.ptree[m['name']].append([m['name'], 'end', c['code'], c['code'], [c['name'],c['segment'],c['addr']]])
        return self.ptree

    def make_box_switch(self, str1, active, callback = None):
        label1 = MyLabel(text=str1, halign='left', size_hint=(1, None), height=(fs * 3,  'dp'))
        sw = Switch(active=active, size_hint=(1, None), height=(fs * 3,  'dp'))
        if callback:
            sw.bind(active=callback)
        self.button[str1] = sw
        label1.bind(size=label1.setter('text_size'))
        glay = MyGridLayout(cols=2, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        glay.add_widget(label1)
        glay.add_widget(sw)
        return glay

    def make_bt_device_entry(self):
        ports = mod_ddt_utils.getPortList()
        label1 = MyLabel(text='ELM port', halign='left', size_hint=(1, None), height=(fs*3,  'dp'))
        self.bt_dropdown = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay = MyGridLayout(cols=2, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        btn = Button(text='WiFi (192.168.0.10:35000)', size_hint_y=None, height=(fs * 3,  'dp'))
        btn.bind(on_release=lambda btn: self.bt_dropdown.select(btn.text))
        self.bt_dropdown.add_widget(btn)
        try:
            porte = ports.iteritems()
        except:
            porte = ports.items()
        for name, address in porte:
            if mod_globals.opt_port == name:
                mod_globals.opt_dev_address = address
            btn = Button(text=name + '>' + address, size_hint_y=None, height=(fs * 3,  'dp'))
            btn.bind(on_release=lambda btn: self.bt_dropdown.select(btn.text))
            self.bt_dropdown.add_widget(btn)
        self.mainbutton = Button(text='Select', size_hint=(1, None), height=(fs * 3,  'dp'))
        self.mainbutton.bind(on_release=self.bt_dropdown.open)
        self.bt_dropdown.bind(on_select=lambda instance, x: setattr(self.mainbutton, 'text', x))
        self.bt_dropdown.select(mod_globals.opt_port)
        glay.add_widget(label1)
        glay.add_widget(self.mainbutton)
        return glay

    def make_input_toggle(self, str1, iText, state):
        toggle = ToggleButton(state=state, text=str1, size_hint=(1, None), height=(fs * 3,  'dp'))
        self.button[str1] = toggle
        ti = TextInput(text=iText, multiline=False, font_size=(fs,  'dp'))
        self.textInput[str1] = ti
        glay = MyGridLayout(cols=2, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        glay.add_widget(toggle)
        glay.add_widget(ti)
        return glay

    def make_input(self, str1, iText):
        label1 = MyLabel(text=str1, halign='left', size_hint=(1, None), height=(fs * 3,  'dp'))
        ti = TextInput(text=iText, multiline=False, font_size=(fs,  'dp'))
        self.textInput[str1] = ti
        glay = MyGridLayout(cols=2, padding=(fs/2,  'dp'), height=(fs * 4,  'dp'), spadding=20, size_hint=(1, None))
        glay.add_widget(label1)
        glay.add_widget(ti)
        return glay

def destroy():
    exit()

def kivyScreenConfig():
    global resizeFont
    if mod_globals.os != 'android':
        height = Window.size[1]*0.85
        width = height/1.3
        Window.size = (width, height)
    Window.bind(on_close=destroy)
    while 1:
        config = PYDDT()
        config.run()
        if not resizeFont:
            return
        resizeFont = False

def main():
    if not os.path.exists(mod_globals.cache_dir):
        os.makedirs(mod_globals.cache_dir)
    if not os.path.exists(mod_globals.log_dir):
        os.makedirs(mod_globals.log_dir)
    if not os.path.exists(mod_globals.dumps_dir):
        os.makedirs(mod_globals.dumps_dir)
    mod_db_manager.find_DBs()
    settings = mod_globals.Settings()
    kivyScreenConfig()
    settings.save()

if __name__ == '__main__':
    main()