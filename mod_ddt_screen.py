# -*- coding: utf-8 -*-
try:
    from kivy_deps import sdl2, glew
except:
    pass
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.scatter import Scatter
from kivy.uix.scatterlayout import ScatterLayout
import gc, os, sys, datetime, copy, time
import mod_db_manager, mod_globals
import xml.etree.ElementTree as et
from mod_utils import *
from mod_elm import AllowedList
from mod_elm import dnat
from functools import partial
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
fmn = 1.7
bmn = 2.5

class MyScatterLayout(ScatterLayout):
    def __init__(self, **kwargs):
        super(MyScatterLayout, self).__init__(**kwargs)
        if 'bgcolor' in kwargs:
            self.bgcolor = kwargs['bgcolor']
        else:
            self.bgcolor =(0, 0, 0, 0)
        with self.canvas.before:
            Color(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
            Rectangle(pos=self.pos, size=self.size)
    
class MyButton(Button):
    def __init__(self, **kwargs):
        super(MyButton, self).__init__(**kwargs)
        self.bind(size=self.setter('text_size'))
        if 'halign' not in kwargs:
            self.halign = 'center'
        if 'valign' not in kwargs:
            self.valign = 'middle'
        if 'size_hint' not in kwargs:
            self.size_hint =(1, 1)

class MyLabel(Label):
    def __init__(self, **kwargs):
        if 'bgcolor' in kwargs:
            self.bgcolor = kwargs['bgcolor']
        else:
            self.bgcolor =(0, 0, 0, 0)
        super(MyLabel, self).__init__(**kwargs)
        self.bind(size=self.setter('text_size'))
        if 'halign' not in kwargs:
            self.halign = 'center'
        if 'valign' not in kwargs:
            self.valign = 'middle'
        if 'height' not in kwargs:
            self.height = self.size[1]*1.1
        if 'size' in kwargs:
            self.size[0] = self.size[0]+4
        if 'pos' in kwargs:
            self.pos[0] = self.pos[0]+4
    def on_size(self, *args):
        if not self.canvas:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 1)
            Rectangle(pos=(self.pos[0]-4, self.pos[1]), size=(self.size[0], self.size[1]*1.1))
        with self.canvas.before:
            Color(self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
            Rectangle(pos=(self.pos[0], self.pos[1]+4), size=(self.size[0]-8,self.size[1]*1.1-8))
            
class MyLabelBlue(Label):
    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 1, 0, 0.25)
            Rectangle(pos=self.pos, size=self.size)
            

class MyLabelGreen(Label):
    def __init__(self, mfs = None, **kwargs):
        super(MyLabelGreen, self).__init__(**kwargs)
        self.text_size = self.size
        self.bind(size=self.on_size)
    def on_size(self, widget, size):
        self.text_size =(size[0], None)
        self.texture_update()
        if self.size_hint_y is None and self.size_hint_x is not None:
            self.height = fs * fmn
        elif self.size_hint_x is None and self.size_hint_y is not None:
            self.width = self.texture_size[0]
        self.toNormal()
    def toNormal(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 1, 0.25)
            Rectangle(pos=self.pos, size=self.size)

class screenSettings():
    geometry = ''
    scf = 1.0
