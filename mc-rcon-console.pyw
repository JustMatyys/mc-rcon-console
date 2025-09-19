import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from mcrcon import MCRcon
import threading
import json
import os
import customtkinter as ctk

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MinecraftRCONGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft RCON Console")
        self.root.geometry("900x780")
        
        # Connection variables
        self.mcr = None
        self.connected = False
        self.profiles_file = "rcon_profiles.json"
        self.profiles = self.load_profiles()
        
        # Command history
        self.command_history = []
        self.history_index = -1
        
        self.setup_ui()
        self.update_profile_dropdown()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Connection frame
        conn_frame = ctk.CTkFrame(main_frame)
        conn_frame.pack(fill="x", padx=10, pady=10)
        
        # Profile management
        profile_frame = ctk.CTkFrame(conn_frame)
        profile_frame.pack(fill="x", padx=10, pady=10)
        
        profile_label = ctk.CTkLabel(profile_frame, text="Profile:", font=ctk.CTkFont(size=14, weight="bold"))
        profile_label.pack(side="left", padx=(10, 5))
        
        self.profile_var = tk.StringVar()
        self.profile_dropdown = ctk.CTkComboBox(profile_frame, variable=self.profile_var, width=200, 
                                               command=self.load_selected_profile, state="readonly")
        self.profile_dropdown.pack(side="left", padx=5)
        
        self.load_profile_btn = ctk.CTkButton(profile_frame, text="Load", command=self.load_selected_profile, width=80)
        self.load_profile_btn.pack(side="left", padx=5)
        
        self.save_profile_btn = ctk.CTkButton(profile_frame, text="Save", command=self.save_current_profile, width=80)
        self.save_profile_btn.pack(side="left", padx=5)
        
        self.delete_profile_btn = ctk.CTkButton(profile_frame, text="Delete", command=self.delete_selected_profile, 
                                               width=80, fg_color="red", hover_color="darkred")
        self.delete_profile_btn.pack(side="left", padx=5)
        
        # Connection fields
        conn_fields_frame = ctk.CTkFrame(conn_frame)
        conn_fields_frame.pack(fill="x", padx=10, pady=10)
        
        # Host
        host_frame = ctk.CTkFrame(conn_fields_frame, fg_color="transparent")
        host_frame.pack(side="left", padx=5)
        host_label = ctk.CTkLabel(host_frame, text="Host:", font=ctk.CTkFont(size=12, weight="bold"))
        host_label.pack()
        self.host_entry = ctk.CTkEntry(host_frame, width=150, placeholder_text="server.example.com")
        self.host_entry.pack(pady=(5, 0))
        
        # Port
        port_frame = ctk.CTkFrame(conn_fields_frame, fg_color="transparent")
        port_frame.pack(side="left", padx=5)
        port_label = ctk.CTkLabel(port_frame, text="Port:", font=ctk.CTkFont(size=12, weight="bold"))
        port_label.pack()
        self.port_entry = ctk.CTkEntry(port_frame, width=100, placeholder_text="25575")
        self.port_entry.pack(pady=(5, 0))
        
        # Password
        password_frame = ctk.CTkFrame(conn_fields_frame, fg_color="transparent")
        password_frame.pack(side="left", padx=5)
        password_label = ctk.CTkLabel(password_frame, text="Password:", font=ctk.CTkFont(size=12, weight="bold"))
        password_label.pack()
        self.password_entry = ctk.CTkEntry(password_frame, width=150, placeholder_text="password", show="*")
        self.password_entry.pack(pady=(5, 0))
        
        # Connect button
        self.connect_btn = ctk.CTkButton(conn_fields_frame, text="Connect", command=self.toggle_connection, 
                                        width=120, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.connect_btn.pack(side="left", padx=20, pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(conn_frame, text="● Disconnected", text_color="red", 
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=5)
        
        # Console frame
        console_frame = ctk.CTkFrame(main_frame)
        console_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Console output label
        console_label = ctk.CTkLabel(console_frame, text="Console Output:", font=ctk.CTkFont(size=14, weight="bold"))
        console_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Console output (using tkinter ScrolledText as CTk doesn't have equivalent)
        console_container = ctk.CTkFrame(console_frame)
        console_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.console_output = scrolledtext.ScrolledText(
            console_container, 
            height=20, 
            state="disabled",
            bg="#1a1a1a",
            fg="white",
            font=("Consolas", 11),
            insertbackground="white",
            selectbackground="#333333",
            wrap=tk.WORD
        )
        self.console_output.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Setup Minecraft color support
        self.setup_minecraft_colors()
        
        # Command input frame
        cmd_frame = ctk.CTkFrame(console_frame)
        cmd_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        cmd_label = ctk.CTkLabel(cmd_frame, text="Command:", font=ctk.CTkFont(size=12, weight="bold"))
        cmd_label.pack(side="left", padx=(10, 5))
        
        self.command_entry = ctk.CTkEntry(cmd_frame, font=ctk.CTkFont(family="Consolas", size=12), 
                                         placeholder_text="Enter Minecraft command...")
        self.command_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.command_entry.bind("<Return>", self.send_command)
        self.command_entry.bind("<Up>", self.previous_command)
        self.command_entry.bind("<Down>", self.next_command)
        
        self.send_btn = ctk.CTkButton(cmd_frame, text="Send", command=self.send_command, width=80)
        self.send_btn.pack(side="right", padx=5)
        
        self.clear_btn = ctk.CTkButton(cmd_frame, text="Clear", command=self.clear_console, width=80,
                                      fg_color="orange", hover_color="darkorange")
        self.clear_btn.pack(side="right", padx=5)
        
        # Initially disable command controls
        self.command_entry.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        
    def previous_command(self, event):
        """Navigate to previous command in history (Up arrow)"""
        if not self.command_history:
            return "break"
        
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        if 0 <= self.history_index < len(self.command_history):
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        
        return "break"
    
    def next_command(self, event):
        """Navigate to next command in history (Down arrow)"""
        if not self.command_history or self.history_index == -1:
            return "break"
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            # Clear entry when going past the last command
            self.history_index = -1
            self.command_entry.delete(0, tk.END)
        
        return "break"
    
    def add_to_history(self, command):
        """Add command to history, avoiding duplicates"""
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
            # Limit history to 50 commands
            if len(self.command_history) > 50:
                self.command_history.pop(0)
        self.history_index = -1
    
    def load_profiles(self):
        """Load saved profiles from JSON file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def save_profiles(self):
        """Save profiles to JSON file"""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save profiles: {str(e)}")
    
    def update_profile_dropdown(self):
        """Update the profile dropdown with available profiles"""
        profile_names = list(self.profiles.keys())
        self.profile_dropdown.configure(values=profile_names)
        if profile_names and not self.profile_var.get():
            self.profile_var.set(profile_names[0])
    
    def load_selected_profile(self, choice=None):
        """Load the selected profile into the connection fields"""
        profile_name = self.profile_var.get()
        if profile_name and profile_name in self.profiles:
            profile = self.profiles[profile_name]
            self.host_entry.delete(0, tk.END)
            self.host_entry.insert(0, profile.get('host', ''))
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, profile.get('port', ''))
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, profile.get('password', ''))
    
    def save_current_profile(self):
        """Save current connection settings as a new profile"""
        profile_name = simpledialog.askstring("Save Profile", "Enter profile name:")
        if profile_name:
            if profile_name in self.profiles:
                if not messagebox.askyesno("Overwrite Profile", f"Profile '{profile_name}' already exists. Overwrite?"):
                    return
            
            self.profiles[profile_name] = {
                'host': self.host_entry.get().strip(),
                'port': self.port_entry.get().strip(),
                'password': self.password_entry.get()
            }
            
            self.save_profiles()
            self.update_profile_dropdown()
            self.profile_var.set(profile_name)
            self.log_to_console(f"Profile '{profile_name}' saved successfully.")
    
    def delete_selected_profile(self):
        """Delete the selected profile"""
        profile_name = self.profile_var.get()
        if profile_name and profile_name in self.profiles:
            if messagebox.askyesno("Delete Profile", f"Are you sure you want to delete profile '{profile_name}'?"):
                del self.profiles[profile_name]
                self.save_profiles()
                self.update_profile_dropdown()
                self.profile_var.set('')
                # Clear connection fields
                self.host_entry.delete(0, tk.END)
                self.port_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
                self.log_to_console(f"Profile '{profile_name}' deleted successfully.")
    
    def setup_minecraft_colors(self):
        """Setup Minecraft color mappings"""
        self.mc_colors = {
            '§0': '#000000',  # Black
            '§1': '#0000AA',  # Dark Blue
            '§2': '#00AA00',  # Dark Green
            '§3': '#00AAAA',  # Dark Aqua
            '§4': '#AA0000',  # Dark Red
            '§5': '#AA00AA',  # Dark Purple
            '§6': '#FFAA00',  # Gold
            '§7': '#AAAAAA',  # Gray
            '§8': '#555555',  # Dark Gray
            '§9': '#5555FF',  # Blue
            '§a': '#55FF55',  # Green
            '§b': '#55FFFF',  # Aqua
            '§c': '#FF5555',  # Red
            '§d': '#FF55FF',  # Light Purple
            '§e': '#FFFF55',  # Yellow
            '§f': '#FFFFFF',  # White
            '§r': '#FFFFFF',  # Reset
        }
        
        # Configure text tags for colors
        for code, color in self.mc_colors.items():
            self.console_output.tag_configure(f"color_{code}", foreground=color)
    
    def strip_colors(self, text):
        """Remove Minecraft color codes from text"""
        return re.sub(r"§.", "", text)
    
    def parse_minecraft_colors(self, text):
        """Parse Minecraft color codes and return formatted segments"""
        segments = []
        current_pos = 0
        current_color = "white"  # Default color
        
        # Find all color codes
        color_matches = list(re.finditer(r"§[0-9a-z]", text))
        
        for match in color_matches:
            # Add text before color code with current color
            if match.start() > current_pos:
                text_segment = text[current_pos:match.start()]
                if text_segment:
                    segments.append((text_segment, current_color))
            
            # Update current color
            color_code = match.group()
            current_color = f"color_{color_code}"
            current_pos = match.end()
        
        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text:
                segments.append((remaining_text, current_color))
        
        # If no color codes found, return entire text as white
        if not segments:
            segments.append((text, "white"))
        
        return segments
    
    def log_to_console(self, message, color="white", parse_colors=False):
        """Add a message to the console output"""
        self.console_output.config(state="normal")
        
        if parse_colors and "§" in message:
            # Parse and display colored text
            segments = self.parse_minecraft_colors(message)
            for text_segment, tag_color in segments:
                self.console_output.insert(tk.END, text_segment, tag_color)
        else:
            # Simple text with single color
            if color == "white":
                self.console_output.insert(tk.END, message)
            else:
                self.console_output.insert(tk.END, message, color)
        
        self.console_output.insert(tk.END, "\n")
        self.console_output.see(tk.END)
        self.console_output.config(state="disabled")
    
    def toggle_connection(self):
        """Connect or disconnect from the RCON server"""
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    
    def connect_to_server(self):
        """Connect to the Minecraft RCON server"""
        try:
            host = self.host_entry.get().strip()
            port_str = self.port_entry.get().strip()
            password = self.password_entry.get()
            
            if not host or not port_str or not password:
                messagebox.showerror("Error", "Host, port, and password are all required!")
                return
            
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror("Error", "Port must be a valid number!")
                return
            
            self.log_to_console(f"Connecting to {host}:{port}...")
            
            self.mcr = MCRcon(host=host, port=port, password=password)
            self.mcr.connect()
            
            self.connected = True
            self.status_label.configure(text="● Connected", text_color="green")
            self.connect_btn.configure(text="Disconnect")
            self.command_entry.configure(state="normal")
            self.send_btn.configure(state="normal")
            self.command_entry.focus()
            
            # Disable connection fields while connected
            self.host_entry.configure(state="disabled")
            self.port_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
            self.profile_dropdown.configure(state="disabled")
            self.load_profile_btn.configure(state="disabled")
            self.save_profile_btn.configure(state="disabled")
            self.delete_profile_btn.configure(state="disabled")
            
            self.log_to_console("Successfully connected to RCON server!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.log_to_console(f"Connection failed: {str(e)}")
    
    def disconnect_from_server(self):
        """Disconnect from the RCON server"""
        try:
            if self.mcr:
                self.mcr.disconnect()
            
            self.connected = False
            self.status_label.configure(text="● Disconnected", text_color="red")
            self.connect_btn.configure(text="Connect")
            self.command_entry.configure(state="disabled")
            self.send_btn.configure(state="disabled")
            
            # Re-enable connection fields and profile controls
            self.host_entry.configure(state="normal")
            self.port_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
            self.profile_dropdown.configure(state="readonly")
            self.load_profile_btn.configure(state="normal")
            self.save_profile_btn.configure(state="normal")
            self.delete_profile_btn.configure(state="normal")
            
            self.log_to_console("Disconnected from RCON server.")
            
        except Exception as e:
            self.log_to_console(f"Error during disconnect: {str(e)}")
    
    def send_command(self, event=None):
        """Send a command to the RCON server"""
        if not self.connected or not self.mcr:
            messagebox.showwarning("Warning", "Not connected to server!")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Add to command history
        self.add_to_history(command)
        
        try:
            # Log the command being sent
            self.log_to_console(f">> {command}")
            
            # Send command in a separate thread to prevent GUI freezing
            def execute_command():
                try:
                    output = self.mcr.command(command)
                    
                    # Update GUI from main thread with colored output
                    self.root.after(0, lambda: self.log_to_console(output, parse_colors=True))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log_to_console(f"Command error: {str(e)}", "red"))
            
            threading.Thread(target=execute_command, daemon=True).start()
            
            # Clear command entry
            self.command_entry.delete(0, tk.END)
            
        except Exception as e:
            self.log_to_console(f"Error sending command: {str(e)}")
    
    def clear_console(self):
        """Clear the console output"""
        self.console_output.config(state="normal")
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state="disabled")
    
    def on_closing(self):
        """Handle application closing"""
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()

def main():
    root = ctk.CTk()
    app = MinecraftRCONGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()