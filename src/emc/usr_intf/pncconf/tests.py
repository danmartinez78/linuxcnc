#!/usr/bin/python2.4
# -*- encoding: utf-8 -*-
#    This is pncconf, a graphical configuration editor for LinuxCNC
#    Chris Morley copyright 2009
#    This is based from stepconf, a graphical configuration editor for linuxcnc
#    Copyright 2007 Jeff Epler <jepler@unpythonic.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USAimport os
import os
import gtk
import time

class TESTS:
    def __init__(self,app):
        # access to:
        self.d = app.d  # collected data
        global SIG
        SIG = app._p    # private data (signals names)
        global _PD
        _PD = app._p    # private data
        self.a = app    # The parent, pncconf
        self.w = app.widgets
        global debug
        debug = self.a.debug
        global dbg
        dbg = self.a.dbg

    def parporttest(self,w):
        if not self.a.check_for_rt(self):
            return
        panelname = os.path.join(_PD.DISTDIR, "configurable_options/pyvcp")
        self.halrun = halrun = os.popen("cd %(panelname)s\nhalrun -Is > /dev/null"% {'panelname':panelname,}, "w" )  
        halrun.write("loadrt threads period1=100000 name1=base-thread fp1=0 period2=%d name2=servo-thread\n"% self.d.servoperiod)
        self.hal_cmnds("LOAD")
        for i in range(0,self.d.number_pports ):
            halrun.write("loadusr -Wn parport%(number)dtest pyvcp -g +%(pos)d+0 -c parport%(number)dtest %(panel)s\n" 
                    % {'pos':(i*300),'number':i,'panel':"parportpanel.xml\n",})
        halrun.write("loadrt or2 count=%d\n"%(self.d.number_pports * 12))
        self.hal_cmnds("READ")
        for i in range(0,(self.d.number_pports * 12)):
           halrun.write("addf or2.%d base-thread\n"% i)
        halrun.write("loadusr halmeter pin parport.0.pin-01-out -g 0 500\n")
        self.hal_cmnds("WRITE")
        
        templist = ("pp1","pp2","pp3")
        for j in range(self.d.number_pports):         
            if self.d[templist[j]+"_direction"] == 1:
                inputpins = (10,11,12,13,15)
                outputpins = (1,2,3,4,5,6,7,8,9,14,16,17)               
                for x in (2,3,4,5,6,7,8,9):
                    halrun.write( "setp parport%dtest.led.%d.disable true\n"%(j, x))
                    halrun.write( "setp parport%dtest.led_text.%d.disable true\n"%(j, x))
            else:
                inputpins = (2,3,4,5,6,7,8,9,10,11,12,13,15)
                outputpins = (1,14,16,17)
                for x in (2,3,4,5,6,7,8,9):
                    halrun.write( "setp parport%dtest.button.%d.disable true\n"% (j , x))
                    halrun.write( "setp parport%dtest.button_text.%d.disable true\n"% (j , x))

            for x in inputpins: 
                i = self.w["%s_Ipin%d_inv" % (templist[j], x)].get_active()
                if i:  halrun.write( "net red_in_not.%d parport%dtest.led.%d <= parport.%d.pin-%02d-in-not\n" % (x, j, x, j, x))
                else:  halrun.write( "net red_in.%d parport%dtest.led.%d <= parport.%d.pin-%02d-in\n" % (x, j, x, j ,x))
            for num, x in enumerate(outputpins):  
                i = self.w["%s_Opin%d_inv" % (templist[j], x)].get_active()
                if i:  halrun.write( "setp parport.%d.pin-%02d-out-invert true\n" %(j, x))
                halrun.write("net signal_out%d or2.%d.out parport.%d.pin-%02d-out\n"% (x, num, j, x))
                halrun.write("net pushbutton.%d or2.%d.in1 parport%dtest.button.%d\n"% (x, num, j, x))
                halrun.write("net latchbutton.%d or2.%d.in0 parport%dtest.checkbutton.%d\n"% (x, num, j, x))           
        halrun.write("start\n")
        halrun.write("waitusr parport0test\n"); halrun.flush()
        halrun.close()
        self.w['window1'].set_sensitive(1)

    # This is for pyvcp test panel
    def testpanel(self,w):
        pos = "+0+0"
        size = ""
        panelname = os.path.join(_PD.DISTDIR, "configurable_options/pyvcp")
        if self.w.pyvcpblank.get_active() == True:
           return True
        if self.w.pyvcp1.get_active() == True:
           panel = "spindle.xml"
        if self.w.pyvcp2.get_active() == True:
           panel = "xyzjog.xml"
        if self.w.pyvcpexist.get_active() == True:
           panel = "pyvcp-panel.xml"
           panelname = os.path.expanduser("~/linuxcnc/configs/%s" % self.d.machinename)
        if self.w.pyvcpposition.get_active() == True:
            xpos = self.w.pyvcpxpos.get_value()
            ypos = self.w.pyvcpypos.get_value()
            pos = "+%d+%d"% (xpos,ypos)
        if self.w.pyvcpsize.get_active() == True:
            width = self.w.pyvcpwidth.get_value()
            height = self.w.pyvcpheight.get_value()
            size = "%dx%d"% (width,height)    
        self.halrun = halrun = os.popen("cd %(panelname)s\nhalrun -Is > /dev/null"% {'panelname':panelname,}, "w" )    
        halrun.write("loadusr -Wn displaytest pyvcp -g %(size)s%(pos)s -c displaytest %(panel)s\n" %{'size':size,'pos':pos,'panel':panel,})
        if self.w.pyvcp1.get_active() == True:
                halrun.write("setp displaytest.spindle-speed 1000\n")
        halrun.write("waitusr displaytest\n"); halrun.flush()
        halrun.close()

    def display_gladevcp_panel(self):
        pos = "+0+0"
        size = "200x200"
        options = ""
        folder = "/tmp"
        if not self.w.createconfig.get_active() and self.w.gladeexists.get_active():
            folder = os.path.expanduser("~/linuxcnc/configs/%s" % self.d.machinename)
            if not os.path.exists(folder + "/gvcp-panel.ui"):
                self.a.warning_dialog (_("""You specified there is an existing gladefile, \
But there is not one in the machine-named folder.."""),True)
                return
        self.gladevcptestpanel(self)
        if self.w.gladevcpposition.get_active() == True:
            xpos = self.w.gladevcpxpos.get_value()
            ypos = self.w.gladevcpypos.get_value()
            pos = "+%d+%d"% (xpos,ypos)
        if self.w.gladevcpsize.get_active() == True:
            width = self.w.gladevcpwidth.get_value()
            height = self.w.gladevcpheight.get_value()
            size = "%dx%d"% (width,height)
        if not self.w.gladevcptheme.get_active_text() == "Follow System Theme":
            options ="-t %s"% (self.w.gladevcptheme.get_active_text())
            print options
        self.halrun = halrun = os.popen("cd %s\nhalrun -Is > /dev/null"%(folder), "w" )    
        halrun.write("loadusr -Wn displaytest gladevcp -g %(size)s%(pos)s -c displaytest %(option)s gvcp-panel.ui\n" %{'size':size,'pos':pos,'option':options})
        if self.w.spindlespeedbar.get_active():
            halrun.write("setp displaytest.spindle-speed 500\n")
        if self.w.zerox.get_active():
            halrun.write("setp displaytest.zero-x-active true\n")
        if self.w.zeroy.get_active():
            halrun.write("setp displaytest.zero-y-active true\n")
        if self.w.zeroz.get_active():
            halrun.write("setp displaytest.zero-z-active true\n")
        if self.w.zeroa.get_active():
            halrun.write("setp displaytest.zero-a-active true\n")
        if self.w.autotouchz.get_active():
            halrun.write("setp displaytest.auto-touch-z-active true\n")
        if self.w.spindleatspeed.get_active():
            halrun.write("setp displaytest.spindle-at-speed-led true\n")
        halrun.write("setp displaytest.button-box-active true\n")
        halrun.write("waitusr displaytest\n"); halrun.flush()
        halrun.close()

    def gladevcptestpanel(self,w):
        directory = "/tmp/"
        filename = os.path.join(directory, "gvcp-panel.ui")
        file = open(filename, "w")
        print >>file, ("""<?xml version="1.0"?>
<interface>
  <!-- interface-requires gladevcp 0.0 -->
  <requires lib="gtk+" version="2.16"/>
  <!-- interface-naming-policy project-wide -->
  <object class="GtkWindow" id="window1">
    <property name="width_request">100</property>
    <child>
      <object class="GtkVBox" id="vbox1">
        <property name="visible">True</property>""")
        if self.w.spindlespeedbar.get_active():
            print >>file, ("""
        <child>
          <object class="HAL_HBar" id="spindle-speed">
            <property name="visible">True</property>
            <property name="force_height">36</property>""")
            print >>file, ("""<property name="max">%(maxrpm)d</property>"""%{'maxrpm':self.w.maxspeeddisplay.get_value() })
            print >>file, ("""
            <property name="z0_color">#0000ffff0000</property>
            <property name="value">44.25</property>
            <property name="z1_color">#ffffffff0000</property>
            <property name="bg_color">#bebebebebebe</property>
            <property name="text_template">Spindle: % 4d RPM</property>
            <property name="z0_border">0.94999998807907104</property>
            <property name="z2_color">#ffff00000000</property>
            <property name="show_limits">False</property>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="position">0</property>
          </packing>
        </child>""" )
        if self.w.spindleatspeed.get_active():
            print >>file, ("""
        <child>
          <object class="GtkHBox" id="hbox1">
            <property name="visible">True</property>
            <child>
              <object class="GtkLabel" id="label1">
                <property name="visible">True</property>
                <property name="ypad">5</property>
                <property name="label" translatable="yes"> Spindle Up To Speed </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="HAL_LED" id="spindle-at-speed-led">
                <property name="visible">True</property>
                <property name="led_shape">2</property>
                <property name="on_color">green</property>
                <property name="led_size">5</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="padding">10</property>
                <property name="position">1</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="position">1</property>
          </packing>
        </child>""")
        print >>file, ("""
        <child>
          <object class="HAL_Table" id="button-box-active">
            <property name="visible">True</property>
            <property name="n_rows">5</property>
            <property name="homogeneous">False</property>""")
        if self.w.autotouchz.get_active():
            print >>file, ("""
            <child>
              <object class="HAL_HBox" id="auto-touch-z-active">
                <property name="visible">True</property>
                <child>
                  <object class="HAL_Button" id="auto-touch-z">
                    <property name="label" translatable="yes">Z  Auto Touch Off</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">True</property>
                    <property name="yalign">0.56000000238418579</property>
                  </object>
                  <packing>
                    <property name="position">0</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="top_attach">4</property>
                <property name="bottom_attach">5</property>
              </packing>
            </child>""")
        if self.w.zeroa.get_active():
            print >>file, ("""
            <child>
              <object class="HAL_HBox" id="zero-a-active">
                <property name="visible">True</property>
                <child>
                  <object class="HAL_Button" id="zero-a">
                    <property name="label" translatable="yes">Zero A</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">True</property>
                  </object>
                  <packing>
                    <property name="position">0</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="top_attach">3</property>
                <property name="bottom_attach">4</property>
              </packing>
            </child>""")
        if self.w.zeroz.get_active():
            print >>file, ("""
            <child>
              <object class="HAL_HBox" id="zero-z-active">
                <property name="visible">True</property>
                <child>
                  <object class="HAL_Button" id="zero-z">
                    <property name="label" translatable="yes">Zero Z</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">True</property>
                  </object>
                  <packing>
                    <property name="position">0</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="top_attach">2</property>
                <property name="bottom_attach">3</property>
              </packing>
            </child>""")
        if self.w.zeroy.get_active():
            print >>file, ("""
            <child>
              <object class="HAL_HBox" id="zero-y-active">
                <property name="visible">True</property>
                <child>
                  <object class="HAL_Button" id="zero-y">
                    <property name="label" translatable="yes">Zero Y</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">True</property>
                  </object>
                  <packing>
                    <property name="position">0</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="top_attach">1</property>
                <property name="bottom_attach">2</property>
              </packing>
            </child>""")
        if self.w.zerox.get_active():
            print >>file, ("""
            <child>
              <object class="HAL_HBox" id="zero-x-active">
                <property name="visible">True</property>
                <child>
                  <object class="HAL_Button" id="zero-x">
                    <property name="label" translatable="yes">Zero X</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">True</property>
                  </object>
                  <packing>
                    <property name="position">0</property>
                  </packing>
                </child>
              </object>
            </child>""")
        print >>file, ("""
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">False</property>
            <property name="position">2</property>
          </packing>
        </child>
      </object>
    </child>
  </object>
</interface>""")
        file.close()



    # for classicladder test  
    def load_ladder(self,w): 
        newfilename = os.path.join(_PD.DISTDIR, "configurable_options/ladder/TEMP.clp")    
        self.d.modbus = self.w.modbus.get_active()
        self.halrun = halrun = os.popen("halrun -Is > /dev/null", "w")
        if debug:
            halrun.write("echo\n")
        halrun.write(""" 
              loadrt threads period1=%(period)d name1=base-thread fp1=0 period2=%(period2)d name2=servo-thread 
              loadrt classicladder_rt numPhysInputs=%(din)d numPhysOutputs=%(dout)d numS32in=%(sin)d\
               numS32out=%(sout)d numFloatIn=%(fin)d numFloatOut=%(fout)d numBits=%(bmem)d numWords=%(wmem)d
               addf classicladder.0.refresh servo-thread
               start\n""" % {
                      'din': self.w.digitsin.get_value(),
                      'dout': self.w.digitsout.get_value(),
                      'sin': self.w.s32in.get_value(),
                      'sout': self.w.s32out.get_value(), 
                      'fin':self.w.floatsin.get_value(),
                      'fout':self.w.floatsout.get_value(),
                      'bmem':self.w.bitmem.get_value(),
                      'wmem':self.w.wordmem.get_value(),
                      'period':100000, 
                      'period2':self.d.servoperiod
                 })
        if self.w.ladderexist.get_active() == True:
            if self.d.tempexists:
               self.d.laddername='TEMP.clp'
            else:
               self.d.laddername= 'blank.clp'
        if self.w.ladder1.get_active() == True:
            self.d.laddername= 'estop.clp'
        if self.w.ladder2.get_active() == True:
            self.d.laddername = 'serialmodbus.clp'
            self.d.modbus = True
            self.w.modbus.set_active(True)
        if self.w.laddertouchz.get_active() == True:
            self.d.laddertouchz = True
            self.d.laddername = 'touchoff_z.clp'
            self.d.halui = True
            self.w.halui.set_active(True)
        if self.w.ladderexist.get_active() == True:
            self.d.laddername='custom.clp'
            originalfile = filename = os.path.expanduser("~/linuxcnc/configs/%s/custom.clp" % self.d.machinename)
        else:
            filename = os.path.join(_PD.DISTDIR, "configurable_options/ladder/"+ self.d.laddername)        
        if self.d.modbus == True: 
            halrun.write("loadusr -w classicladder --modmaster --newpath=%(newname)s %(filename)s\n" %                                  {'newname':newfilename,'filename':filename})
        else:
            halrun.write("loadusr -w classicladder --newpath=%(newname)s %(filename)s\n" % { 'newname':newfilename ,'filename':filename })
        halrun.write("start\n"); halrun.flush()
        halrun.close()
        if os.path.exists(newfilename):
            self.d.tempexists = True
            self.w.newladder.set_text('Edited ladder program')
            self.w.ladderexist.set_active(True)
        else:
            self.d.tempexists = 0
      
    # servo and stepper test  
    def tune_axis(self, axis):
        def get_value(d):
            return self.a.get_value(d)
        if not self.a.check_for_rt(self):
            return
        d = self.d
        w = self.w
        self.updaterunning = False
        axnum = "xyzas".index(axis)
        self.axis_under_tune = axis
        step_sig = self.a.stepgen_sig(axis)
        self.stepgen = self.a.stepgen_sig(axis)
        #print axis," stepgen--",self.stepgen
        self.encoder = self.a.encoder_sig(axis)
        #print axis," encoder--",self.encoder
        pwm_sig = self.a.pwmgen_sig(axis)
        self.pwm = self.d.make_pinname(pwm_sig)
        #print axis," pwgen--",self.pwmgen
        pump = self.d.findsignal("charge-pump")

        if self.stepgen:
            w.xtuningnotebook.set_current_page(1)
            w.xpid.set_sensitive(0)
            w.xtuneinvertencoder.set_sensitive(0)
            w.xpidtable.set_sensitive(0)
        else:
            w.xtuningnotebook.set_current_page(0)
            w.xstep.set_sensitive(0)
            w.xsteptable.set_sensitive(0)
            text = _("Servo tuning is not avaiable in PNCconf yet\n")
            self.a.warning_dialog(text,True)
            return

        if axis == "a":
            w,xtunedistunits.set_text(_("degrees"))
            w.xtunevelunits.set_text(_("degrees / minute"))
            w.xtuneaccunits.set_text(_("degrees / second²"))
        elif axis == "s":
            w.xtunedistunits.set_text(_("revolutions"))
            w.xtunevelunits.set_text(_("rpm"))
            w.xtuneaccunits.set_text(_("revs / second²"))
        elif d.units == _PD._METRIC:
            w.xtunedistunits.set_text(_("mm"))
            w.xtunevelunits.set_text(_("mm / minute"))
            w.xtuneaccunits.set_text(_("mm / second²"))
        else:
            w.xtunedistunits.set_text(_("inches"))
            w.xtunevelunits.set_text(_("inches / minute"))
            w.xtuneaccunits.set_text(_("inches / second²"))
        w.xtunevel.set_value(get_value(w[axis+"maxvel"]))
        w.xtuneacc.set_value(get_value(w[axis+"maxacc"]))
        w.xtunecurrentP.set_value(w[axis+"P"].get_value())
        w.xtuneorigP.set_text("%s" % w[axis+"P"].get_value())
        w.xtunecurrentI.set_value(w[axis+"I"].get_value())
        w.xtuneorigI.set_text("%s" % w[axis+"I"].get_value())
        w.xtunecurrentD.set_value(w[axis+"D"].get_value())
        w.xtuneorigD.set_text("%s" % w[axis+"D"].get_value())
        w.xtunecurrentFF0.set_value(w[axis+"FF0"].get_value())
        w.xtuneorigFF0.set_text("%s" % w[axis+"FF0"].get_value())
        w.xtunecurrentFF1.set_value(w[axis+"FF1"].get_value())
        w.xtuneorigFF1.set_text("%s" % w[axis+"FF1"].get_value())
        w.xtunecurrentFF2.set_value(w[axis+"FF2"].get_value())
        w.xtuneorigFF2.set_text("%s" % w[axis+"FF2"].get_value())
        w.xtunecurrentbias.set_value(w[axis+"bias"].get_value())
        w.xtuneorigbias.set_text("%s" % w[axis+"bias"].get_value())
        w.xtunecurrentdeadband.set_value(w[axis+"deadband"].get_value())
        w.xtuneorigdeadband.set_text("%s" % w[axis+"deadband"].get_value())
        w.xtunecurrentsteptime.set_value(w[axis+"steptime"].get_value())
        w.xtuneorigsteptime.set_text("%s" % w[axis+"steptime"].get_value())
        w.xtunecurrentstepspace.set_value(get_value(w[axis+"stepspace"]))
        w.xtuneorigstepspace.set_text("%s" % w[axis+"stepspace"].get_value())
        w.xtunecurrentdirhold.set_value(get_value(w[axis+"dirhold"]))
        w.xtuneorigdirhold.set_text("%s" % w[axis+"dirhold"].get_value())
        w.xtunecurrentdirsetup.set_value(get_value(w[axis+"dirsetup"]))
        w.xtuneorigdirsetup.set_text("%s" % w[axis+"dirsetup"].get_value())
        self.tunejogplus = self.tunejogminus = 0
        w.xtunedir.set_active(0)
        w.xtunerun.set_active(0)
        w.xtuneinvertmotor.set_active(w[axis+"invertmotor"].get_active())
        w.xtuneinvertencoder.set_active(w[axis+"invertencoder"].get_active())
        dac_scale = get_value(w[axis+"outputscale"])
        pwmminlimit = get_value(w[axis+"outputminlimit"])
        pwmmaxlimit = get_value(w[axis+"outputmaxlimit"])
        pwmmaxoutput = get_value(w[axis+"outputscale"])
             
        self.halrun = halrun = os.popen("halrun -Is > /dev/null", "w")
        if debug:
            halrun.write("echo\n")
        halrun.write("""
        loadrt threads period1=%(period)d name1=base-thread fp1=0 period2=%(period2)d name2=servo-thread
        loadusr halscope
        loadrt scale names=scale_to_rpm
        loadrt steptest     
        """ % {'period':100000, 'period2':self.d.servoperiod })   
        if not self.stepgen: 
            halrun.write("loadrt pid num_chan=1\n")
        self.hal_cmnds("LOAD")
        self.hal_cmnds("READ")
        if pump:
            halrun.write( "loadrt charge_pump\n")
            halrun.write( "net enable charge-pump.enable\n")
            halrun.write( "net charge-pump <= charge-pump.out\n")
            halrun.write( "addf charge-pump servo-thread\n")
        halrun.write("addf steptest.0 servo-thread \n")
        if not self.stepgen: 
            halrun.write("addf pid.0.do-pid-calcs servo-thread \n")
        halrun.write("addf scale_to_rpm servo-thread \n")
        self.hal_cmnds("WRITE")
        halrun.write( "newsig estop-out bit\n")
        halrun.write( "sets estop-out false\n")
        # search and connect I/o signals needed to enable amps etc
        self.hal_test_signals(axis)
        # for encoder signals
        if self.encoder: 
            #print self.encoder,"--",self.encoder[4:5],self.encoder[10:],self.encoder[6:7] 
            self.enc_signalname = self.d.make_pinname(self.encoder)                 
            halrun.write("setp %s.counter-mode 0\n"% (self.enc_signalname))
            halrun.write("setp %s.filter 1\n"% (self.enc_signalname))
            halrun.write("setp %s.index-invert 0\n"% (self.enc_signalname))
            halrun.write("setp %s.index-mask 0\n"% (self.enc_signalname))
            halrun.write("setp %s.index-mask-invert 0\n"% (self.enc_signalname)) 
            halrun.write("setp %s.scale %d\n"% (self.enc_signalname, get_value(w[axis + "encoderscale"])))                         
            halrun.write("loadusr halmeter -s pin %s.velocity -g 0 625 330\n"% (self.enc_signalname))
            halrun.write("loadusr halmeter -s pin %s.position -g 0 675 330\n"% (self.enc_signalname))
            halrun.write("loadusr halmeter pin %s.velocity -g 275 415\n"% (self.enc_signalname))

        # setup pwm generator
        if self.pwm:
            print self.pwm
            if "pwm" in self.pwm: # mainboard PWM
                pwmtype = self.d[pwm_sig+"type"]
                if  pwmtype == _PD.PWMP: pulsetype = 1
                elif pwmtype == _PD.PDMP: pulsetype = 3
                elif pwmtype == _PD.UDMU: pulsetype = 2
                else: 
                    print "**** ERROR PNCCONF- PWM type not recognized in tune test"
                    return
                halrun.write("setp %s %d \n"%  (self.pwm +".output-type", pulsetype))
                halrun.write("net enable %s \n"%  (self.pwm +".enable"))
                halrun.write("setp %s \n"%  (self.pwm +".scale %f"% dac_scale))
                ending = ".value"
                pwminvertlist = self.d.pwmgen_invert_pins(pwm_sig)
                for i in pwminvertlist:
                    halrun.write("setp    "+i+".invert_output true")
            else: # sserial PWM
                pwm_enable = self.d.make_pinname(pwm_sig,False,True) # get prefix only
                halrun.write("net enable %s \n"%  (pwm_enable +"analogena"))
                halrun.write("setp   "+self.pwm+"-minlim   %.1f\n"% pwmminlimit)
                halrun.write("setp   "+self.pwm+"-maxlim   %.1f\n"% pwmmaxlimit)
                halrun.write("setp   "+self.pwm+"-scalemax %.1f\n"% pwmmaxoutput)
                ending = ""
            halrun.write("net output %s \n"%  (self.pwm + ending))
            halrun.write("loadusr halmeter -s pin %s -g 0 575 330\n"%  (self.pwm + ending))
            halrun.write("loadusr halmeter pin %s -g 0 550 375\n"% (self.pwm + ending) )
            halrun.write("loadusr halmeter -s sig enable -g 0 525 330\n")

        # for step gen components
        if self.stepgen:                        
            # check current component number to signal's component number                             
            self.step_signalname = self.d.make_pinname(self.stepgen) 
            #print "step_signal--",self.step_signalname   
            if w[axis+"invertmotor"].get_active():
                self.scale = get_value(w[axis + "stepscale"]) * -1
            else:
                self.scale = get_value(w[axis + "stepscale"]) * 1
            stepinvertlist = self.a.stepgen_invert_pins(step_sig)
            for i in stepinvertlist:
                halrun.write("setp    "+i+".invert_output true")
            halrun.write("setp %s.step_type 0 \n"% (self.step_signalname))
            halrun.write("setp %s.position-scale %f \n"% (self.step_signalname,self.scale))
            halrun.write("setp %s.steplen %d \n"% (self.step_signalname,w[axis+"steptime"].get_value()))
            halrun.write("setp %s.stepspace %d \n"% (self.step_signalname,w[axis+"stepspace"].get_value()))
            halrun.write("setp %s.dirhold %d \n"% (self.step_signalname,w[axis+"dirhold"].get_value()))
            halrun.write("setp %s.dirsetup %d \n"% (self.step_signalname,w[axis+"dirsetup"].get_value()))
            halrun.write("setp steptest.0.epsilon %f\n"% abs(1. / get_value(w[axis + "stepscale"]))  )
            halrun.write("setp %s.maxaccel 0 \n"% (self.step_signalname))
            halrun.write("setp %s.maxvel 0 \n"% (self.step_signalname))
            halrun.write("net enable => %s.enable \n"% (self.step_signalname))
            halrun.write("net cmd steptest.0.position-cmd => %s.position-cmd \n"% (self.step_signalname))
            halrun.write("net feedback steptest.0.position-fb <= %s.position-fb \n"% (self.step_signalname))
            halrun.write("net speed_rps scale_to_rpm.in <= %s.velocity-fb \n"% (self.step_signalname))
            halrun.write("net speed_rpm scale_to_rpm.out\n")
            halrun.write("setp scale_to_rpm.gain 60\n")
            halrun.write("loadusr halmeter sig speed_rpm -g 0 415\n")
            halrun.write("loadusr halmeter -s pin %s.velocity-fb -g 0 575 350\n"% (self.step_signalname))
            halrun.write("loadusr halmeter -s pin %s.position-fb -g 0 525 350\n"% (self.step_signalname))
        # set up PID if there is a feedback sensor and pwm. TODO add ability to test closed loop steppers
        if self.encoder and self.pwm:
            halrun.write("setp pid.0.Pgain     %d\n"% ( w[axis+"P"].get_value() ))
            halrun.write("setp pid.0.Igain     %d\n"% ( w[axis+"I"].get_value() ))
            halrun.write("setp pid.0.Dgain     %d\n"% ( w[axis+"D"].get_value() ))
            halrun.write("setp pid.0.bias      %d\n"% ( w[axis+"bias"].get_value() ))
            halrun.write("setp pid.0.FF0       %d\n"% ( w[axis+"FF0"].get_value() ))
            halrun.write("setp pid.0.FF1       %d\n"% ( w[axis+"FF1"].get_value() ))
            halrun.write("setp pid.0.FF2       %d\n"% ( w[axis+"FF2"].get_value() ))
            halrun.write("setp pid.0.deadband  %d\n"% ( w[axis+"deadband"].get_value() ))
            halrun.write("setp pid.0.maxoutput  %d\n"% ( w[axis+"maxoutput"].get_value() ))
            halrun.write("net enable     => pid.0.enable\n")
            halrun.write("net output     pid.0.output\n")
            halrun.write("net pos-cmd    steptest.0.position-cmd => pid.0.command\n")
            halrun.write("net feedback steptest.0.position-fb <= %s.position \n"% (self.enc_signalname))
   
        self.updaterunning = True
        halrun.write("start\n"); halrun.flush()
        w.tunedialog.set_title(_("%s Axis Tune") % axis.upper())
        w.tunedialog.move(550,0)
        w.tunedialog.show_all()
        self.w['window1'].set_sensitive(0)
        result = w.tunedialog.run()
        w.tunedialog.hide()
        if result == gtk.RESPONSE_OK:
            w[axis+"maxvel"].set_value( get_value(w.xtunevel))
            w[axis+"maxacc"].set_value( get_value(w.xtuneacc))
            w[axis+"P"].set_value( get_value(w.xtunecurrentP))
            w[axis+"I"].set_value( get_value(w.xtunecurrentI))
            w[axis+"D"].set_value( get_value(w.xtunecurrentD))
            w[axis+"FF0"].set_value( get_value(w.xtunecurrentFF0))
            w[axis+"FF1"].set_value( get_value(w.xtunecurrentFF1))
            w[axis+"FF2"].set_value( get_value(w.xtunecurrentFF2))
            w[axis+"bias"].set_value( get_value(w.xtunecurrentbias))
            w[axis+"deadband"].set_value( get_value(w.xtunecurrentdeadband))
            w[axis+"bias"].set_value(w.xtunecurrentbias.get_value())
            w[axis+"steptime"].set_value(get_value(w.xtunecurrentsteptime))
            w[axis+"stepspace"].set_value(get_value(w.xtunecurrentstepspace))
            w[axis+"dirhold"].set_value(get_value(w.xtunecurrentdirhold))
            w[axis+"dirsetup"].set_value(get_value(w.xtunecurrentdirsetup))
            w[axis+"invertmotor"].set_active(w.xtuneinvertmotor.get_active())
            w[axis+"invertencoder"].set_active(w.xtuneinvertencoder.get_active())      
        halrun.write("sets enable false\n")   
        time.sleep(.001)   
        halrun.close()  
        self.w['window1'].set_sensitive(1)

    def update_tune_test_params(self, *args):       
        axis = self.axis_under_tune
        if axis is None or not self.updaterunning: return   
        temp = not self. w.xtunerun.get_active()
        self.w.xtuneinvertmotor.set_sensitive( temp)
        self.w.xtuneamplitude.set_sensitive( temp)
        self.w.xtunedir.set_sensitive( temp)
        self.w.xtunejogminus.set_sensitive(temp)
        self.w.xtunejogplus.set_sensitive(temp)
        temp = self.w.xtuneenable.get_active()
        if not self.w.xtunerun.get_active():
            self.w.xtunejogminus.set_sensitive(temp)
            self.w.xtunejogplus.set_sensitive(temp)
        self.w.xtunerun.set_sensitive(temp)
        halrun = self.halrun
        if self.stepgen:
            halrun.write("""
                setp %(stepgen)s.steplen %(len)d
                setp %(stepgen)s.stepspace %(space)d
                setp %(stepgen)s.dirhold %(hold)d
                setp %(stepgen)s.dirsetup %(setup)d
                setp %(stepgen)s.maxaccel %(accel)f
                setp %(stepgen)s.maxvel %(velps)f
                setp %(stepgen)s.position-scale %(scale)f  
                setp steptest.0.jog-minus %(jogminus)s
                setp steptest.0.jog-plus %(jogplus)s
                setp steptest.0.run %(run)s
                setp steptest.0.amplitude %(amplitude)f
                setp steptest.0.maxvel %(velps)f
                setp steptest.0.maxaccel %(accel)f
                setp steptest.0.dir %(dir)s
                setp steptest.0.pause %(pause)d
                sets enable %(enable)s
                sets estop-out %(estop)s
            """ % {
                'scale':self.scale,
                'len':self.w.xtunecurrentsteptime.get_value(),
                'space':self.w.xtunecurrentstepspace.get_value(),
                'hold':self.w.xtunecurrentdirhold.get_value(),
                'setup':self.w.xtunecurrentdirsetup.get_value(),
                'stepgen': self.step_signalname,               
                'jogminus': self.tunejogminus,
                'jogplus': self.tunejogplus,
                'run': self.w.xtunerun.get_active(),
                'amplitude': self.w.xtuneamplitude.get_value(),
                'accel': self.w.xtuneacc.get_value(),
                'vel': self.w.xtunevel.get_value(),
                'velps': (self.w.xtunevel.get_value()/60),
                'dir': self.w.xtunedir.get_active(),
                'pause':int(self.w.xtunepause.get_value()),
                'enable':self.w.xtuneenable.get_active(),
                'estop':(self.w.xtuneenable.get_active())
            })
        else:
            halrun.write("""  
                setp pid.0.Pgain  %(p)f
                setp pid.0.Igain  %(i)f
                setp pid.0.Dgain  %(d)f 
                setp pid.0.bias   %(bias)f
                setp pid.0.FF0    %(ff0)f
                setp pid.0.FF1    %(ff1)f     
                setp pid.0.FF2    %(ff2)f
                setp pid.0.bias   %(bias)f
                setp pid.0.deadband  %(deadband)f
                setp steptest.0.jog-minus %(jogminus)s
                setp steptest.0.jog-plus %(jogplus)s
                setp steptest.0.run %(run)s
                setp steptest.0.amplitude %(amplitude)f
                setp steptest.0.maxvel %(velps)f
                setp steptest.0.maxaccel %(accel)f
                setp steptest.0.dir %(dir)s
                setp steptest.0.pause %(pause)d
                sets enable %(enable)s
            """ % {
                'p':self.w.xtunecurrentP.get_value(),
                'i':self.w.xtunecurrentI.get_value(),
                'd':self.w.xtunecurrentD.get_value(),
                'ff0':self.w.xtunecurrentFF0.get_value(),
                'ff1':self.w.xtunecurrentFF1.get_value(),
                'ff2':self.w.xtunecurrentFF2.get_value(),
                'bias':self.w.xtunecurrentbias.get_value(),
                'deadband':self.w.xtunecurrentdeadband.get_value(),
                'invert':self.w.xtuneinvertmotor.get_active(),
                'jogminus': self.tunejogminus,
                'jogplus': self.tunejogplus,
                'run': self.w.xtunerun.get_active(),
                'amplitude': self.w.xtuneamplitude.get_value(),
                'accel': self.w.xtuneacc.get_value(),
                'vel': self.w.xtunevel.get_value(),
                'velps': (self.w.xtunevel.get_value()/60),
                'dir': self.w.xtunedir.get_active(),
                'pause':int(self.w.xtunepause.get_value()),
                'enable':self.w.xtuneenable.get_active()
            })
        halrun.flush()

    def tune_jogminus(self, direction):
        self.tunejogminus = direction
        self.update_tune_test_params()
    def tune_jogplus(self, direction):
        self.tunejogplus = direction
        self.update_tune_test_params()
    # TODO fix scaling for servos:
    def toggle_tuneinvertmotor(self):
        def get_value(d):
            return self.a.get_value(d)
        axis = self.axis_under_tune
        w = self.w
        if w.xtuneinvertmotor.get_active():
            self.scale = get_value(w[axis + "stepscale"]) * -1
        else:
            self.scale = get_value(w[axis + "stepscale"])                 
        self.update_tune_test_params()

    # openloop servo test
    def test_axis(self, axis):
        def get_value(d):
            return self.a.get_value(d)
        # can't test with a simulator
        if not self.a.check_for_rt(self):
            return
        # one needs real time, pwm gen and an encoder for open loop testing.
        temp = self.d.findsignal( (axis + "-encoder-a"))
        self.enc = self.d.make_pinname(temp)
        temp = self.d.findsignal( (axis + "-resolver"))
        self.res = self.d.make_pinname(temp)
        pwm_sig = self.d.findsignal( (axis + "-pwm-pulse"))
        self.pwm = self.d.make_pinname(pwm_sig)
        pot_sig = self.d.findsignal(axis+"-pot-output")
        self.pot = self.d.make_pinname(pot_sig)

        if axis == "s":
            if (not self.pwm and not self.pot) and (not self.enc and not self.res):
                self.a.warning_dialog( _(" You must designate a ENCODER / RESOLVER signal and an ANALOG SPINDLE signal for this axis test") , True)
                return
        else:
            if not self.pwm or (not self.enc and not self.res) :
                self.a.warning_dialog( _(" You must designate a ENCODER / RESOLVER signal and a PWM signal for this axis test") , True)
                return           

        self.halrun = halrun = os.popen("halrun -Is > /dev/null", "w")
        if debug:
            halrun.write("echo\n")
        data = self.d
        widgets = self.w
        axnum = "xyzas".index(axis)
        pump = False
        fastdac = get_value(widgets["fastdac"])
        slowdac = get_value(widgets["slowdac"])
        dacspeed = widgets.Dac_speed_fast.get_active()
        dac_scale = get_value(widgets[axis+"outputscale"])
        max_dac = get_value(widgets[axis+"maxoutput"])
        pwmminlimit = get_value(widgets[axis+"outputminlimit"])
        pwmmaxlimit = get_value(widgets[axis+"outputmaxlimit"])
        pwmmaxoutput = get_value(widgets[axis+"outputscale"])
        enc_scale = get_value(widgets[axis+"encoderscale"])
        pump = self.d.findsignal("charge-pump")

        halrun.write("loadrt threads period1=%d name1=base-thread fp1=0 period2=%d name2=servo-thread \n" % (100000, self.d.servoperiod  ))       
        self.hal_cmnds("LOAD")
        #halrun.write("loadrt steptest\n")
        halrun.write("loadusr halscope\n")
        self.hal_cmnds("READ")
        if pump:
            halrun.write( "loadrt charge_pump\n")
            halrun.write( "net enable charge-pump.enable\n")
            halrun.write( "net charge-pump <= charge-pump.out\n")
            halrun.write( "addf charge-pump servo-thread\n")
        #halrun.write("addf steptest.0 servo-thread\n")
        self.hal_cmnds("WRITE")
        halrun.write( "newsig estop-out bit\n")
        halrun.write( "sets estop-out false\n")
        halrun.write( "newsig enable-not bit\n")
        halrun.write( "newsig dir-not bit\n")
        halrun.write( "newsig dir bit\n")
        # search for pins with test signals that may be needed to enable amp
        self.hal_test_signals(axis)

        # setup sserial potentiometer 
        if self.pot:
            halrun.write("net dac " + self.pot + "spinout\n")
            halrun.write("net enable " + self.pot +"spinena\n")
            halrun.write("net dir " + self.pot +"spindir\n")
            halrun.write("setp   "+self.pot+"spinout-minlim   %.1f\n"% pwmminlimit)
            halrun.write("setp   "+self.pot+"spinout-maxlim   %.1f\n"% pwmmaxlimit)
            halrun.write("setp   "+self.pot+"spinout-scalemax %.1f\n"% pwmmaxoutput)
            potinvertlist = self.d.spindle_invert_pins(pot_sig)
            for i in potinvertlist:
                    if i == _PD.POTO:
                        halrun.write("setp   "+self.pot+"spindir-invert   true\n")
                    if i == _PD.POTE:
                        halrun.write("setp   "+self.pot+"spinena-invert   true\n")
        # setup pwm generator
        if self.pwm:
            if "pwm" in self.pwm: # mainboard PWM
                pwmtype = self.d[pwm_sig+"type"]
                if  pwmtype == _PD.PWMP: pulsetype = 1
                elif pwmtype == _PD.PDMP: pulsetype = 3
                elif pwmtype == _PD.UDMU: pulsetype = 2
                else: 
                    print "**** ERROR PNCCONF- PWM type not recognized in open loop test"
                    return
                halrun.write("setp %s %d \n"%  (self.pwm +".output-type", pulsetype))
                halrun.write("net enable %s \n"%  (self.pwm +".enable"))
                halrun.write("setp %s \n"%  (self.pwm +".scale %f"% dac_scale))
                ending = ".value"
                pwminvertlist = self.a.pwmgen_invert_pins(pwm_sig)
                for i in pwminvertlist:
                    halrun.write("setp    "+i+".invert_output true\n")

            else: # sserial PWM
                pwm_enable = self.d.make_pinname(pwm_sig,False,True) # get prefix only
                if 'analogout5' in self.pwm:
                    enable ='spinena'
                else:
                    enable ='analogena'
                halrun.write("net enable %s \n"%  (pwm_enable + enable))
                halrun.write("setp   "+self.pwm+"-minlim   %.1f\n"% pwmminlimit)
                halrun.write("setp   "+self.pwm+"-maxlim   %.1f\n"% pwmmaxlimit)
                halrun.write("setp   "+self.pwm+"-scalemax %.1f\n"% pwmmaxoutput)
                ending = ""
            halrun.write("net dac %s \n"%  (self.pwm + ending))
            halrun.write("loadusr halmeter -s pin %s -g 550 500 330\n"%  (self.pwm + ending))
            halrun.write("loadusr halmeter pin %s -g 550 375\n"% (self.pwm + ending) )
            halrun.write("loadusr halmeter -s sig enable -g 0 475 330\n")

        # set up encoder     
        if self.enc:
            print self.enc
            halrun.write("net enc-reset %s \n"%  (self.enc +".reset"))
            halrun.write("setp %s.scale %f \n"%  (self.enc, enc_scale))
            halrun.write("setp %s \n"%  (self.enc +".filter true"))
            halrun.write("loadusr halmeter -s pin %s -g 550 550 330\n"%  (self.enc +".position"))
            halrun.write("loadusr halmeter -s pin %s -g 550 600 330\n"%  (self.enc +".velocity"))
        # set up resolver
        if self.res:
            halrun.write("net resolver-reset %s \n"%  (self.res +".reset"))
            halrun.write("setp %s.scale %f \n"%  (self.res, enc_scale))

        widgets.openloopdialog.set_title(_("%s Axis Test") % axis.upper())
        widgets.openloopdialog.move(550,0)
        self.jogplus = self.jogminus = self.enc_reset = self.res_reset = self.enable_amp = 0
        self.axis_under_test = axis
        widgets.testinvertmotor.set_active(widgets[axis+"invertmotor"].get_active())
        widgets.testinvertencoder.set_active(widgets[axis+"invertencoder"].get_active())
        widgets.testenc_scale.set_value(float(enc_scale))
        widgets.fastdac.set_range(0,max_dac)
        widgets.slowdac.set_range(0,max_dac)
        self.update_axis_params()      
        halrun.write("start\n"); halrun.flush()
        self.w['window1'].set_sensitive(0)
        self.w.jogminus.set_sensitive(0)
        self.w.jogplus.set_sensitive(0)
        widgets.openloopdialog.show_all()
        result = widgets.openloopdialog.run()

        widgets.openloopdialog.hide()
        time.sleep(.001)
        halrun.close()        
        if result == gtk.RESPONSE_OK:
            #widgets[axis+"maxacc"].set_text("%s" % widgets.testacc.get_value())
            widgets[axis+"invertmotor"].set_active(widgets.testinvertmotor.get_active())
            widgets[axis+"invertencoder"].set_active(widgets.testinvertencoder.get_active())
            widgets[axis+"encoderscale"].set_value(widgets.testenc_scale.get_value())
            #widgets[axis+"maxvel"].set_text("%s" % widgets.testvel.get_value())
        self.axis_under_test = None
        self.w['window1'].set_sensitive(1)
    
    def update_axis_params(self, *args):
        def get_value(d):
            return self.a.get_value(d)
        axis = self.axis_under_test
        if axis is None: return
        halrun = self.halrun
        enc_scale = self.w.testenc_scale.get_value()
        if self.w.testinvertencoder.get_active() == True: 
            enc_invert = -1
        else: 
            enc_invert = 1
        if self.w.Dac_speed_fast.get_active() == True:
            output = get_value(self.w.fastdac)
        else: 
            output = get_value(self.w.slowdac)
        if self.jogminus == 1:
            output = output * -1
        elif not self.jogplus == 1:
            output = 0
        invertmotor = self.w.testinvertmotor.get_active()
        output += get_value(self.w.testoutputoffset)
        halrun.write("sets enable %d\n"% ( self.enable_amp))
        halrun.write("sets enable-not %d\n"% ( not(self.enable_amp)))
        halrun.write("sets estop-out %d\n"% ( self.enable_amp))
        if invertmotor:
            output = output * -1
        if self.enc:
            halrun.write("""setp %(scalepin)s.scale %(scale)f\n""" % { 'scalepin':self.enc, 'scale': (enc_scale * enc_invert)})
            halrun.write("""sets enc-reset %(reset)d\n""" % { 'reset': self.enc_reset})
        if self.res:
            halrun.write("""setp %(scalepin)s.scale %(scale)f\n""" % { 'scalepin':self.res, 'scale': (enc_scale * enc_invert)})
            halrun.write("""sets resolver-reset %(reset)d\n""" % { 'reset': self.res_reset})
        if self.pwm:
            halrun.write("""sets dac %(output)f\n""" % { 'output': output})
        if self.pot:
            halrun.write("""sets dac %(output)f\n""" % { 'output': abs(output)})
            if output == 0:
                halrun.write("sets dir false\n")
                halrun.write("sets dir-not false\n")
            elif output < 0:
                halrun.write("sets dir true\n")
                halrun.write("sets dir-not false\n")
            else:
                halrun.write("sets dir false\n")
                halrun.write("sets dir-not true\n")
        halrun.flush()

    def oloop_jogminus(self, direction):
        self.jogminus = direction
        self.update_axis_params()
    def oloop_jogplus(self, direction):
        self.jogplus = direction
        self.update_axis_params()

    def oloop_resetencoder(self, state):
        self.enc_reset = self.res_reset = state
        self.update_axis_params()

    def oloop_enableamp(self):
        self.enable_amp = self.enable_amp * -1 + 1
        self.w.jogminus.set_sensitive(self.enable_amp)
        self.w.jogplus.set_sensitive(self.enable_amp)
        self.update_axis_params()

    def hal_test_signals(self, axis):
        # during testing pncconf looks for pins with these signals names
        # and connects to them so as to enable amps etc
        # force-pin-true will just make the pin be true all the time
        # this could be used as a temparary way to enable I/O that the
        # specific machine needs on for the amp to work but pncconf doesn't look for.
        if not axis == "s":
            signallist = ((axis+"-enable"),"machine-is-enabled","estop-out","charge-pump","force-pin-true")
        else:
            signallist = ("spindle-cw","spindle-ccw","spindle-brake","spindle-on","machine-is-enabled",
                            "estop-out","charge-pump","force-pin-true")
        halrun = self.halrun
        def write_pins(pname,p,i,t):
            if p in signallist:
                pinname  = self.d.make_pinname(pname)
                if pinname:
                    #print p, pname, i
                    if p == "estop-out": signal = p
                    elif p == "spindle-cw": signal = "dir"
                    elif p == "spindle-ccw": signal = "dir-not"
                    elif p == "spindle-brake": signal = "enable-not"
                    else: signal = "enable"
                    print pinname, p
                    if "parport" in pinname:
                        if p == "force-pin-true":
                            halrun.write("setp %s true\n"% (pinname))
                        else:
                            halrun.write("net %s %s \n"% (signal,pinname))
                    else:
                        if not "sserial" in pname: # mainboard GPIO need to be set to output/opendrain
                            halrun.write("setp %s true\n"% (pinname + ".is_output"))
                            if t == _PD.GPIOD: halrun.write("setp    "+pinname+".is_opendrain  true\n")
                        if "sserial" in pname and "dig" in pinname: ending = ".out" # 7i76 sserial board
                        elif "sserial" in pname: ending = "" # all other sserial
                        elif not "sserial" in pname: ending =".out" # mainboard GPIO
                        if p == "force-pin-true":
                            halrun.write("setp %s true\n"% ((pinname + ending)))
                        else:
                            halrun.write("net %s %s \n"% (signal,(pinname + ending)))
                    if i: # invert pin
                        if "sserial" in pname and "dig" in pinname: ending = ".invert" # 7i76 sserial board
                        elif "sserial" in pname or "parport" in pinname: ending = "-invert"# all other sserial or parport
                        else: ending = ".invert_output" # mainboard GPIO
                        halrun.write("setp %s true\n"%  (pinname + ending ))
                    return

        # search everything for multiple same named signal output pins
        # mesa mainboard
        for boardnum in range(0,int(self.d.number_mesa)):
            for concount,connector in enumerate(self.d["mesa%d_currentfirmwaredata"% (boardnum)][_PD._NUMOFCNCTRS]) :
                for pin in range(0,24):
                    pname = 'mesa%dc%dpin%d' % (boardnum,connector, pin)
                    p = self.d['mesa%dc%dpin%d' % (boardnum,connector, pin)]
                    i = self.d['mesa%dc%dpin%dinv' % (boardnum,connector, pin)]
                    t = self.d['mesa%dc%dpin%dtype' % (boardnum,connector, pin)]
                    if t in (_PD.GPIOO,_PD.GPIOD) and not p == "unused-output":
                        write_pins(pname,p,i,t)
            # mesa sserial
            if self.d["mesa%d_numof_sserialports"% (boardnum)]: # only check if we have sserialports
                port = 0
                for channel in range (0,self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._MAXSSERIALCHANNELS]):
                    if channel >4: break # TODO only have 5 channels worth of glade widgets
                    for pin in range (0,_PD._SSCOMBOLEN):
                        pname = 'mesa%dsserial%d_%dpin%d' % (boardnum,port,channel,pin)
                        p = self.d['mesa%dsserial%d_%dpin%d' % (boardnum,port,channel,pin)]
                        i = self.d['mesa%dsserial%d_%dpin%dinv' % (boardnum,port,channel,pin)]
                        t = self.d['mesa%dsserial%d_%dpin%dtype' % (boardnum,port,channel,pin)]
                        if t in (_PD.GPIOO,_PD.GPIOD) and not p == "unused-output":
                            write_pins(pname,p,i,t)
        # parports
        templist = ("pp1","pp2","pp3")
        for j, k in enumerate(templist):
            if self.d.number_pports < (j+1): break 
            for x in (1,2,3,4,5,6,7,8,9,14,16,17):
                pname = "%s_Opin%d" % (k, x)
                p = self.d[pname]
                i = self.d[pname+"_inv"]
                if not p == "unused-output":
                    write_pins(pname,p,i,None)

    def hal_cmnds(self,command ):
        halrun = self.halrun
        if command == "LOAD":
            halrun.write("loadrt probe_parport\n")
            # parport stuff
            if self.d.number_pports>0:
                port3name = port2name = port1name = port3dir = port2dir = port1dir = ""
                if self.d.number_pports>2:
                     port3name = " " + self.d.ioaddr3
                     if self.d.pp3_direction:
                        port3dir =" out"
                     else: 
                        port3dir =" in"
                if self.d.number_pports>1:
                     port2name = " " + self.d.ioaddr2
                     if self.d.pp2_direction:
                        port2dir =" out"
                     else: 
                        port2dir =" in"
                port1name = self.d.ioaddr1
                if self.d.pp1_direction:
                   port1dir =" out"
                else: 
                   port1dir =" in"
                halrun.write("loadrt hal_parport cfg=\"%s%s%s%s%s%s\"\n" % (port1name, port1dir, port2name, port2dir, port3name, port3dir))
            # mesa stuff
            halrun.write("loadrt hostmot2\n")
            board0 = self.d.mesa0_currentfirmwaredata[_PD._BOARDNAME]
            board1 = self.d.mesa1_currentfirmwaredata[_PD._BOARDNAME]
            driver0 = self.d.mesa0_currentfirmwaredata[_PD._HALDRIVER]
            driver1 = self.d.mesa1_currentfirmwaredata[_PD._HALDRIVER]
            directory0 = self.d.mesa0_currentfirmwaredata[_PD._DIRECTORY]
            directory1 = self.d.mesa1_currentfirmwaredata[_PD._DIRECTORY]
            firm0 = self.d.mesa0_currentfirmwaredata[_PD._FIRMWARE]
            firm1 = self.d.mesa1_currentfirmwaredata[_PD._FIRMWARE]
            firmstring0 = firmstring1 = ""
            if not "5i25" in board0:
                firmstring0 = "firmware=hm2/%s/%s.BIT" % (directory0, firm0)
            if not "5i25" in board1:
                firmstring1 = "firmware=hm2/%s/%s.BIT" % (directory1, firm1)
            # TODO fix this hardcoded hack: only one serialport
            ssconfig0 = ssconfig1 = resolver0 = resolver1 = temp = ""
            if self.d.mesa0_numof_sserialports:
                for i in range(1,9):
                    if i <= self.d.mesa0_numof_sserialchannels:
                        # if m1 in the name then it needs mode 1
                        if "m1" in self.d["mesa0sserial0_%dsubboard"% (i-1)]:
                            temp = temp + "1"
                        else:
                            temp = temp + "0"
                    else:
                        temp = temp + "x"
                ssconfig0 = "sserial_port_0=%s"% temp
            if self.d.mesa1_numof_sserialports:
                for i in range(1,9):
                    if i <= self.d.mesa1_numof_sserialchannels:
                        # if m1 in the name then it needs mode 1
                        if "m1" in self.d["mesa1sserial1_%dsubboard"% (i-1)]:
                            temp = temp + "1"
                        else:
                            temp = temp + "0"
                    else:
                        temp = temp + "x"
                ssconfig1 = "sserial_port_0=%s"% temp
            if self.d.mesa0_numof_resolvers:
                resolver0 = "num_resolvers=%d"% self.d.mesa0_numof_resolvers
            if self.d.mesa1_numof_resolvers:
                resolver1 = "num_resolvers=%d"% self.d.mesa1_numof_resolvers

            if self.d.number_mesa == 1:            
                halrun.write( """loadrt %s config="%s num_encoders=%d num_pwmgens=%d num_3pwmgens=%d num_stepgens=%d %s %s"\n """ % (
                    driver0, firmstring0, self.d.mesa0_numof_encodergens, self.d.mesa0_numof_pwmgens, self.d.mesa0_numof_tppwmgens, self.d.mesa0_numof_stepgens, ssconfig0, resolver0))
            elif self.d.number_mesa == 2 and (driver0 == driver1):
                halrun.write( """loadrt %s config="%s num_encoders=%d num_pwmgens=%d num_3pwmgens=%d num_stepgens=%d %s %s,\
                                %s num_encoders=%d num_pwmgens=%d num_3pwmgens=%d num_stepgens=%d %s %s"\n""" % (
                    driver0, firmstring0, self.d.mesa0_numof_encodergens, self.d.mesa0_numof_pwmgens, self.d.mesa0_numof_tppwmgens,
                        self.d.mesa0_numof_stepgens, ssconfig0, resolver0, firmstring1, self.d.mesa1_numof_encodergens,
 self.d.mesa1_numof_pwmgens, self.d.mesa1_numof_tppwmgens,self.d.mesa1_numof_stepgens, ssconfig1, resolver1))
            elif self.d.number_mesa == 2:
                halrun.write( """loadrt %s config="%s num_encoders=%d num_pwmgens=%d num_3pwmgens=%d num_stepgens=%d" %s %s\n """ % (
                    driver0, firmstring0, self.d.mesa0_numof_encodergens, self.d.mesa0_numof_pwmgens, self.d.mesa0_numof_tppwmgens, self.d.mesa0_numof_stepgens, ssconfig0, resolver0 ))
                halrun.write( """loadrt %s config="%s num_encoders=%d num_pwmgens=%d num_3pwmgens=%d num_stepgens=%d %s %s"\n """ % (
                    driver1, firmstring1, self.d.mesa1_numof_encodergens, self.d.mesa1_numof_pwmgens, self.d.mesa0_numof_tppwmgens, self.d.mesa1_numof_stepgens, ssconfig1, resolver1 ))
            for boardnum in range(0,int(self.d.number_mesa)):
                if boardnum == 1 and (board0 == board1):
                    halnum = 1
                else:
                    halnum = 0
                if self.d["mesa%d_numof_pwmgens"% boardnum] > 0:
                    halrun.write( "    setp hm2_%s.%d.pwmgen.pwm_frequency %d\n"% (
                     self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME],halnum, self.d["mesa%d_pwm_frequency"% boardnum] ))
                    halrun.write( "    setp hm2_%s.%d.pwmgen.pdm_frequency %d\n"% ( 
                    self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME], halnum,self.d["mesa%d_pdm_frequency"% boardnum] ))
                halrun.write( "    setp hm2_%s.%d.watchdog.timeout_ns %d\n"% ( 
                    self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME], halnum,self.d["mesa%d_watchdog_timeout"% boardnum] ))  
        if command == "READ":
            if self.d.number_pports > 0:
                halrun.write( "addf parport.0.read base-thread\n")
            if self.d.number_pports > 1:
                halrun.write( "addf parport.1.read base-thread\n")
            if self.d.number_pports > 2:
                halrun.write( "addf parport.2.read base-thread\n")
            for boardnum in range(0,int(self.d.number_mesa)):
                if boardnum == 1 and (self.d.mesa0_currentfirmwaredata[_PD._BOARDNAME] == self.d.mesa1_currentfirmwaredata[_PD._BOARDNAME]):
                    halnum = 1
                else:
                    halnum = 0         
                halrun.write( "addf hm2_%s.%d.read servo-thread\n"% (self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME], halnum))
                halrun.write( "addf hm2_%s.%d.pet_watchdog  servo-thread\n"% (self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME], halnum))
        if command == "WRITE":
            if self.d.number_pports > 0:
                halrun.write( "addf parport.0.write base-thread\n")
            if self.d.number_pports > 1:
                halrun.write( "addf parport.1.write base-thread\n")
            if self.d.number_pports > 2:
                halrun.write( "addf parport.2.write base-thread\n")
            for boardnum in range(0,int(self.d.number_mesa)):
                if boardnum == 1 and (self.d.mesa0_currentfirmwaredata[_PD._BOARDNAME] == self.d.mesa1_currentfirmwaredata[_PD._BOARDNAME]):
                    halnum = 1
                else:
                    halnum = 0         
                halrun.write( "addf hm2_%s.%d.write servo-thread\n"% (self.d["mesa%d_currentfirmwaredata"% boardnum][_PD._BOARDNAME], halnum))


    def launch_mesa_panel(self):
        if not self.a.check_for_rt(): return
        if not self.a.warning_dialog(_("Do to technical reasons this test panel can be loaded only once without reloading pncconf.\
You also will not be able to do any other testing untill you reload pncconf and quite possibly open a terminal and type 'halrun -U' \
I hesitate to even allow it's use but at times it's very useful.\nDo you wish to continue the test?"),False):
                        return
        self.halrun = os.popen("halrun -Is > /dev/null", "w") 
        self.halrun.write("loadrt threads period1=50000 name1=base-thread fp1=0 period2=1000000 name2=servo-thread\n")
        self.hal_cmnds("LOAD")
        self.hal_cmnds("READ")
        self.hal_cmnds("WRITE")
        self.halrun.write("start\n")
        self.halrun.write("loadusr  halmeter\n")
        self.halrun.flush()
        time.sleep(1)
        try:
            PyApp(self,self.d,self.widgets)  
        except:
            self.halrun.close()
            a = os.popen("halrun -U > /dev/null", "w")
            a.flush()
            time.sleep(1)
            a.close()
            a.kill()
            
    def on_mesapanel_returned(self, *args):
        #print "Quit test panel"
        try:
            self.halrun.write("delsig all\n")
            self.halrun.write("exit\n")
            self.halrun.flush()
            time.sleep(1)
            self.halrun.close()
            a = os.popen("halrun -U > /dev/null", "w")
            a.flush()
            time.sleep(1)
            a.close()
            a.kill()
        except :
            pass
