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
        self.eculist = mod_ddt_utils.loadECUlist()
        super(MainApp, self).__init__()

    def build(self):
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1.0, None))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text='PyDDT', font_size=(fs*2,  'dp'), height=(fs * 2,  'dp'), size_hint=(1, None)))
        
        layout.add_widget(Button(text= 'start test', size_hint=(1, None), on_press=self.start_test, height=(fs * 2,  'dp')))
       
       
       
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,
         'center_y': 0.5})
        root.add_widget(layout)
        return root

    def start_test(self, dt):
        self.ptree = {}
        self.pl = mod_ddt_utils.ddtProjects()
        layout = GridLayout(cols=1, padding=10, spacing=20, size_hint=(1.0, None))
        self.proj_path = 'vehicles/projects.xml'
        dropdown = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        dropdown_m = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        for m in self.pl.plist:
            self.ptree[m['name']] = []
            btn = Button(text=m['name'], size_hint_y=None, height=(fs * 2,  'dp'))
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

            
            
            #self.ptree.insert('','end',iid=m['name'], text=m['name'], open=True)
            #layout.add_widget(Label (text=m['name'], size_hint=(1, None)))
            for c in m['list']:
                self.ptree[m['name']].append(c['name'])
                #self.ptree.insert(m['name'], 'end', iid = c['code'], text = c['code'], values=[c['name'],c['segment'],c['addr']])
                """#layout.add_widget(Label (text=c['name'], size_hint=(1, None)))
                #self.ptree[m['name']].append((c['name'])) 
                if m['name'] == self.mainbutton:
                    
                    
                    """
                #self.ptree.insert(m['name'], 'end', iid = c['code'], text = c['code'], values=[c['name'],c['segment'],c['addr']])
        
        
        self.mainbutton = Button(text='Select', size_hint=(1, None), height=(fs * 2,  'dp'))
        self.mainbutton.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(self.mainbutton, 'text', x))
        
        btn_m = Button(text=str(filter(lambda x: self.mainbutton.text == 'RENAULT', self.ptree)), size_hint_y=None, height=(fs * 2,  'dp'))
        btn_m.bind(on_release=lambda btn_m: dropdown_m.select(btn_m.text))
        dropdown_m.add_widget(btn_m)
        """for key in self.ptree:
            
            
            if key == (self.mainbutton.text = lambda self.mainbutton.text: (self.mainbutton.text)) :
                btn_m = Button(text=key, size_hint_y=None, height=(fs * 2,  'dp'))
                btn_m.bind(on_release=lambda btn_m: dropdown_m.select(btn_m.text))
                dropdown_m.add_widget(btn_m)"""
            
        self.mainbutton_m = Button(text='Select', size_hint=(1, None), height=(fs * 2,  'dp'))
        self.mainbutton_m.bind(on_release=dropdown_m.open)
        dropdown_m.bind(on_select=lambda instance, x: setattr(self.mainbutton_m, 'text', x, clear_widgets()))
        layout.add_widget(self.mainbutton)
        layout.add_widget(self.mainbutton_m)
        
        layout.add_widget(Label (text='test', size_hint=(1, None)))
        root = ScrollView(size_hint=(1, 1), do_scroll_x=False, pos_hint={'center_x': 0.5,
         'center_y': 0.5})
        root.add_widget(layout)
        popup_load = Popup(title='test', content=root, size=(500, 500), size_hint=(None, None), auto_dismiss=True)
        popup_load.open()

    def make_bt_device_entry(self):
        
        
        label1 = Label(text='Chosse avto', halign='left', valign='middle', size_hint=(1, None), height=(fs,  'dp'), font_size=(fs,  'dp'))
        """self.bt_dropdown = DropDown(size_hint=(1, None), height=(fs * 2,  'dp'))
        label1.bind(size=label1.setter('text_size'))
        glay = GridLayout(cols=2, height=(fs * 3,  'dp'), size_hint=(1, None), padding=10, spacing=10)
        
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
        return glay"""

if __name__ == '__main__':
    if not os.path.exists(mod_globals.cache_dir):
        os.makedirs(mod_globals.cache_dir)
    if not os.path.exists(mod_globals.log_dir):
        os.makedirs(mod_globals.log_dir)
    if not os.path.exists(mod_globals.dumps_dir):
        os.makedirs(mod_globals.dumps_dir)
    mod_db_manager.find_DBs()
    app = MainApp()
    app.run()