import sys
import os
import subprocess
import threading
import json
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load()
        self.set_default_size(600, 250)
        self.set_title("AAXtoMP3")
        
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_margin_top(5)
        self.box.set_margin_bottom(5)
        self.box.set_margin_start(5)
        self.box.set_margin_end(5)
        self.box.set_spacing(5)
        self.set_child(self.box)
        
        # Row 1: AAX File Path #################################################
        # File: ______________________________________________________________ #
        self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.append(self.row1)
        # Label "File: "
        self.file_label = Gtk.Label(label="File: ")
        self.row1.append(self.file_label)
        # Textbox
        self.file_textbox = Gtk.Entry()
        self.file_textbox.set_placeholder_text("Enter .aax file path here...")
        if "path" in self.settings:
            self.file_textbox.set_buffer(Gtk.EntryBuffer.new(self.settings["path"],len(self.settings["path"])))
        self.file_textbox.connect("activate", self.path_chosen)
        self.row1.append(self.file_textbox)
        self.file_textbox.set_hexpand(True)
        
        # Row 2: Format & Compression Level ####################################
        # Format: mp3 v                               Compression level: 0 -|+ #
        # Format: mp4 v                                                        #
        self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.append(self.row2)
        # Label "Format: "
        self.format_label = Gtk.Label(label="Format: ")
        self.row2.append(self.format_label)
        # Dropdown to choose format
        self.formats = ["mp3","m4a","m4b","opus","flac"]
        self.format_calls = ["-e:mp3","-e:m4a","-e:m4b","--opus","--flac"]
        self.format_dropdown = Gtk.DropDown.new_from_strings(self.formats)
        if "format" in self.settings:
            self.format_dropdown.set_selected(self.formats.index(self.settings["format"]))
        self.format_dropdown.connect("notify::selected-item", self.format_chosen)
        self.row2.append(self.format_dropdown)
        # Space
        self.space_holder1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.space_holder1.set_hexpand(True)
        self.row2.append(self.space_holder1)
        # Compression level space holder
        self.clevel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.row2.append(self.clevel_box)
        # Fill compression level space holder if the format supports it
        self.format_chosen(self.format_dropdown, [])
        
        # Row 3: Chaptered & Continue ##########################################
        # Chaptered: (() )                                                     #
        # Chaptered: ( ())                                     Continue: (() ) #
        # Chaptered: ( ())                               Continue: ( ()) 0 -|+ #
        self.row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.append(self.row3)
        # Label "Chaptered: "
        self.chap_label = Gtk.Label(label="Chaptered: ")
        self.row3.append(self.chap_label)
        # Switch
        self.chap_switch = Gtk.Switch()
        if "chaptered" in self.settings:
            self.chap_switch.set_active(self.settings["chaptered"])
        else:
            self.chap_switch.set_active(True)
        self.chap_switch.connect("state-set", self.chap_switched)
        self.row3.append(self.chap_switch)
        # Space
        self.space_holder2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.space_holder2.set_hexpand(True)
        self.row3.append(self.space_holder2)
        # Continue space holder
        self.cont_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.row3.append(self.cont_box)
        # Fill continue space holder if chaptered is set True
        self.chap_switched(self.chap_switch, self.chap_switch.get_state())
        
        # Row 4: Authcode ######################################################
        # Authcode: __________________                                         #
        self.row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.box.append(self.row4)
        # Label "Authcode: "
        self.auth_label = Gtk.Label(label="Authcode: ")
        self.row4.append(self.auth_label)
        # Textbox
        self.auth_textbox = Gtk.Entry()
        self.auth_textbox.set_placeholder_text("Enter your authentication code here.")
        self.auth_textbox.set_buffer(Gtk.EntryBuffer.new(self.authcode,len(self.authcode)))
        self.row4.append(self.auth_textbox)
        
        # Space ################################################################
        #                                                                      #
        self.space_holder3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.space_holder3.set_vexpand(True)
        self.box.append(self.space_holder3)
        
        # Row 5: Save & Run ####################################################
        # <=========================================================> Save Run #
        self.row5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.row5.set_spacing(5)
        self.box.append(self.row5)
        # Progress Bar
        self.progress_bar = Gtk.ProgressBar.new()
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_valign(Gtk.Align.CENTER)
        self.row5.append(self.progress_bar)
        # Save Button
        self.save_button = Gtk.Button(label="Save")
        self.save_button.connect('clicked', self.save)
        self.row5.append(self.save_button)
        # Run Button
        self.run_button = Gtk.Button(label="Run")
        self.run_button.connect('clicked', self.run)
        self.row5.append(self.run_button)
    
    # Update compression level area ############################################
    def format_chosen(self,dropdown, data):
        # Remove outdated compression level box
        self.row2.remove(self.clevel_box)
        # Generate new compression level box
        self.clevel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # Add label and spinbutton to compression level box for mp3, flac and opus
        if self.formats[dropdown.get_selected()] in ["mp3","flac","opus"]:
            # Label "Compression level: "
            self.clevel_label = Gtk.Label(label="Compression level: ")
            self.clevel_box.append(self.clevel_label)
            # Spinbutton
            if self.formats[dropdown.get_selected()] == "mp3":
                self.clevel_spinbutton = Gtk.SpinButton.new_with_range(0,9,1)
                if "mp3_compression_level" in self.settings:
                    self.clevel_spinbutton.set_value(self.settings["mp3_compression_level"])
            if self.formats[dropdown.get_selected()] == "flac":
                self.clevel_spinbutton = Gtk.SpinButton.new_with_range(0,12,1)
                if "flac_compression_level" in self.settings:
                    self.clevel_spinbutton.set_value(self.settings["flac_compression_level"])
            if self.formats[dropdown.get_selected()] == "opus":
                self.clevel_spinbutton = Gtk.SpinButton.new_with_range(0,10,1)
                if "opus_compression_level" in self.settings:
                    self.clevel_spinbutton.set_value(self.settings["opus_compression_level"])
            self.clevel_spinbutton.set_numeric(True)
            self.clevel_spinbutton.set_snap_to_ticks(True)
            self.clevel_box.append(self.clevel_spinbutton)
        # Insert new compression level box
        self.row2.append(self.clevel_box)
    
    # Update continue area #####################################################
    def chap_switched(self, switch, state):
        # Remove outdated continue box
        self.row3.remove(self.cont_box)
        # Generate new  continue box
        self.cont_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if state:
            # Label "Continue: "
            self.cont_label = Gtk.Label(label="Continue: ")
            self.cont_box.append(self.cont_label)
            # Switch
            self.cont_switch = Gtk.Switch()
            self.cont_switch.set_active(False)
            self.cont_switch.connect("state-set", self.cont_switched)
            self.cont_box.append(self.cont_switch)
            # Continue spin button space holder
            self.cont_spin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.cont_box.append(self.cont_spin_box)
            # Fill continue spin button space holder if continue is set True
            self.cont_switched(self.cont_switch, self.cont_switch.get_state())
        # Insert new continue box
        self.row3.append(self.cont_box)
    
    # Uptade continue spin button area #########################################
    def cont_switched(self, switch, state):
        # Remove outdated continue spin button box
        self.cont_box.remove(self.cont_spin_box)
        # Generate new continue spin button box
        self.cont_spin_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        if state:
            # Spin button
            self.cont_spinbutton = Gtk.SpinButton.new_with_range(0,10000,1)
            self.cont_spin_box.append(self.cont_spinbutton)
        # Insert new continue spin button box
        self.cont_box.append(self.cont_spin_box)
        
    def path_chosen(self, entry):
        path = entry.get_buffer().get_text()
        if path[-1] == "\n":
          path = path[:-1]
        if path[-1] == "\r":
          path = path[:-1]
        if path[:7] == "file://":
          path = path[7:]
        entry.set_buffer(Gtk.EntryBuffer.new(path,len(path)))
    
    # Load .authcode and .settings #############################################
    def load(self):
        # Load settings
        if os.path.exists(".settings"):
            with open(".settings", "r") as file:
                self.settings = json.load(file)
        else:
            self.settings = {}
        # Load .authcode
        if os.path.exists(".authcode"):
            with open(".authcode", "r") as file:
                self.authcode = file.read()[:-1]
        elif os.path.exists(os.path.expanduser("~/.authcode")):
            with open(os.path.expanduser("~/.authcode"), "r") as file:
                self.authcode = file.read()[:-1]
        else:
            self.authcode = ""
    
    # Save .settings ###########################################################
    def save(self,button):
        self.path_chosen(self.file_textbox)
        self.settings["path"] = self.file_textbox.get_buffer().get_text()
        self.settings["format"] = self.formats[self.format_dropdown.get_selected()]
        if self.formats[self.format_dropdown.get_selected()] == "mp3":
            self.settings["mp3_compression_level"] = self.clevel_spinbutton.get_value_as_int()
        elif self.formats[self.format_dropdown.get_selected()] == "flac":
            self.settings["flac_compression_level"] = self.clevel_spinbutton.get_value_as_int()
        elif self.formats[self.format_dropdown.get_selected()] == "opus":
            self.settings["opus_compression_level"] = self.clevel_spinbutton.get_value_as_int()
        self.settings["chaptered"] = self.chap_switch.get_active()
        with open(".settings", "w") as file:
            json.dump(self.settings, file, indent=4)
        self.load()
    
    def update_progress(self, fraction):
        self.progress_bar.set_fraction(fraction)
        
    def run_subprocess(self, call):
        self.process = subprocess.Popen(call,stdout=subprocess.PIPE, text=True)
        
        while self.process.poll() is None:
            output = self.process.stdout.readline()
            
            if output.startswith("Total length: "):
                length = output[14:22]
                length_s = int(length[:2])*3600+int(length[3:5])*60+int(length[6:8])
                
            if output.startswith("size="):
                for i in range(len(output)-5):
                    if output[i:i+5] == "time=":
                        progress = output[i+5:i+13]
                        progress_s = int(progress[:2])*3600+int(progress[3:5])*60+int(progress[6:8])
                        GLib.idle_add(self.update_progress,progress_s/length_s)
                        
            if output[:18]=="Chapter splitting:":
                GLib.idle_add(self.update_progress,int(output[42:45])/100)
    
    # Run AAXtoMP3 #############################################################
    def run(self,button):
        self.path_chosen(self.file_textbox)
        call = ["./AAXtoMP3"]
        call.append(self.format_calls[self.format_dropdown.get_selected()])
        if self.formats[self.format_dropdown.get_selected()] in ["mp3","flac","opus"]:
            call.append("--level")
            call.append(str(self.clevel_spinbutton.get_value_as_int()))
        if self.chap_switch.get_active():
            call.append("-c")
            if self.cont_switch.get_active():
                call.append("--continue")
                call.append(str(self.cont_spinbutton.get_value_as_int()))
        else:
            call.append("-s")
        call.append("-A")
        call.append(self.auth_textbox.get_buffer().get_text())
        call.append(self.file_textbox.get_buffer().get_text())
        
        thread = threading.Thread(target=self.run_subprocess, args=(call,))
        thread.start()
        
    def __del__(self):
        try:
          self.process.terminate()
        except Error:
          pass

class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()

app = MyApp(application_id="com.example.GtkApplication")
app.run(sys.argv)