i = 0
class DDTScreen():
    
    tl = 0
    updatePeriod = 50
    decu = None
    xmlName = ''
    Screens = {}
    dDisplay = {}
    dValue = {}  # display value indexed by DataName
    iValue = {}  # input   value indexed by DataName
    iValueNeedUpdate = {}
    dReq = {}  # request names
    sReq_dl = {}  # delays for requests sent thru starting the screen
    sReq_lst = []  # list of requests sent thru starting the screen(order is important)
    dBtnSend = {}
    dFrames = []
    dObj = []  # objects for place_forget
    tObj = {}  # objects for text captions
    start = True
    jid = None
    firstResize = False
    jdsu = None
    firstResize = False
    prefer_ECU = True  # type would be changed
    
    currentscreen = None
    
    scf = 1.0  # font scale factor
    
    def __init__(self, ddtFileName, xdoc, decu, top = False):
        global fs
        fs = mod_globals.fontSize
        mod_globals.opt_exp = True
        self.Screens = {}
        self.screens = {}
        self.catnames = []
        self.scf = 8
        
        self.blue_part_size = 0.75
        self.scrnames = []
        self.Labels = {}
        self.xmlName = ddtFileName
        self.xdoc = xdoc
        self.decu = decu
        self.decu.screen = self
        self.winfo_height = int(Window.size[1]*0.9)
        self.winfo_width = int(Window.size[0])
        Window.bind(on_keyboard=self.key_handler)
        self.approve = True
        self.needupdate = False
        clearScreen ()
        self.decu.clearELMcache()
        self.initUI()
        self.decu.initRotary()
        len_screen = len(self.Screens)*2
        self.startStopButton = Button(text='', size_hint=(1, 1))
        self.boxs = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1.0, None))
        self.boxs.bind(minimum_height=self.boxs.setter('height'))
        self.box1 = BoxLayout(orientation='horizontal', size_hint=(1, None))
        for x in self.catnames:
            self.button = MyButton(text=x, id=x, on_press=self.OnScreenChange, size_hint=(1, None), height=fs*4)
            self.boxs.add_widget(self.button)
        self.boxs.add_widget(Button(text='EXIT', size_hint=(1, None), on_press=self.exit))
        
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(self.boxs)
        self.popup_select_screen = Popup(title=self.xmlName, title_align='center', content=root, size=(Window.size[0], Window.size[1]), size_hint=(None, None))
        self.popup_select_screen.open()

    def key_handler(self, window, keycode1, keycode2, text, modifiers):
        global resizeFont
        if resizeFont:
            return True
        if keycode1 == 45 and mod_globals.fontSize > 10:
            mod_globals.fontSize = mod_globals.fontSize - 1
            resizeFont = True
            if self.clock_event is not None:
                self.clock_event.cancel()
            self.needupdate = False
            self.running = False
            self.stop()
            return True
        if keycode1 == 61 and mod_globals.fontSize < 40:
            mod_globals.fontSize = mod_globals.fontSize + 1
            resizeFont = True
            if self.clock_event is not None:
                self.clock_event.cancel()
            self.needupdate = False
            self.running = False
            self.stop()
            return True
        return False


    def __del__(self):
        try:
            self.exit()
            gc.collect()
        except:
            pass

    def close_EXIT(self, dt):
        self.popup_select_screen.dismiss()
        self.exit()

    def show_box(self):
        glay = BoxLayout(orientation='vertical', size_hint=(1, None), height=fs * 2.0)
        label2 = MyLabelBlue(text='val', halign='right', valign='top', size_hint=(1 - self.blue_part_size, 1), font_size=fs)
        glay.add_widget(label2)
        return glay

    def close_Screen(self, dt):
        self.popup.dismiss()
        self.startStop()
        self.start = False
        self.decu.rotaryRunAlloved.clear()
        self.jid = ''

    def select_option(self, bt, i):
        self.dropdowns[i].dismiss()
        self.Labels[i].text = bt
        self.triggers[i].text = bt

    def open_Screen(self):
        if self.start:
            self.jid = Clock.schedule_once(self.updateScreen, 0.2)
            self.decu.rotaryRunAlloved.set()
        self.startStopButton = MyButton(text='STOP', size_hint=(1, 1))
        self.winfo_width, self.winfo_height = self.size_screen
        layout = GridLayout(cols=1, padding=10, spacing=10, size_hint=(None, None), size=(Window.size[0], Window.size[1]*0.9))
        layout3 = GridLayout(cols=1, size_hint=(1, None))
        box = GridLayout(cols=2, size_hint=(1, None), height=fs*3)
        box.add_widget(self.startStopButton)
        self.startStopButton.bind(on_release=lambda args:self.startStop())
        box.add_widget(MyButton(text='CLOSE', size_hint=(1, 1), on_press=self.close_Screen))
        layout.add_widget(box)
        
        self.dropdowns = {}
        self.triggers = {}
        flayout = MyScatterLayout(size_hint=(None, None), bgcolor=self.scr_c, size=(self.winfo_width, self.winfo_height), do_rotation=False )
        if self.ddt_label:
            for i in self.ddt_label:
                if i == 'New label': continue
                label = MyLabel(text=i, id=i, color=self.LddtColor[i]['xfcolor'], bold=self.ddt_fontL[i]['bold'], italic=self.ddt_fontL[i]['italic'], font_size=int(self.ddt_fontL[i]['size']), valign=self.ddt_fontL[i]['anchor'], bgcolor=self.LddtColor[i]['xcolor'], size_hint=(None, None), size=(self.ddt_label[i]['width'], self.ddt_label[i]['height']/1.1), pos=(self.ddt_label[i]['left'], self.winfo_height-self.ddt_label[i]['top']))
                flayout.add_widget(label)
        if self.ddt_inputs:
            for i in self.ddt_inputs:
                if self.ddt_inputs[i]['xw'] > 40:
                    label = MyLabel(text=i, id=i, valign=self.ddt_fontI[i]['anchor'], color=self.IddtColor[i]['xfcolor'], bold=self.ddt_fontI[i]['bold'], italic=self.ddt_fontI[i]['italic'], halign='left', font_size=int(self.ddt_fontI[i]['size']), bgcolor=self.IddtColor[i]['xcolor'], size_hint=(None, None), size=(self.ddt_inputs[i]['width'], self.ddt_inputs[i]['height']/1.1), pos=(self.ddt_inputs[i]['left'], self.winfo_height-self.ddt_inputs[i]['top']))
                    flayout.add_widget(label)
                if i in self.ListOption.keys():
                    self.dropdowns[i] = DropDown()
                    for o in self.ListOption[i]:
                        btn = Button(text=o, id=o, font_size=int(self.ddt_fontI[i]['size']), size_hint_y=None, height=self.ddt_inputs[i]['height'])
                        btn.bind(on_release=lambda btn=btn, i=i: self.select_option(btn.text, i))
                        self.dropdowns[i].add_widget(btn)
                    self.triggers[i] = Button(text='None', id=i, size_hint=(None, None), font_size=int(self.ddt_fontI[i]['size']), size=(self.ddt_inputs[i]['widthV'], self.ddt_inputs[i]['height']), pos=(self.ddt_inputs[i]['leftV'], self.winfo_height-self.ddt_inputs[i]['top']))
                    self.triggers[i].bind(on_release=self.dropdowns[i].open)
                    self.Labels[i] = self.triggers[i]
                    self.dropdowns[i].bind(on_select=lambda instance, x: setattr(self.triggers[i], 'text', x))
                    flayout.add_widget(self.triggers[i])
                elif self.iValue[i] == 'Enter here':
                    label_IT = TextInput(text=self.iValue[i], valign=self.ddt_fontI[i]['anchor'], color=self.IddtColor[i]['xfcolor'], bgcolor=(0, 1, 0, 1), bold=self.ddt_fontI[i]['bold'], italic=self.ddt_fontI[i]['italic'], font_size=int(self.ddt_fontI[i]['size']), size_hint=(None, None), size=(self.ddt_inputs[i]['widthV'], self.ddt_inputs[i]['height']), pos=(self.ddt_inputs[i]['leftV'], self.winfo_height-self.ddt_inputs[i]['top']))
                    self.Labels[i] = label_IT
                    flayout.add_widget(label_IT)
                else:
                    label_I = MyLabel(text=self.iValue[i], valign=self.ddt_fontI[i]['anchor'], color=self.IddtColor[i]['xfcolor'], bgcolor=(0, 1, 0, 1), bold=self.ddt_fontI[i]['bold'], italic=self.ddt_fontI[i]['italic'], font_size=int(self.ddt_fontI[i]['size']), size_hint=(None, None), size=(self.ddt_inputs[i]['widthV'], self.ddt_inputs[i]['height']), pos=(self.ddt_inputs[i]['leftV'], self.winfo_height-self.ddt_inputs[i]['top']))
                    self.Labels[i] = label_I
                    flayout.add_widget(label_I)
                self.needupdate = True

        if self.ddt_button:
            for i in self.ddt_button:
                button = Button(text=self.ddt_button[i]['name'], valign=self.ddt_fontB[i]['anchor'], id=i, color=self.BddtColor[i]['xfcolor'], bold=self.ddt_fontB[i]['bold'], italic=self.ddt_fontB[i]['italic'], font_size=int(self.ddt_fontB[i]['size']), size_hint=(None, None), size=(self.ddt_button[i]['width'], self.ddt_button[i]['height']), pos=(self.ddt_button[i]['left'], self.winfo_height-self.ddt_button[i]['top']))
                button.bind(on_release = lambda btn=self.ddt_button[i]['name'], key=i: self.buttonPressed(btn.text, btn.id))
                flayout.add_widget(button)

        if self.ddt_dispalys:
            for i in self.ddt_dispalys:
                if self.ddt_dispalys[i]['xw'] > 40:
                    label = MyLabel(text=i, id=i, valign=self.ddt_fontD[i]['anchor'], color=self.DddtColor[i]['xfcolor'], bold=self.ddt_fontD[i]['bold'], italic=self.ddt_fontD[i]['italic'], font_size=int(self.ddt_fontD[i]['size']), halign='left', bgcolor=self.DddtColor[i]['xcolor'], size_hint=(None, None), size=(self.ddt_dispalys[i]['width'], self.ddt_dispalys[i]['height']), pos=(self.ddt_dispalys[i]['left'], self.winfo_height-self.ddt_dispalys[i]['top']))
                    flayout.add_widget(label)
                label_D = MyLabel(text=self.dValue[i], valign=self.ddt_fontD[i]['anchor'], bgcolor=(0, 1, 0, 1), color=self.DddtColor[i]['xfcolor'], bold=self.ddt_fontD[i]['bold'], italic=self.ddt_fontD[i]['italic'], font_size=int(self.ddt_fontD[i]['size']), size_hint=(None, None), size=(self.ddt_dispalys[i]['widthV'], self.ddt_dispalys[i]['height']), pos=(self.ddt_dispalys[i]['leftV'], self.winfo_height-self.ddt_dispalys[i]['top']))
                self.Labels[i] = label_D
                flayout.add_widget(label_D)
                self.needupdate = True
        layout3.add_widget(flayout)
        layout.add_widget(layout3)
        self.popup = Popup(title=self.xmlName, content=layout, size=(Window.size[0], Window.size[1]), size_hint=(None, None))
        self.popup.open()

    def chang_zoom(self, dt):
        self.popup.dismiss()
        self.scf = self.scf + dt
        self.loadScreen(self.currentscreen)

    def ButtonConfirmation(self, text, data=None):
        
        layout = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1, 1))
        box1 = BoxLayout(orientation='vertical', size_hint=(1, 0.8), height=fs * 2.0)
        box2 = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), height=fs * 2.0)
        button1 = Button(text='YES')
        if not 'ERROR' in text: box2.add_widget(button1)
        button2 = Button(text='NO')
        box2.add_widget(button2)
        layout.add_widget(MyLabel(text=text))
        layout.add_widget(box1)
        layout.add_widget(box2)
        root = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height))
        root.add_widget(layout)
        self.popup_confirm = Popup(title='Please confirm', content=root, size=(Window.size[0]*0.8, Window.size[1]*0.8), size_hint=(None, None))
        self.popup_confirm.open()
        button1.bind(on_release=lambda args:self.yes(data))
        button2.bind(on_release=self.no)

    def yes(self, slist):
        self.popup_confirm.dismiss()
        confirmed = True
        if confirmed:
            for c in slist:
                r = c['r']
                rsp = '00'
                if mod_globals.opt_exp:
                    rsp = self.decu.elmRequest (c['c'], c['d'], cache=False)
                else:
                    rsp = r.ReplyBytes.replace (' ', '')
                    rsp = ' '.join (a + b for a, b in zip (rsp[::2], rsp[1::2]))
                if len (r.ReceivedDI.keys ()):
                    for d in r.ReceivedDI.keys ():
                        val = self.decu.getValue (d, False, r, rsp)
                        if d in self.dValue.keys ():
                            if ':' in val:
                                self.dValue[d] = val.split (':')[1]
                            else:
                                self.dValue[d] = val
                        if d in self.iValue.keys ():
                            if len (self.decu.datas[d].List) or self.decu.datas[d].BytesASCII or self.decu.datas[d].Scaled:
                                self.iValue[d] = val
                            else:
                                val = self.decu.getHex (d, False, r, rsp)
                                if val != mod_globals.none_val:
                                    val = '0x' + val
                                self.iValue[d] = val
                            self.iValueNeedUpdate[d] = False
        self.update_dInputs()
        if self.start:
            self.jid = Clock.schedule_once(self.updateScreen, 0.2)
            self.decu.rotaryRunAlloved.set()

    def buttonPressed(self, btn, key):
        layout = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1, 1))
        self.decu.rotaryRunAlloved.clear()
        
        if self.jid is not None:
            self.jid = ''
        self.decu.rotaryRunAlloved.clear()

        self.decu.clearELMcache ()
        
        if key in self.dBtnSend.keys():
            sends = self.dBtnSend[key]
        else:
            return
        slist = []
        smap = {}
        error = False
        for i in self.iValue.keys():
            if i in self.Labels:
                self.iValue[i] = self.Labels[i].text
        for send in sends:
            delay = send['Delay']
            requestName = send['RequestName']
            r = self.decu.requests[requestName]
            sendCmd = self.decu.packValues (requestName, self.iValue)
            if 'ERROR' in sendCmd:
                self.ButtonConfirmation(sendCmd)
                return
            smap['d'] = delay
            smap['c'] = sendCmd
            smap['r'] = r
            slist.append (copy.deepcopy (smap))
        if self.approve:
            commandSet = '\n\n'
            for c in slist:
                commandSet += "%-10s Delay:%-3s (%s)\n" % (c['c'], c['d'], c['r'].Name)
            self.ButtonConfirmation(commandSet, slist)
   
    def updateScreen(self, dt=None):
        if self.decu:
            self.decu.rotaryRunAlloved
        else:
            return
        if self.decu.rotaryCommandsQueue.empty():
            for r in self.dReq.keys():
                if self.dReq[r]:continue
                req = self.decu.requests[r].SentBytes
                if(req[:2] not in AllowedList) and not mod_globals.opt_exp:
                    tmstr = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    continue
                self.decu.putToRotary(req)
        tb = time.time()
        while not self.decu.rotaryResultsQueue.empty():
            if time.time()-tb > 0.1:
                break
            (req,rsp) = self.decu.rotaryResultsQueue.get_nowait()
            self.updateScreenValues(req,rsp)
        self.jid = Clock.schedule_once(self.updateScreen, 0.2)
        tb = time.time()
        self.tl = tb

    def updateScreenValues(self, req, rsp ):
        if req is None or rsp is None:
            return
        request_list = []
        if self.decu.req4sent[req] in self.decu.requests.keys():
            r = self.decu.requests[self.decu.req4sent[req]]
            for k in self.decu.requests.keys():
                if self.decu.requests[k].SentBytes == req:
                    request_list.append(self.decu.requests[k])
        else:
            return
        for request in request_list:
            if(any(key in request.ReceivedDI.keys() for key in self.dValue.keys()) or 
                any(key in request.ReceivedDI.keys() for key in self.iValue.keys())):
                r = request
        tmstr = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        for d in r.ReceivedDI.keys():
            if d not in self.dValue.keys() and d not in self.iValue.keys():continue
            val = self.decu.getValue(d)
            if d in self.dValue.keys():
                if ':' in val:
                    self.Labels[d].text=(val.split(':')[1])
                else:
                    self.Labels[d].text=(val)
            if d in self.iValue.keys() and self.iValueNeedUpdate[d]:
                if self.prefer_ECU:
                    if len(self.decu.datas[d].List) or self.decu.datas[d].BytesASCII or self.decu.datas[d].Scaled:
                        self.Labels[d].text =(val)
                    else:
                        val = self.decu.getHex(d)
                        if val!=mod_globals.none_val:
                            val = '0x' + val
                        self.Labels[d].text =(val)
                else:
                    cmd = self.decu.cmd4data[d]
                    val = self.decu.getValue(d, request=self.decu.requests[cmd],
                                             responce=self.decu.requests[cmd].SentBytes)
                    if len(self.decu.datas[d].List) or self.decu.datas[d].BytesASCII or self.decu.datas[d].Scaled:
                        self.Labels[d].text =(val)
                    else:
                        val = self.decu.getHex(d, request=self.decu.requests[cmd],
                                               responce=self.decu.requests[cmd].SentBytes)
                        if val!=mod_globals.none_val:
                            val = '0x' + val
                        self.Labels[d].text =(val)
                self.iValueNeedUpdate[d] = False

    def update_dInputs(self):
        for i in self.iValueNeedUpdate.keys():
            self.iValueNeedUpdate[i] = True

    def make_box_params(self, parameter_name, val):
        glay = BoxLayout(orientation='horizontal', size_hint=(1, None), height=fs * 2.0)
        label1 = MyLabelGreen(text=parameter_name, halign='left', valign='top', size_hint=(self.blue_part_size, None), font_size=fs)
        label2 = MyLabelBlue(text=val, halign='right', valign='top', size_hint=(1 - self.blue_part_size, 1), font_size=fs)
        glay.add_widget(label1)
        glay.add_widget(label2)
        self.Labels[parameter_name] = label2
        return glay

    def OnScreenChange(self, item):
        self.box = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1.0, None))
        self.box.bind(minimum_height=self.box.setter('height'))
        for a in self.screens[item.id]:
            self.button = Button(text=a, id=a, on_press=lambda bt:self.loadScreen(bt.id), size_hint=(1, None), height=fs*4)
            self.box.add_widget(self.button)
        self.box.add_widget(Button(text='CLOSE', size_hint=(1, None), font_size=fs, on_press=self.close_OnScreenChange))
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(self.box)
        self.popup_screen = Popup(title=item.id, title_align='center', content=root, size=(Window.size[0]*0.9, Window.size[1]*0.9), size_hint=(None, None))
        self.popup_screen.open()

    def close_OnScreenChange(self, dt):
        self.popup_screen.dismiss()

    def no(self, instance):
        self.popup_confirm.dismiss()
        return False

    def ButtonConfirmationDialog(self, bt, title=None, content=None):
        if not title:
            title = 'Info'
        box = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1.0, None))
        label = MyLabel(text='Info')
        box.add_widget(label)
        if content:
            label.text = content
        b = BoxLayout(orientation='horizontal')
        b.add_widget(MyButton(text='YES'))
        b.add_widget(MyButton(text='NO', on_press=lambda args:self.confirm_popup.dismiss()))
        box.add_widget(b)
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(box)
        self.confirm_popup = Popup(title=title, content=root, size_hint=(None, None), size=(Window.size[0], Window.size[1]*0.6))
        self.confirm_popup.open()

    def exit(self, td):
        del(self.decu)
        self.popup_select_screen.dismiss()
        if self.decu is not None:
            self.decu.rotaryRunAlloved.clear()
            self.decu.rotaryTerminate.set()
        if self.jid is not None:
            self.jid = None
        if self.jdsu is not None:
            self.jdsu = None
        try:
            if self.translated is not None: del(self.translated)
        except:
            pass
        try:
            if self.expertmode is not None: del(self.expertmode)
        except:
            pass
        try:
            if self.approve is not None: del(self.approve)
        except:
            pass
        try:
            if self.prefer_ECU is not None: del(self.prefer_ECU)
        except:
            pass
        try:
            if self.Screens is not None: del(self.Screens)
        except:
            pass
        try:
            if self.dDisplay is not None: del(self.dDisplay)
        except:
            pass
        try:
            if self.dValue is not None: del(self.dValue)
        except:
            pass
        try:
            if self.iValue is not None: del(self.iValue)
        except:
            pass
        try:
            if self.iValueNeedUpdate is not None: del(self.iValueNeedUpdate)
        except:
            pass
        try:
            if self.dReq is not None: del(self.dReq)
        except:
            pass
        try:
            if self.sReq_dl is not None: del(self.sReq_dl)
        except:
            pass
        try:
            if self.sReq_lst is not None: del(self.sReq_lst)
        except:
            pass
        try:
            if self.dBtnSend is not None: del(self.dBtnSend)
        except:
            pass
        try:
            if self.dFrames is not None: del(self.dFrames)
        except:
            pass
        try:
            if self.dObj is not None: del(self.dObj)
        except:
            pass
        try:
            if self.tObj is not None: del(self.tObj)
        except:
            pass
        try:
            if self.images is not None: del(self.images)
        except:
            pass

    def hex_to_rgb(self, hex_string):
        hex_string = hex(int(hex_string)).split('x')[-1]
        if hex_string == '0': return 0.0, 0.0, 0.0, 1.0
        while len(hex_string)<6: hex_string = '0'+hex_string
        try:
            r_hex = int(hex_string[0:2], 16)/255.0
        except:
            r_hex = 0
        try:
            g_hex = int(hex_string[2:4], 16)/255.0
        except:
            g_hex = 0
        try:
            b_hex = int(hex_string[4:6], 16)/255.0
        except:
            b_hex = 0
        return r_hex, g_hex, b_hex, 1.0

    def saveDump(self):
        self.decu.saveDump ()

    def loadDump(self, fname):
        self.decu.loadDump (fname)
        self.decu.clearELMcache ()
        self.update_dInputs ()

    def startStop(self):
        if self.start:
            self.start = False
            self.startStopButton.text = 'START'
            if self.jid is not None:
                self.jid = ''
            self.decu.rotaryRunAlloved.clear()
        else:
            self.start = True
            self.startStopButton.text = 'STOP'
            self.decu.rotaryRunAlloved.set()
            self.jid = Clock.schedule_once(self.updateScreen, 0.2)

    def initUI(self):
        screenTitle = self.xmlName
        categs = self.xdoc.findall("ns0:Target/ns1:Categories/ns1:Category", mod_globals.ns)
        if len(categs):
            for cat in categs:
                catname = cat.attrib["Name"]
                self.scrnames.append(catname)
                self.catnames.append(catname)
                self.screens[catname] = []
                screens = cat.findall("ns1:Screen", mod_globals.ns)
                if len(screens):
                    for scr in screens:
                        scrname = scr.attrib["Name"]
                        self.scrnames.append(scrname)
                        self.screens[catname].append(scrname)
                        self.Screens[scrname] = scr
        categs = self.xdoc.findall("ns0:Target/ns1:Categories/ns1:Category", mod_globals.ns)
        if len(categs):
            for cat in categs:
                catname = cat.attrib["Name"]
                screens = cat.findall("ns1:Screen", mod_globals.ns)
                if len(screens):
                    for scr in screens:
                        scrname = scr.attrib["Name"]
                        iid = 'I'+str(self.scrnames.index(scrname)).zfill(3)
                        self.Screens[iid] = scr
        self.screens['ddt_all_commands'] = []
        self.catnames.append('ddt_all_commands')
        for req in sorted(self.decu.requests.keys()):
            if self.decu.requests[req].SentBytes[:2] in ['21','22']:
                self.screens['ddt_all_commands'].append(req)
                self.scrnames.append(req)
                iid = 'I'+str(len(self.scrnames)).zfill(3)
                self.Screens[iid] = req

    def minInputHeight(self, scr):
        _minInputHeight = 0xffff
        inputs = scr.findall("ns1:Input", mod_globals.ns)
        if len(inputs):
            for input in inputs:
                xRect = input.findall("ns1:Rectangle", mod_globals.ns)[0]
                if len(xRect):
                    xrHeight = int(xRect.attrib["Height"])
                    if xrHeight < _minInputHeight:
                        _minInputHeight = xrHeight
        return _minInputHeight

    def minButtonHeight(self, scr):
        _minButtonHeight = 0xffff
        inputs = scr.findall("ns1:Button", mod_globals.ns)
        if len(inputs):
            for input in inputs:
                xRect = input.findall("ns1:Rectangle", mod_globals.ns)[0]
                if len(xRect):
                    xrHeight = int(xRect.attrib["Height"])
                    if xrHeight < _minButtonHeight:
                        _minButtonHeight = xrHeight
        return _minButtonHeight

    def startScreen(self):
        self.decu.rotaryRunAlloved.set()
        for r in self.sReq_lst:
            req = self.decu.requests[r].SentBytes
            if (req[:2] not in ['10'] + AllowedList) and not mod_globals.opt_exp:
                print 'Request:' + req + ' rejected due to non expert mode'
                continue
            self.decu.putToRotary(req)


    def loadScreen(self, scr):
        print
        ns = mod_globals.ns
        if scr in self.Screens.keys():
            scr = self.Screens[scr]
        self.currentscreen = scr
        if type(scr) is str or type(scr) is unicode:
            self.loadSyntheticScreen(scr)
            return
        self.firstResize = True
        
        scr_w = int(scr.attrib["Width"])
        scr_h = int(scr.attrib["Height"])
        self.scr_c = self.hex_to_rgb(int(scr.attrib["Color"]))
        self.winfo_height = self.winfo_height * self.scf
        self.winfo_width = self.winfo_width * self.scf
        bg_color = scr.attrib["Color"]
        scx = 1*self.scf  # scale X
        scy = 1*self.scf  # scale Y
        max_x = 0.0
        max_y = 0.0
        recs = scr.findall("*/ns1:Rectangle", ns)
        for rec in recs:
            xrLeft = int(rec.attrib["Left"])
            xrTop = int(rec.attrib["Top"])
            xrHeight = int(rec.attrib["Height"])
            xrWidth = int(rec.attrib["Width"])
            w = xrLeft + xrWidth
            h = xrTop + xrHeight
            if w > max_x and w < scr_w * 3:
                max_x = w
            if h > max_y and h < scr_h * 3:
                max_y = h

        self.dValue = {}
        self.iValue = {}
        self.iValueNeedUpdate = {}
        self.dReq = {}
        self.sReq_dl = {}
        self.sReq_lst = []
        self.dDisplay = {}
        self.dObj = []
        self.tObj = {}
        self.dFrames = []
        self.images = []
        self.ListOption = {}

        self.ddt_fontL = {}
        self.ddt_fontD = {}
        self.ddt_fontI = {}
        self.ddt_fontB = {}
        self.ddt_label = {}
        self.ddt_dispalys = {}
        self.ddt_dispalys_val = {}
        self.ddt_button = {}
        self.ddt_inputs = {}

        self.BddtColor = {}
        self.DddtColor = {}
        self.LddtColor = {}
        self.IddtColor = {}
        
        #scx = int(max_x / self.winfo_width+1)
        #scy = int(max_y / self.winfo_height+1)
        
        _minInputHeight = int(self.minInputHeight(scr)) / 25
        _minButtonHeight = int(self.minButtonHeight(scr)) / 25
        h = 0
        w = 0

        if _minInputHeight == 0: _minInputHeight = 10
        if _minButtonHeight == 0: _minButtonHeight = 20
        #scx = min([scx, 20])
        #scy = min([scy, _minInputHeight, _minButtonHeight, 10])
        self.size_screen = (max_x / scx, max_y / scy)

        labels = scr.findall("ns1:Label", ns)
        if len(labels):
            slab = []
            for label in labels:
                xRect_ = label.findall("ns1:Rectangle", ns)
                if len(xRect_):
                    xRect = xRect_[0]
                    xrHeight = int(xRect.attrib["Height"]) / scy
                    xrWidth = int(xRect.attrib["Width"]) / scx
                else:
                    xrHeight = 1
                    xrWidth = 1
                sq = xrHeight * xrWidth
                sl = {}
                sl['sq'] = sq
                sl['lb'] = label
                slab.append(sl)
            for lab in sorted(slab, key=lambda k: k['sq'], reverse=True):
                label = lab['lb']
                xText = label.attrib["Text"]
                xColor = label.attrib["Color"]
                xAlignment = label.attrib["Alignment"]
                xRect = label.findall("ns1:Rectangle", ns)
                if len(xRect):
                    xRect = xRect[0]
                    xrLeft = int(xRect.attrib["Left"]) / scx
                    xrTop = int(xRect.attrib["Top"]) / scy
                    xrHeight = int(xRect.attrib["Height"]) / scy
                    xrWidth = int(xRect.attrib["Width"]) / scx
                xFont = label.findall("ns1:Font", ns)
                if len(xFont):
                    xFont = xFont[0]
                    xfName = xFont.attrib["Name"]
                    xfSize = xFont.attrib["Size"]
                    xfBold = xFont.attrib["Bold"]
                    xfItalic = xFont.attrib["Italic"]
                    xfColor = xFont.attrib["Color"]
                self.ddt_label[xText] = dict(left=xrLeft, top=xrHeight+xrTop, width=xrWidth, height=xrHeight)

                if '::pic:' not in xText or not mod_db_manager.path_in_ddt('graphics'):
                    self.LddtColor[xText] = dict(xcolor=self.hex_to_rgb(xColor), xfcolor=self.hex_to_rgb(xfColor))
                
                if '::pic:' in xText:
                    self.LddtColor[xText] = dict(xcolor=self.hex_to_rgb(65535), xfcolor=self.hex_to_rgb(xfColor))
                
                if xText == 'New label': continue
                #if xColor == xfColor: continue
                xfSize = str(int(float(xfSize)*15/self.scf))
                
                if xrLeft < 0: xrLeft = 0
                if xrTop < 0: xrTop = 0
                
                xfBold = True if xfBold == '0' else False
                xfItalic = True if xfItalic == '0' else False
                
                if xAlignment == '1':
                    xrTop = xrTop + xrHeight / 2
                    xAlignment = 'middle'#'w'
                elif xAlignment == '2':
                    xrLeft = xrLeft + xrWidth / 2
                    xAlignment = 'top'#'n'
                else:
                    xAlignment = 'middle'#'nw'
                
                self.ddt_fontL[xText] = dict(name=xfName, size=xfSize, bold=xfBold, italic=xfItalic, anchor=xAlignment)
                
                if '::pic:' not in xText:
                    self.ddt_fontL[xText] = dict(name=xfName, size=xfSize, bold=xfBold, italic=xfItalic, anchor=xAlignment)
                else:
                    gifname = xText.replace('::pic:', 'graphics/') + '.gif'
                    gifname = gifname.replace('\\', '/')
                    gifname = mod_db_manager.extract_from_ddt_to_cache(gifname)
                    if gifname:
                        self.images[xText] = gifname
                        x1 = self.images[-1].width()
                        y1 = self.images[-1].height()
                        self.images[-1] = self.images[-1].zoom(3, 3)
                        self.images[-1] = self.images[-1].subsample(x1 * 3 / xrWidth, y1 * 3 / xrHeight)
                        self.ddt_label[xText] = [xrLeft, xrTop]

        dispalys = scr.findall("ns1:Display", ns)
        if len(dispalys):
            for dispaly in dispalys:
                xAlignment = '0'
                xText = ""
                if "DataName" in dispaly.attrib.keys():
                    xText = dispaly.attrib["DataName"]
                xReq = ""
                if "RequestName" in dispaly.attrib.keys():
                    xReq = dispaly.attrib["RequestName"]
                self.dReq[xReq] = self.decu.requests[xReq].ManuelSend
                
                if "Color" in dispaly.attrib.keys():
                    xColor = dispaly.attrib["Color"]
                else:
                    xColor = '000000'
                    
                xWidth = ""
                if "Width" in dispaly.attrib.keys():
                    xWidth = int(dispaly.attrib["Width"]) / scx
                
                xRect = dispaly.findall("ns1:Rectangle", ns)
                if len(xRect):
                    xRect = xRect[0]
                    xrLeft = int(xRect.attrib["Left"]) / scx
                    xrTop = int(xRect.attrib["Top"]) / (scy)
                    xrHeight = int(xRect.attrib["Height"]) / scy
                    xrWidth = int(xRect.attrib["Width"]) / scx
                
                xFont = dispaly.findall("ns1:Font", ns)
                if len(xFont):
                    xFont = xFont[0]
                    xfName = xFont.attrib["Name"]
                    xfSize = xFont.attrib["Size"]
                    xfBold = xFont.attrib["Bold"]
                    xfItalic = xFont.attrib["Italic"]
                    xfColor = xFont.attrib["Color"]

                if len(xText) == 0:
                    if len(self.decu.requests[xReq].ReceivedDI) == 1:
                        xText = self.decu.requests[xReq].ReceivedDI.keys()[0]
                    else:
                        xText = xReq
                
                self.dDisplay[xText] = 1
                self.ddt_dispalys[xText] = dict(left=xrLeft, top=xrTop+xrHeight, width=xrWidth, height=xrHeight, leftV=xrLeft + xWidth, widthV=xrWidth - xWidth, xw=xWidth)
                
                #if xColor == xfColor: continue
                
                xfSize = str(int(float(xfSize)*15/self.scf))
                
                if xrLeft < 0: xrLeft = 0
                if xrTop < 0: xrTop = 0
                
                xfBold = True if xfBold == '0' else False
                xfItalic = True if xfItalic == '0' else False
                
                self.DddtColor[xText] = dict(xcolor=self.hex_to_rgb(xColor), xfcolor=self.hex_to_rgb(xfColor))
                
                if xAlignment == '1':
                    xAlignment = 'bottom'#'w'
                elif xAlignment == '2':
                    xrLeft = xrLeft + xrWidth / 2
                    xAlignment = 'top'#'n'
                else:
                    xAlignment = 'middle'#'nw'
                
                if xWidth > 40:
                    tText = xText
                
                self.ddt_fontD[xText] = dict(name=xfName, size=xfSize, bold=xfBold, italic=xfItalic, anchor=xAlignment)
                if xText not in self.dValue.keys():
                    self.dValue[xText] = mod_globals.none_val

        inputs = scr.findall("ns1:Input", ns)
        if len(inputs):
            for input in inputs:
                xAlignment = '0'
                xReq = input.attrib["RequestName"]
                try:
                    xText = input.attrib["DataName"]
                except:
                    xText = xReq
                xColor = input.attrib["Color"]
                xWidth = int(input.attrib["Width"]) / scx
                
                xRect = input.findall("ns1:Rectangle", ns)
                if len(xRect):
                    xRect = xRect[0]
                    xrLeft = int(xRect.attrib["Left"]) / scx
                    xrTop = int(xRect.attrib["Top"]) / (scy)
                    xrHeight = int(xRect.attrib["Height"]) / scy
                    xrWidth = int(xRect.attrib["Width"]) / scx
                
                xFont = input.findall("ns1:Font", ns)
                if len(xFont):
                    xFont = xFont[0]
                    xfName = xFont.attrib["Name"]
                    xfSize = xFont.attrib["Size"]
                    xfBold = xFont.attrib["Bold"]
                    xfItalic = xFont.attrib["Italic"]
                    xfColor = xFont.attrib["Color"]

                self.ddt_inputs[xText] = dict(left=xrLeft, top=xrTop+xrHeight, width=xrWidth, height=xrHeight, leftV=xrLeft + xWidth, widthV=xrWidth - xWidth, xw=xWidth)
                
                #if xColor == xfColor: continue
                
                xfSize = str(int(float(xfSize)*10/self.scf))
                if xrLeft < 0: xrLeft = 0
                if xrTop < 0: xrTop = 0
                
                self.IddtColor[xText] = dict(xcolor=self.hex_to_rgb(xColor), xfcolor=self.hex_to_rgb(xfColor))
                
                xfBold = True if xfBold == '0' else False
                xfItalic = True if xfItalic == '0' else False
                
                if xAlignment == '1':
                    xrTop = xrTop + xrHeight / 2
                    xAlignment = 'bottom'#'w'
                elif xAlignment == '2':
                    xrLeft = xrLeft + xrWidth / 2
                    xAlignment = 'top'#'n'
                else:
                    xAlignment = 'middle'#'nw'
                
                if xWidth > 40:
                    tText = xText
                    self.tObj[id] = xText
                self.ddt_fontI[xText] = dict(name=xfName, size=xfSize, bold=xfBold, italic=xfItalic, anchor=xAlignment)
                if xText not in self.iValue.keys():
                    if xText not in self.dValue.keys():
                        self.dValue[xText] = ''
                    if xText in self.decu.req4data.keys() and self.decu.req4data[xText] in self.decu.requests.keys():
                        self.dReq[self.decu.req4data[xText]] = self.decu.requests[self.decu.req4data[xText]].ManuelSend
                    self.iValue[xText] = ''
                    self.iValueNeedUpdate[xText] = True
                if xText in self.decu.datas.keys() and len(self.decu.datas[xText].List.keys()):
                    optionList = []
                    if xText not in self.iValue.keys():
                        self.iValue[xText] = ''
                        self.iValueNeedUpdate[xText] = True
                    for i in self.decu.datas[xText].List.keys():
                        optionList.append(
                            hex(int(i)).replace("0x", "").upper() + ':' + self.decu.datas[xText].List[i])
                    self.ListOption[xText] = optionList
                    self.iValue[xText] = optionList[0]
                else:
                    self.iValue[xText] =('Enter here')
        buttons = scr.findall("ns1:Button", ns)
        if len(buttons):
            for button in buttons:
                xText = button.attrib["Text"]
                xRect = button.findall("ns1:Rectangle", ns)
                if len(xRect):
                    xRect = xRect[0]
                    xrLeft = int(xRect.attrib["Left"]) / scx
                    xrTop = int(xRect.attrib["Top"]) / (scy)
                    xrHeight = int(xRect.attrib["Height"]) / scy
                    xrWidth = int(xRect.attrib["Width"]) / scx
                if "Color" in button.attrib.keys():
                    xColor = button.attrib["Color"]
                else:
                    xColor = '000000'
                xFont = button.findall("ns1:Font", ns)
                if len(xFont):
                    xFont = xFont[0]
                    xfName = xFont.attrib["Name"]
                    xfSize = xFont.attrib["Size"]
                    xfBold = xFont.attrib["Bold"]
                    xfItalic = xFont.attrib["Italic"]
                    if "Color" in xFont.attrib.keys():
                      xfColor = xFont.attrib["Color"]
                    else:
                      xfColor = '000000'

                xSends = button.findall("ns1:Send", ns)
                slist = []
                if len(xSends):
                    slist = []
                    for xSend in xSends:
                        smap = {}
                        xsDelay = xSend.attrib["Delay"]
                        xsRequestName = xSend.attrib["RequestName"]
                        smap['Delay'] = xsDelay
                        smap['RequestName'] = xsRequestName
                        if len(xsRequestName) > 0:
                            slist.append(smap)
                if len(slist):
                    self.dBtnSend[str(slist)] = slist

                xfSize = str(int(float(xfSize)*15/self.scf))
                
                if xrLeft < 0: xrLeft = 0
                if xrTop < 0: xrTop = 0

                xfBold = True if xfBold == '0' else False
                xfItalic = True if xfItalic == '0' else False
                self.BddtColor[str(slist)] = dict(xcolor=self.hex_to_rgb(xColor), xfcolor=self.hex_to_rgb(xfColor))
                
                self.ddt_fontB[str(slist)] = dict(name=xfName, size=xfSize, bold=xfBold, italic=xfItalic, anchor='middle')
                if '::btn:' not in xText:
                    self.ddt_button[str(slist)] = dict(name=xText,left=xrLeft, top=xrTop+xrHeight, width=xrWidth, height=xrHeight)
                else:
                    gifname = 'graphics/' + xText.split('|')[1] + '.gif'
                    gifname = gifname.replace('\\', '/')
                    gifname = mod_db_manager.extract_from_ddt_to_cache(gifname)
                    if gifname:
                        self.images.append(tk.PhotoImage(file=gifname))
                        x1 = self.images[-1].width()
                        y1 = self.images[-1].height()
                        self.images[-1] = self.images[-1].zoom(3, 3)
                        self.images[-1] = self.images[-1].subsample(x1 * 3 / xrWidth + 1, y1 * 3 / xrHeight + 1)
        self.decu.clearELMcache()
        self.update_dInputs()
        sends = scr.findall("ns1:Send", ns)
        if len(sends):
            for send in sends:
                sDelay = '0'
                if "Delay" in send.attrib.keys():
                    sDelay = send.attrib["Delay"]
                sRequestName = ''
                if "RequestName" in send.attrib.keys():
                    sRequestName = send.attrib["RequestName"]
                self.sReq_dl[sRequestName] = sDelay
                self.sReq_lst.append(sRequestName)
        if len(self.sReq_lst):
            self.startScreen()
        self.start = True
        self.open_Screen()

    def loadSyntheticScreen(self, rq):
        read_cmd = self.decu.requests[rq].SentBytes
        if read_cmd[:2]=='21':
            read_cmd = read_cmd[:4]
            write_cmd = '3B'+read_cmd[2:4]
        elif read_cmd[:2]=='22':
            read_cmd = read_cmd[:6]
            write_cmd = '2E'+read_cmd[2:6]
        
        wc = ''
        set1 = set(self.decu.requests[rq].ReceivedDI.keys())
        set2 = []
        for r in self.decu.requests.keys():
            if self.decu.requests[r].SentBytes.startswith(write_cmd):
                set2 = set(self.decu.requests[r].SentDI.keys())
                if set1 == set2:
                    wc = r
                    break
        
        del( set1 )
        del( set2 )
        
        self.dValue = {} # value indexed by DataName
        self.iValue = {}  # value indexed by DataName param with choise
        self.iValueNeedUpdate = {}
        self.dReq = {}  # request names
        self.sReq_dl = {}  # delays for requests sent thru starting the screen
        self.sReq_lst = []  # list of requests sent thru starting the screen(order is important)
        self.dDisplay = {}  # displays object for renew
        self.dObj = []  # objects for place_forget
        self.tObj = {}  # objects for text captions
        self.dFrames = []  # container frames
        self.images = []  # images
        
        max_x = Window.size[0]
        max_y = 200 + len(self.decu.requests[rq].ReceivedDI)*40
        bg_color = "16777215"
        
        layout = GridLayout(cols=1, padding=10, spacing=10, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))
        tfSize = str(int(float(20) * self.scf))
        title = self.decu.requests[rq].SentBytes + ' - ' + rq
        
        xfSize = str(int(float(10) * self.scf))
        pn = 0
        for xText, zzz in sorted(self.decu.requests[rq].ReceivedDI.items(), key=lambda item: item[1].FirstByte):
            
            pn += 1
            
            self.dDisplay[xText] = 1
            yTop = 30 + pn * 40
            
            if xText not in self.dValue.keys():
                self.dValue[xText] = mod_globals.none_val
                if xText in self.decu.req4data.keys() and self.decu.req4data[xText] in self.decu.requests.keys():
                    self.dReq[self.decu.req4data[xText]] = self.decu.requests[self.decu.req4data[xText]].ManuelSend
            layout.add_widget(self.make_box_params(xText, self.dValue[xText]))
        
        if len(wc) > 0:
            slist = []
            smap = {}
            smap['Delay'] = 1000
            smap['RequestName'] = wc
            slist.append(smap)
            self.dBtnSend[str(slist)] = slist

            pn = pn + 1
            yTop = 30 + pn * 40
        
        
        root = ScrollView(size_hint=(1, 1))
        root.add_widget(layout)
        self.popup = Popup(title=title, title_size=int(tfSize), title_align='center', content=root, size=(Window.size[0]*0.8, Window.size[1]*0.8), size_hint=(None, None))
        self.popup.open()
        #self.decu.clearELMcache()
        #self.update_dInputs()
        #self.sReq_lst.append(rq)
        #self.startScreen()
 