#***************************************************************
# testpanel code
class hal_interface:
    def __init__(self):  
        try: 
            self.c = hal.component("testpanel")      
        except:
            print"problem in HAL routine"
class Data2:
    def __init__(self):
        self.inv = []
        self.swch = []
        self.led = []
        self.enc = []
        self.pwm = []
        self.stp = []
    def __getitem__(self, item):
        return getattr(self, item)
    def __setitem__(self, item, value):
        return setattr(self, item, value)

class LED(gtk.DrawingArea):

    def __init__(self, parent):
        self.par = parent       
        super(LED, self).__init__() 
        self._dia = 10
        self._state = 0
        self._on_color = [0.3, 0.4, 0.6]
        self._off_color = [0.9, 0.1, 0.1]
        self.set_size_request(25, 25)
        self.connect("expose-event", self.expose)
        

    # This method draws our widget
    # it draws a black circle for a rim around LED
    # Then depending on self.state
    # fills in that circle with on or off color.
    # the dim depends on self.diam
    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_line_width(3)
        #cr.set_source_rgb(0, 0, 0.0)    
        self.set_size_request(25, 25)  
        #cr.set_source_rgb(0, 0, 0.0)    
        #self.set_size_request(self._dia*2+5, self._dia*2+5) 
        w = self.allocation.width
        h = self.allocation.height
        cr.translate(w/2, h/2)
        #cr = widget.window.cairo_create()
        lg2 = cairo.RadialGradient(0, 0, 0,  0, 0, self._dia)
        if self._state:
            r = self._on_color[0]
            g = self._on_color[1]
            b = self._on_color[2]
        else:
            r = self._off_color[0]
            g = self._off_color[1]
            b = self._off_color[2]
        lg2.add_color_stop_rgba(1, r/.25,g/.25,b/.25, 1)
        lg2.add_color_stop_rgba(.5, r,g,b, .5)
        #lg2.add_color_stop_rgba(0, 0, 0, 0, 1)
        cr.arc(0, 0, self._dia, 0, 2*math.pi)
        cr.stroke_preserve()
        #cr.rectangle(20, 20, 300, 100)
        cr.set_source(lg2)
        cr.fill()

        return False
      
    # This sets the LED on or off
    # and then redraws it
    # Usage: ledname.set_active(True) 
    def set_active(self, data2 ):
        self._state = data2
        self.queue_draw()
    
    # This allows setting of the on and off color
    # Usage: ledname.set_color("off",[r,g,b])
    def set_color(self, state, color = [0,0,0] ):
        if state == "off":
            self._off_color = color
        elif state == "on":
            self._on_color = color
        else:
            return

    def set_dia(self, dia):
        self._dia = dia
        self.queue_draw()
 
