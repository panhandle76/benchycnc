#!/usr/bin/env python

import time
import hal
import linuxcnc
import gtk
import gtk.glade


class BlockingWindow():
   def __init__(self, message):
      self.gladefile = "prompt.ui"
      self.glade = gtk.Builder()
      self.glade.add_from_file(self.gladefile)
      self.glade.connect_signals(self)
      self.message = message

   def on_btnOk_clicked(self,button):
      self.glade.get_object("dialog1").hide_all()
      gtk.main_quit()

   def run(self):
      self.glade.get_object("label1").set_text(self.message)
      self.glade.get_object("dialog1").show_all()
      gtk.main()
      self.glade.get_object("dialog1").destroy()
      return None


class AutoToolZero:
   def __init__(self):
      self.gladefile = "autotoolzero.ui"
      self.glade = gtk.Builder()
      self.glade.add_from_file(self.gladefile)
      self.glade.connect_signals(self)

   def __del__(self):
      print("AutoToolZero __del__")

   def on_btnOk_clicked(self, button):
      # get which axis was checked
      self.doX = self.glade.get_object("cbXaxis").get_active()
      self.doY = self.glade.get_object("cbYaxis").get_active()

      # get the position of the probe
      if self.glade.get_object("rbLeftFront").get_active(): 
         self.position = "Left/Front"
      elif self.glade.get_object("rbLeftRear").get_active():
         self.position = "Left/Rear"
      elif self.glade.get_object("rbRightFront").get_active():
         self.position = "Right/Front"
      else:
        self.position = "Right/Rear"

      # get whether to pause
      self.pause = self.glade.get_object("cbPause").get_active()

      # get diameter and divide to get the radius
      diameter = float(self.glade.get_object("txtDiameter").get_text())
      self.radius = diameter/2

      # get unit
      if self.glade.get_object("rbInch").get_active():
         self.unit = "inch"
      else: # self.glade.get_object("rbMM").get_active()
         self.unit = "mm"

      # quit
      gtk.main_quit()

   def on_btnCancel_clicked(self, button):
      gtk.main_quit()

   def run(self):
      self.glade.get_object("window1").show_all()
      gtk.main()
      self.glade.get_object("window1").destroy()
      return {"x":self.doX, "y":self.doY, "position":self.position, "pause":self.pause, "radius":self.radius, "unit":self.unit}


class HandlerClass:

   def __init__(self, halcomp, builder, useropts):
      print("init")
      #self.halcomp = halcomp
      #self.halcomp.newpin("number", hal.HAL_FLOAT, hal.HAL_IN)
      self.touch_plate_height = 1                       # height of touchplate (inch)
      self.touch_plate_width = 2.205                    # width of touchplate (inch) (~56mm)
      self.ztravel_height = 0.125                       # how high to lift tool while probing X and Y (inch)
      self.zlift_height = 0.5                           # how high to lift after probing is done (inch)

   def on_btnAutoToolZero_clicked(self, button):
      # prompt user with dialog
      atz = AutoToolZero()
      values = atz.run()
      print("values="+str(values))
      doX = values["x"]
      doY = values["y"]
      radius = values["radius"]
      unit = values["unit"]

      c = linuxcnc.command()
      c.mode(linuxcnc.MODE_MDI)
      c.wait_complete() # wait for mode switch

      ### set units to inch
      c.mdi("G20")
      c.wait_complete() # wait
      ###
      c.mdi("G90")  # absolute
      c.wait_complete() # wait

      ### probe Z
      b = BlockingWindow("Jog tool over touchplate and Press Ok")
      b.run()
      self.probeZ("Z", radius)

      ### probe X if requested
      if doX:
         b = BlockingWindow("Align Tool Flutes for X-Axis Travel and Press Ok")
         b.run()
         self.probeXY("X", radius)

      ### probe Y if requested
      if doY:
         b = BlockingWindow("Align Tool Flutes for Y-Axis Travel and Press Ok")
         b.run()
         self.probeXY("Y", radius)

      ### move up enough to clear the tool
      c.mdi("G1 Z" + str(1+self.zlift_height) + " F2")
      c.wait_complete() # wait

   def probeZ(self, axis, tool_radius):
      print("probe " + axis + ":" + str(tool_radius));
      c = linuxcnc.command()
      c.mode(linuxcnc.MODE_MDI)
      c.wait_complete() # wait for mode switch
      ### move until we hit the probe
      c.mdi("G38.3 Z-4 F2")
      c.wait_complete() # wait
      ### set the Z offset. This gcode will calculate the necessary Z offset (G54) for a final position of '1'
      c.mdi("G10 L20 P1 Z1")
      c.wait_complete() # wait
      ### move up a little
      c.mdi("G1 Z" + str(1+self.ztravel_height) + " F2")
      c.wait_complete() # wait

   def probeXY(self, axis, tool_radius):
      print("probe " + axis + ":" + str(tool_radius));
      c = linuxcnc.command()
      c.mode(linuxcnc.MODE_MDI)
      c.wait_complete() # wait for mode switch
      ### move toward probe and stop
      c.mdi("G38.3 "+axis+"15 F2")  # 15 is just some large number to move toward. we should hit touch plate before then
      c.wait_complete() # wait
      ### set offset to be (touchprobe width minus tool radius)
      c.mdi("G10 L20 P1 " + axis + str(self.touch_plate_width-tool_radius))
      c.wait_complete() # wait
      ### move back roughly to the center
      c.mdi("G54 G1 " + axis + "1" + " F10")
      c.wait_complete() # wait

def get_handlers(halcomp, builder, useropts):
   return [HandlerClass(halcomp,builder,useropts)]
