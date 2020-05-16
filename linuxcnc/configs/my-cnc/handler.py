#!/usr/bin/env python

import time
import hal
import linuxcnc
import gtk
import gtk.glade

###
### Just for prompting user to do something
###
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


###
### Prompts user for cornerfinder/zero parameters
###
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


###
### Main class for handling button presses on the main screen
###
class HandlerClass:

   def __init__(self, halcomp, builder, useropts):
      print("init")
      #self.halcomp = halcomp
      #self.halcomp.newpin("number", hal.HAL_FLOAT, hal.HAL_IN)
      
      # put in MDI mode
      self.c = linuxcnc.command()
      self.c.mode(linuxcnc.MODE_MDI)
      self.c.wait_complete(30) # wait for mode switch (max 30 seconds)

      self.touch_plate_height = 1                       # height of touchplate (inch)
      self.touch_plate_width = 2.205                    # width of touchplate (inch) (~56mm)
      self.ztravel_height = 0.125                       # how high to lift tool while probing X and Y (inch)
      self.zlift_height = 0.5                           # how high to lift after probing is done (inch)

   def run_mdi(self, command):
      self.c.mdi(command)
      self.c.wait_complete(30)  # wait for 30 seconds

   def move_abs(self, command, axis, feed):
      self.run_mdi("G90")  # absolute
      self.run_mdi(command+" "+axis+" "+feed)

   def move_inc(self, command, axis, feed):
      self.run_mdi("G91")  # incremental
      self.run_mdi(command+" "+axis+" "+feed)

   def on_btnAutoToolZero_clicked(self, button):
      # prompt user with dialog and get the results
      atz = AutoToolZero()
      values = atz.run()
      print("values="+str(values))
      doX = values["x"]
      doY = values["y"]
      radius = values["radius"]
      unit = values["unit"]

      #
      self.run_mdi("G20") # inch

      # probe Z
      b = BlockingWindow("Jog tool over touchplate and Press Ok")
      b.run()
      self.probeZ("Z")

      # probe X if requested
      if doX:
         b = BlockingWindow("Align Tool Flutes for X-Axis Travel and Press Ok")
         b.run()
         self.probeXY("X", radius)

      # probe Y if requested
      if doY:
         b = BlockingWindow("Align Tool Flutes for Y-Axis Travel and Press Ok")
         b.run()
         self.probeXY("Y", radius)

      # move up enough to clear the tool
      self.move_inc("G1", "Z"+str(self.zlift_height), "F2")

   def probeZ(self, axis):
      print("probe " + axis);
      # move until we hit the probe
      self.run_mdi("G38.3 Z-4 F2")
      # set the Z offset. This gcode will calculate the necessary Z offset (G54) for a final position of '1'
      self.run_mdi("G10 L20 P1 Z1")
      # move up a little
      self.move_inc("G1", "Z"+str(self.ztravel_height), "F2")

   def probeXY(self, axis, tool_radius):
      print("probe " + axis + ":" + str(tool_radius));
      self.run_mdi("G91")  # incremental
      # move toward probe and stop
      self.run_mdi("G38.3 "+axis+"2 F2")  # 15 is just some large number to move toward. we should hit touch plate before then
      # set offset to be (touchprobe width minus tool radius)
      self.run_mdi("G10 L20 P1 " + axis + str(self.touch_plate_width-tool_radius))
      # move back roughly to the center
      self.move_inc("G54 G1", axis+"-1", "F10")

def get_handlers(halcomp, builder, useropts):
   return [HandlerClass(halcomp,builder,useropts)]