class PyApp(gtk.Window): 

    def switch_callback(self, widget, component , boardnum,number, data=None):   
        print component,boardnum,number,data
        if component == "switch":
            invrt = self.data2["brd%dinv%d" % (boardnum,number)].get_active()
            if (data and not invrt ) or (not data and invrt):
                self.hal.c["brd.%d.switch.%d"% (boardnum, number)] = True
            else:
                self.hal.c["brd.%d.switch.%d"% (boardnum, number)] = False
        if component == "invert":
            self.switch_callback(None,"switch",boardnum,number,False)

    def pwm_callback(self, widget, component , boardnum,number, data=None):
        if component == "pwm":
            value = self.data2["brd%dpwm%dadj" % (boardnum,number)].get_value()
            active = self.data2["brd%dpmw_ckbutton%d"% (boardnum,number)].get_active()
            self.hal.c["brd.%d.pwm.%d.enable"% (boardnum, number)] = active
            if active:
                self.hal.c["brd.%d.pwm.%d.value"% (boardnum, number)] = value
            else:
                 self.hal.c["brd.%d.pwm.%d.value"% (boardnum, number)] = 0
    
    def stp_callback(self, widget, component , boardnum,number, data=None):
        if component == "stp":
            value = self.data2["brd%dstp%dcmd" % (boardnum,number)].get_value()
            active = self.data2["brd%dstp_ckbutton%d"% (boardnum,number)].get_active()
            self.hal.c["brd.%d.stp.%d.enable"% (boardnum, number)] = active
            if active:
                self.hal.c["brd.%d.stp.%d.position-cmd"% (boardnum, number)] = value
            

    def quit(self,widget):  
        self.w['window1'].set_sensitive(1)                 
        gobject.source_remove(self.timer)
        self.hal.c.exit()
        self.app.on_mesapanel_returned()
        return True

    def update(self):      
        if hal.component_exists("testpanel"):
            for i in (0,1):
                for j in range(0,72):
                    try:
                        self.data2["brd%dled%d"%(i,j)].set_active(self.hal.c["brd.%d.led.%d"% (i,j)]) 
                    except :
                        continue    
                for k in range(0,16):
                    try:
                        self.data2["brd%denc%dcount"%(i,k)].set_text("%s"% str(self.hal.c["brd.%d.enc.%d.count"% (i,k)])) 
                    except :
                        continue 
            return True # keep running this event
        else:
            return False # kill the event

    # This creates blank labels for placemarks for components
    # such as encoders that use 3 or 4 pins as input
    # but only need one line for user interaction
    # this keeps the page uniform
    def make_blank(self,container,boardnum,number):
        #blankname = "enc-%d" % (number)
        #self.data2["brd%denc%d" % (boardnum,number)]= gtk.Button("Reset-%d"% number)
        #self.hal.c.newpin(encname, hal.HAL_S32, hal.HAL_IN)
        label = gtk.Label("     ")
        container.pack_start(label, False, False, 10)
        label = gtk.Label("      ")
        container.pack_start(label, False, False, 10)
  
    # This creates widgets and HAL pins for encoder controls
    def make_enc(self,container,boardnum,number):
        encname = "brd.%d.enc.%d.reset" % (boardnum,number)   
        print"making HAL pin enc bit Brd %d,num %d"%(boardnum,number)   
        self.hal.c.newpin(encname, hal.HAL_BIT, hal.HAL_OUT)
        hal.new_sig(encname+"-signal",hal.HAL_BIT)
        hal.connect("testpanel."+encname,encname+"-signal")
        self.data2["brd%denc%dreset" % (boardnum,number)]= gtk.Button("Reset-%d"% number)
        container.pack_start(self.data2["brd%denc%dreset" % (boardnum,number)], False, False, 10)
        encname = "brd.%d.enc.%d.count" % (boardnum,number)
        print"making HAL pin enc s32 brd %d num %d"%(boardnum,number)      
        self.hal.c.newpin(encname, hal.HAL_S32, hal.HAL_IN)
        hal.new_sig(encname+"-signal",hal.HAL_S32)
        hal.connect("testpanel."+encname,encname+"-signal")
        label = self.data2["brd%denc%dcount" % (boardnum,number)] = gtk.Label("Encoder-%d"% (number))
        label.set_size_request(100, -1)
        container.pack_start(label, False, False, 10)
    
    # This creates widgets and HAL pins for stepper controls 
    def make_stp(self,container,boardnum,number):
        stpname = "brd.%d.stp.%d.position-cmd" % (boardnum,number)
        self.hal.c.newpin(stpname, hal.HAL_FLOAT, hal.HAL_OUT)
        hal.new_sig(stpname+"-signal",hal.HAL_FLOAT)
        hal.connect("testpanel."+stpname,stpname+"-signal")
        stpname = "brd.%d.stp.%d.enable" % (boardnum,number)
        self.hal.c.newpin(stpname, hal.HAL_BIT, hal.HAL_OUT)
        hal.new_sig(stpname+"-signal",hal.HAL_BIT)
        hal.connect("testpanel."+stpname,stpname+"-signal")
        adj = gtk.Adjustment(0.0, -1000.0, 1000.0, 1.0, 5.0, 0.0)
        spin = self.data2["brd%dstp%dcmd" % (boardnum,number)]= gtk.SpinButton(adj, 0, 1)  
        adj.connect("value_changed", self.stp_callback,"stp",boardnum,number,None)    
        container.pack_start(spin, False, False, 10)
        ckb = self.data2["brd%dstp_ckbutton%d"% (boardnum,number)] = gtk.CheckButton("Enable %d"% (number))
        ckb.connect("toggled", self.stp_callback, "stp",boardnum,number,None)
        container.pack_start(ckb, False, False, 10)
        

    # This places a spinbox for pwm value and a checkbox to enable pwm
    # It creates two HAL pins
    def make_pwm(self,container,boardnum,number):
        pwmname = "brd.%d.pwm.%d.value" % (boardnum,number)
        print"making HAL pin pwm float brd%d num %d"%(boardnum,number)
        self.hal.c.newpin(pwmname, hal.HAL_FLOAT, hal.HAL_OUT)
        hal.new_sig(pwmname+"-signal",hal.HAL_FLOAT)
        hal.connect("testpanel."+pwmname,pwmname+"-signal")
        pwmname = "brd.%d.pwm.%d.enable" % (boardnum,number)
        print"making HAL pin pwm bit brd %d num %d"%(boardnum,number)
        self.hal.c.newpin(pwmname, hal.HAL_BIT, hal.HAL_OUT)
        hal.new_sig(pwmname+"-signal",hal.HAL_BIT)
        hal.connect("testpanel."+pwmname,pwmname+"-signal")
        adj = self.data2["brd%dpwm%dadj" % (boardnum,number)] = gtk.Adjustment(0.0, -10.0, 10.0, 0.1, 0.5, 0.0)
        adj.connect("value_changed", self.pwm_callback,"pwm",boardnum,number,None)      
        pwm = self.data2["brd%dpwm%d" % (boardnum,number)] = gtk.HScale(adj)
        pwm.set_digits(1)
        pwm.set_size_request(100, -1)      
        container.pack_start(pwm, False, False, 10)        
        ckb = self.data2["brd%dpmw_ckbutton%d"% (boardnum,number)] = gtk.CheckButton("PWM-%d\nON"% (number))
        ckb.connect("toggled", self.pwm_callback, "pwm",boardnum,number,None)
        container.pack_start(ckb, False, False, 10)
    
    # This places a LED and a label in specified container
    # it specifies the led on/off colors
    # and creates a HAL pin
    def make_led(self,container,boardnum,number):
        ledname = "brd.%d.led.%d" % (boardnum,number)
        print"making HAL pin led bit brd %d num %d"%(boardnum,number)
        self.hal.c.newpin(ledname, hal.HAL_BIT, hal.HAL_IN)
        hal.new_sig(ledname+"-signal",hal.HAL_BIT)
        hal.connect("testpanel."+ledname,ledname+"-signal")
        led = self.data2["brd%dled%d" % (boardnum,number)] = LED(self)
        led.set_color("off",[1,0,0]) # red
        led.set_color("on",[0,1,0]) # Green
        container.pack_start(led, False, False, 10)
        label = gtk.Label("<--GPIO-%d"% (number))
        container.pack_start(label, False, False, 10)

    # This is for placing a button (switch) and an invert check box into
    # a specified container. It also creates the HAL pin
    # and connects some signals. 
    def make_switch(self,container,boardnum,number):
        # make a HAL pin
        switchname = "brd.%d.switch.%d" % (boardnum,number)
        print"making HAL pin switch bit brd %d num %d"%(boardnum,number)
        self.hal.c.newpin(switchname, hal.HAL_BIT, hal.HAL_OUT)
        hal.new_sig(switchname+"-signal",hal.HAL_BIT)
        hal.connect("testpanel."+switchname,switchname+"-signal")
        # add button to container using boarnum and number as a reference     
        button = self.data2["brd%dswch%d" % (boardnum,number)]= gtk.Button("OUT-%d"% number)
        container.pack_start(button, False, False, 10)
        # connect signals
        button.connect("pressed", self.switch_callback, "switch",boardnum,number,True)
        button.connect("released", self.switch_callback, "switch",boardnum,number,False) 
        # add invert switch
        ckb = self.data2["brd%dinv%d" % (boardnum,number)]= gtk.CheckButton("Invert")
        container.pack_start(ckb, False, False, 10) 
        ckb.connect("toggled", self.switch_callback, "invert",boardnum,number,None)
    
    def __init__(self,App,data,widgets):
        super(PyApp, self).__init__()
        #print "init super pyapp"
        self.data2 = Data2()
        self.d = data
        self.app = App
        self.w = widgets
        #self.halrun = self.app.halrun
        #print "entering HAL init"
        self.hal = hal_interface()
        #print "done HAL init"
        self.set_title("Mesa Test Panel")
        self.set_size_request(450, 450)        
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect_after("destroy", self.quit)
        self.timer = gobject.timeout_add(100, self.update)
        #print "added timer"
        brdnotebook = gtk.Notebook()
        brdnotebook.set_tab_pos(gtk.POS_TOP)
        brdnotebook.show()
        self.add(brdnotebook)             
        
        for boardnum in range(0,int(self.d.number_mesa)):
            board = self.d["mesa%d_currentfirmwaredata"% (boardnum)][_PD._BOARDNAME]+".%d"% boardnum
            self.data2["notebook%d"%boardnum] = gtk.Notebook()
            self.data2["notebook%d"%boardnum].set_tab_pos(gtk.POS_TOP)
            self.data2["notebook%d"%boardnum].show()
            label = gtk.Label("Mesa Board Number %d"% (boardnum))      
            brdnotebook.append_page(self.data2["notebook%d"%boardnum], label)
            for concount,connector in enumerate(self.d["mesa%d_currentfirmwaredata"% (boardnum)][_PD._NUMOFCNCTRS]) :
                table = gtk.Table(12, 3, False)
                seperator = gtk.VSeparator()
                table.attach(seperator, 1, 2, 0, 12,True)
                for pin in range (0,24):
                    if pin >11:
                        column = 2
                        adjust = -12    
                    else:
                        column = 0
                        adjust = 0
                    firmptype,compnum = self.d["mesa%d_currentfirmwaredata"% (boardnum)][_PD._STARTOFDATA+pin+(concount*24)]
                    pinv = 'mesa%dc%dpin%dinv' % (boardnum,connector,pin)
                    ptype = 'mesa%dc%dpin%dtype' % (boardnum,connector,pin)
                    pintype = self.w[ptype].get_active_text()
                    pininv = self.w[pinv].get_active()
                    truepinnum = (concount*24) + pin
                    # for output / open drain pins
                    if  pintype in (_PD.GPIOO,_PD.GPIOD): 
                        h = gtk.HBox(False,2)
                        self.make_switch(h,boardnum,truepinnum)
                        table.attach(h, 0 + column, 1 + column, pin + adjust, pin +1+ adjust,True)
                        hal.set_p("hm2_%s.gpio.%03d.is_output"% (board,truepinnum ),"true")
                        if pininv:  hal.set_p("hm2_%s.gpio.%03d.invert_output"% (board,truepinnum ),"true")
                        hal.connect("hm2_%s.gpio.%03d.out"% (board,truepinnum ),"brd.%d.switch.%d-signal" % (boardnum,truepinnum))
                    # for input pins
                    elif pintype == _PD.GPIOI: 
                        h = gtk.HBox(False,2)
                        self.make_led(h,boardnum,truepinnum)
                        table.attach(h, 0 + column, 1 + column, pin + adjust, pin +1+ adjust,True)
                        if pininv: hal.connect("hm2_%s.gpio.%03d.in_not"% (board,truepinnum),"brd.%d.led.%d-signal"% (boardnum,truepinnum))
                        else:   hal.connect("hm2_%s.gpio.%03d.in"% (board,truepinnum),"brd.%d.led.%d-signal"% (boardnum,truepinnum))
                    # for encoder pins
                    elif pintype in (_PD.ENCA,_PD.ENCB,_PD.ENCI,_PD.ENCM):
                        h = gtk.HBox(False,2)
                        if pintype == _PD.ENCA:
                            self.make_enc(h,boardnum,compnum)
                            hal.connect("hm2_%s.encoder.%02d.reset"% (board,compnum), "brd.%d.enc.%d.reset-signal"% (boardnum,compnum))
                            hal.connect("hm2_%s.encoder.%02d.count"% (board,compnum), "brd.%d.enc.%d.count-signal"% (boardnum,compnum))
                        else:
                            self.make_blank(h,boardnum,compnum)
                        table.attach(h, 0 + column, 1 + column, pin + adjust, pin +1+ adjust,True)
                    # for PWM pins
                    elif pintype in (_PD.PWMP,_PD.PWMD,_PD.PWME,_PD.PDMP,_PD.PDMD,_PD.PDME,_PD.UDMD,_PD.UDME):
                        h = gtk.HBox(False,2)
                        if pintype in (_PD.PWMP,_PD.PDMP,_PD.UDMU):
                            self.make_pwm(h,boardnum,compnum)
                            hal.connect("hm2_%s.pwmgen.%02d.enable"% (board,compnum),"brd.%d.pwm.%d.enable-signal"% (boardnum,compnum)) 
                            hal.connect("hm2_%s.pwmgen.%02d.value"% (board,compnum),"brd.%d.pwm.%d.value-signal"% (boardnum,compnum)) 
                            hal.set_p("hm2_%s.pwmgen.%02d.scale"% (board,compnum),"10") 
                        else:
                            self.make_blank(h,boardnum,compnum)
                        table.attach(h, 0 + column, 1 + column, pin + adjust, pin +1+ adjust,True)
                    # for Stepgen pins
                    elif pintype in (_PD.STEPA,_PD.STEPB):
                        h = gtk.HBox(False,2)
                        if pintype == _PD.STEPA:          
                            self.make_stp(h,boardnum,compnum)
                            hal.connect("hm2_%s.stepgen.%02d.enable"% (board,compnum),"brd.%d.stp.%d.enable-signal"% (boardnum,compnum))
                            hal.connect("hm2_%s.stepgen.%02d.position-cmd"% (board,compnum),"brd.%d.stp.%d.position-cmd-signal"% (boardnum,compnum))   
                            hal.set_p("hm2_%s.stepgen.%02d.maxaccel"% (board,compnum),"0")
                            hal.set_p("hm2_%s.stepgen.%02d.maxvel"% (board,compnum),"2000")
                            hal.set_p("hm2_%s.stepgen.%02d.steplen"% (board,compnum),"2000")
                            hal.set_p("hm2_%s.stepgen.%02d.stepspace"% (board,compnum),"2000")
                            hal.set_p("hm2_%s.stepgen.%02d.dirhold"% (board,compnum),"2000")
                            hal.set_p("hm2_%s.stepgen.%02d.dirsetup"% (board,compnum),"2000")
                        else:
                            self.make_blank(h,boardnum,compnum)
                        table.attach(h, 0 + column, 1 + column, pin + adjust, pin +1+ adjust,True)
                    else:
                        print "pintype error IN mesa test panel method pintype %s boardnum %d connector %d pin %d"% (pintype,boardnum,connector,pin)
                label = gtk.Label("Mesa %d-Connector %d"% (boardnum,connector))      
                self.data2["notebook%d"%boardnum].append_page(table, label)
           
        self.show_all() 
        self.w['window1'].set_sensitive(0) 
        self.hal.c.ready()
        
        #print "got to end of panel"

        
        
# testpanel code end
#****************************************************************