# -*- coding: utf-8 -*-
from kivy.config import Config
try:
    from kivy_deps import sdl2, glew
except:
    pass
from kivy.utils import platform
Config.set('kivy', 'exit_on_escape', '0')
if platform != 'android':
    Config.set('graphics', 'position', 'custom')
    Config.set('graphics', 'left', 300)
    Config.set('graphics', 'top',  50)
from kivy.core.window import Window
from kivy.app import App
from mod_ddt import DDT
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy import base

import mod_globals, mod_db_manager, mod_ddt_utils, os, sys

if int(Window.size[1]) > int(Window.size[0]):
    fs = int(Window.size[1])/(int(Window.size[0])/9)
else:
    fs = int(Window.size[0])/(int(Window.size[1])/9)

__all__ = 'install_android'

mod_globals.os = platform

if mod_globals.os != 'android':
    if Window.size[0]>Window.size[1]: ws = Window.size[0]/Window.size[1]*1.2
    else: ws = Window.size[1]/Window.size[0]*1.2
    Window.size = (Window.size[0], Window.size[1]*ws)

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

class MainApp(App):
    
    def __init__(self):
        self.button = {}
        self.textInput = {}
        self.ptree = {}
        self.eculist = mod_ddt_utils.loadECUlist()
        super(MainApp, self).__init__()
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
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text='PyDDT', font_size=(fs*2,  'dp'), height=(fs * 2,  'dp'), size_hint=(1, None)))
        try:
            self.archive = str(mod_globals.ddtroot).rpartition('/')[2]
        except:
            self.archive = str(mod_globals.ddtroot).rpartition('\\')[2]
        if self.archive == '.' or self.archive == '..': self.archive = 'NOT BASE DDT2000'
        layout.add_widget(Label(text='DB archive : ' + self.archive, font_size=(fs*0.9,  'dp'), height=(fs,  'dp'), multiline=True, size_hint=(1, None)))
        layout.add_widget(Button(text= 'Scan all ECUs', size_hint=(1, None), on_press=self.finish, height=(fs * 2,  'dp')))
        layout.add_widget(self.in_car())
        layout.add_widget(self.make_bt_device_entry())
        layout.add_widget(self.make_box_switch('Demo mode', mod_globals.opt_demo))
        layout.add_widget(self.make_box_switch('Generate logs', True if len(mod_globals.opt_log) > 0 else False))
        layout.add_widget(self.make_input('Log name', mod_globals.opt_log))
        layout.add_widget(self.make_input('Font size', str(mod_globals.fontSize)))
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,
         'center_y': 0.5})
        root.add_widget(layout)
        return root

    def finish(self, instance):
        mod_globals.opt_demo = self.button['Demo mode'].active
        if self.button['Generate logs'].active:
            mod_globals.opt_log = 'log.txt' if self.textInput['Log name'].text == '' else self.textInput['Log name'].text
        else:
            mod_globals.opt_log = 'log.txt'
        if 'wifi' in self.mainbutton.text.lower():
            mod_globals.opt_port = '192.168.0.10:35000'
        else:
            bt_device = self.mainbutton.text.split('>')
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
        self.stop()

    def in_car(self):
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        label1 = Label(text='  Car', halign='left', valign='middle', size_hint=(1, None), height=(fs * 2,  'dp'), font_size=(fs,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay.add_widget(label1)
        self.dropdown = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        avtosd = self.avtos()
        for avto in avtosd:
            btn = Button(text=avto, size_hint_y=None, height=(fs * 2,  'dp'))
            btn.bind(on_release=lambda btn: self.popup_in_car(btn.text))
            self.dropdown.add_widget(btn)
        self.carbutton = Button(text='ALL CARS', size_hint=(1, None), height=(fs * 2,  'dp'))
        self.carbutton.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.carbutton, 'text', x))
        glay.add_widget(self.carbutton)
        return glay

    def popup_in_car(self, instance):
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        avtosd = self.avtos()
        for key in avtosd:
            if key == instance:
                for car in avtosd[key]:
                    btn = Button(text=car[3]+' : '+car[4][0], height=(fs * 3,  'dp'), size_hint_y=None)
                    layout.add_widget(btn)
                    btn.bind(on_release=lambda btn: self.press_car(btn.text))
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,'center_y': 0.5})
        root.add_widget(layout)
        self.popup = Popup(title=instance, content=root, size=(Window.size[0], Window.size[1]), size_hint=(None, None), auto_dismiss=True)
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
        
        label1 = Label(text=str1, halign='left', valign='middle', size_hint=(1, None), height=(fs * 2,  'dp'), font_size=(fs,  'dp'))
        sw = Switch(active=active, size_hint=(1, None), height=(fs * 2,  'dp'))
        if callback:
            sw.bind(active=callback)
        self.button[str1] = sw
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        glay.add_widget(label1)
        glay.add_widget(sw)
        return glay

    def make_bt_device_entry(self):
        
        ports = mod_ddt_utils.getPortList()
        label1 = Label(text='ELM port', halign='left', valign='middle', size_hint=(1, None), height=(fs,  'dp'), font_size=(fs,  'dp'))
        self.bt_dropdown = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        btn = Button(text='WiFi (192.168.0.10:35000)', size_hint_y=None, height=(fs * 2,  'dp'))
        btn.bind(on_release=lambda btn: self.bt_dropdown.select(btn.text))
        self.bt_dropdown.add_widget(btn)
        try:
            porte = ports.iteritems()
        except:
            porte = ports.items()
        for name, address in porte:
            if mod_globals.opt_port == name:
                mod_globals.opt_dev_address = address
            btn = Button(text=name + '>' + address, size_hint_y=None, height=(fs * 2,  'dp'))
            btn.bind(on_release=lambda btn: self.bt_dropdown.select(btn.text))
            self.bt_dropdown.add_widget(btn)

        self.mainbutton = Button(text='Select', size_hint=(1, None), height=(fs * 2,  'dp'))
        self.mainbutton.bind(on_release=self.bt_dropdown.open)
        self.bt_dropdown.bind(on_select=lambda instance, x: setattr(self.mainbutton, 'text', x))
        self.bt_dropdown.select(mod_globals.opt_port)
        glay.add_widget(label1)
        glay.add_widget(self.mainbutton)
        return glay

    def make_input(self, str1, iText):
        label1 = Label(text=str1, halign='left', valign='middle', size_hint=(1, None), height=(fs * 3,  'dp'), font_size=(fs,  'dp'))
        ti = TextInput(text=iText, multiline=False, font_size=(fs,  'dp'))
        self.textInput[str1] = ti
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        glay.add_widget(label1)
        glay.add_widget(ti)
        return glay

def destroy():
    exit()

def kivyScreenConfig():
    global resizeFont
    if mod_globals.os != 'android':
        if Window.size[0]>Window.size[1]: ws = Window.size[0]/Window.size[1]*1.2
        else: ws = Window.size[1]/Window.size[0]*1.2
        Window.size = (Window.size[0], Window.size[1])
    
    Window.bind(on_close=destroy)
    while 1:
        config = MainApp()
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
    while 1:
        DDT().start()

if __name__ == '__main__':
    main()