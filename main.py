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
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy import base
from collections import OrderedDict
from mod_utils import pyren_encode
import os, sys
import mod_globals, mod_ddt_utils, mod_db_manager

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
        mod_globals.csv_dir = user_datadir + '/csv/'
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
        self.eculist = mod_ddt_utils.loadECUlist()
        
        Window.bind(on_keyboard=self.key_handler)
        super(MainApp, self).__init__()

    def build(self):
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        layout.add_widget(Label(text='PyDDT', font_size=(fs*2,  'dp'), height=(fs * 2,  'dp'), size_hint=(1, None)))
        
        
        layout.add_widget(self.make_vehicles())
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,
         'center_y': 0.5})
        root.add_widget(layout)
        return root

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

    def make_input(self, str1, iText):
        
        label1 = Label(text=str1, halign='left', valign='middle', size_hint=(1, None), height=(fs * 3,  'dp'), font_size=(fs,  'dp'))
        ti = TextInput(text=iText, multiline=False, font_size=(fs,  'dp'))
        self.textInput[str1] = ti
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        glay.add_widget(label1)
        glay.add_widget(ti)
        return glay

    def changeLangButton(self, buttonText):
        setattr(self.langbutton, 'text', buttonText)
        setattr(self.langbutton, 'background_normal', '')
        setattr(self.langbutton, 'background_color', (0.345,0.345,0.345,1))

    def make_language_entry(self):
        
        langs = mod_zip.get_languages()
        label1 = Label(text='Language', halign='left', valign='middle', size_hint=(1, None), height=(fs * 2,  'dp'), font_size=(fs,  'dp'))
        self.lang_dropdown = DropDown(size_hint=(1, None), height=(fs,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        for lang in sorted(langs):
            btn = Button(text=lang, size_hint_y=None, height=(fs * 2,  'dp'))
            btn.bind(on_release=lambda btn: self.lang_dropdown.select(btn.text))
            self.lang_dropdown.add_widget(btn)

        if mod_globals.opt_lang:
            if (len(mod_globals.opt_lang) > 2 and len(langs[0]) == 2) or (len(mod_globals.opt_lang) == 2 and len(langs[0]) > 2) :
                txt = 'SELECT'
            else:
                txt = mod_globals.opt_lang
        else:
            txt = 'SELECT'
        
        if txt == 'SELECT':
            self.langbutton = Button(text=txt, size_hint=(1, None), height=(fs * 2,  'dp'), background_normal='', background_color=(1,0,0,1))
        else:
            self.langbutton = Button(text=txt, size_hint=(1, None), height=(fs * 2,  'dp'))
        self.langbutton.bind(on_release=self.lang_dropdown.open)
        self.lang_dropdown.bind(on_select=lambda instance, x: self.changeLangButton(x))
        glay.add_widget(label1)
        glay.add_widget(self.langbutton)
        return glay

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

    def make_vehicles(self):
        glay = GridLayout(cols=1, height=(fs * 3,  'dp'), size_hint=(1, None), padding=20, spacing=20)
        vehicles = self.fltBtnClick()
        self.bt_dropdown = DropDown(size_hint=(1, None), dismiss_on_select=True, height=(fs * 2,  'dp'))
        for key in vehicles:
            self.bt_drop = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
            self.mainbut = Button(text=pyren_encode(key), size_hint=(1, None), height=(fs * 2,  'dp'))
            self.mainbut.bind(on_release=self.bt_drop.open)
            self.bt_drop.bind(on_select=lambda instance, x: setattr(self.mainbut, 'text', x))
            
            
            
            for k in vehicles[key]:
                btn = Button(text=vehicles[key][k][4][0], size_hint_y=None, height=(fs * 2,  'dp'))
                self.bt_dropdown.on_dismiss()
                btn.bind(on_release=lambda btn: self.bt_dropdown.select(btn.text))
                self.bt_drop.add_widget(btn)
                '''layout = BoxLayout(orientation='horizontal', spacing=15, size_hint=(1, 1))
                layout.add_widget(Label(text=pyren_encode(vehicles[key][k][2])))
                layout.add_widget(Label(text=pyren_encode(vehicles[key][k][4][0])))
                glay.add_widget(layout)'''
            self.bt_dropdown.add_widget(self.mainbut)
        self.mainbutton = Button(text='Select', size_hint=(1, None), height=(fs * 2,  'dp'))
        self.mainbutton.bind(on_release=self.bt_dropdown.open)
        self.bt_dropdown.bind(on_select=lambda instance, x: setattr(self.mainbutton, 'text', x))
        glay.add_widget(self.mainbutton)
        return glay

    def make_bt_device_entry(self):
        
        ports = get_devices()
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

    def fltBtnClick(self):
        ptree = {}
        for m in mod_ddt_utils.ddtProjects().plist:
            scmParamsDict = {}
            #ptree[m['name']] = []
            for c in m['list']:
                scmParamsDict[c['name']] = [m['name'], 'end', c['code'], c['code'], [c['name'],c['segment'],c['addr']]]
                #ptree[m['name']].append([m['name'], 'end', c['code'], c['code'], [c['name'],c['segment'],c['addr']]])
            ptree[m['name']] = scmParamsDict
        return ptree




if __name__ == '__main__':
    if not os.path.exists(mod_globals.cache_dir):
        os.makedirs(mod_globals.cache_dir)
    if not os.path.exists(mod_globals.log_dir):
        os.makedirs(mod_globals.log_dir)
    if not os.path.exists(mod_globals.dumps_dir):
        os.makedirs(mod_globals.dumps_dir)
    if not os.path.exists(mod_globals.csv_dir):
        os.makedirs(mod_globals.csv_dir)
    mod_db_manager.find_DBs()
    app = MainApp()
    app.run()