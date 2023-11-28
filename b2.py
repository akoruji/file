import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mysql.connector
import logging
import subprocess
import os
from datetime import datetime

# Configure the logging system
logging.basicConfig(filename='mysql_backup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a variable to track the connection status
connection_successful = False

def connect_to_mysql():
    global connection_successful
    host = host_entry.get()
    port = port_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password
        )
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]

        db_listbox.delete(0, tk.END)
        for db in databases:
            db_listbox.insert(tk.END, db)

        cursor.close()
        connection.close()
        connection_successful = True
        feedback_label.config(text="Connection to MySQL successful", fg="green")
        logging.info("Connection to MySQL successful")
    except mysql.connector.Error as err:
        error_message = f"Error: {err}"
        feedback_label.config(text=error_message, fg="red")
        logging.error(error_message)

def proceed_to_backup():
    selected_db = db_listbox.get(tk.ACTIVE)
    if selected_db:
        try:
            # Prompt the user to choose a location for the backup
            backup_dir = filedialog.askdirectory(title="Select Backup Location")
            if not backup_dir:
                return  # User canceled directory selection

            backup_dir = os.path.join(backup_dir, "NMRS_Backup")

            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            mysqldump_path = os.path.join(current_dir, "mysqldump.exe")

            connection = mysql.connector.connect(
                host=host_entry.get(),
                port=port_entry.get(),
                user=username_entry.get(),
                password=password_entry.get(),
                database=selected_db
            )

            feedback_message = f"Selected database: {selected_db}\n\nDo you wish to proceed?"
            confirmation = messagebox.askyesno("Confirm Backup", feedback_message)
            logging.info("User confirmed the backup")

            if confirmation:
                current_datetime = datetime.now()
                timestamp = current_datetime.strftime('%Y-%m-%d-%H-%M-%S')
                backup_file_name = f"{selected_db}_{timestamp}.sql"
                backup_file_path = os.path.join(backup_dir, backup_file_name)
                backup_zip_name = f"{selected_db}_{timestamp}.zip"
                backup_zip_path = os.path.join(backup_dir, backup_zip_name)

                feedback_label.config(text="Backup in progress...", fg="blue")
                window.update()

                cmd = [mysqldump_path, "-u", username_entry.get(), "--password=" + password_entry.get(), selected_db]
                with open(backup_file_path, "w") as backup_file:
                    subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, check=True)

                with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_file_path, os.path.basename(backup_file_path))

                os.remove(backup_file_path)

                feedback_label.config(text=f"Backup of {selected_db} completed successfully", fg="green")
                logging.info(f"Backup of {selected_db} completed successfully")
            else:
                feedback_label.config(text="Backup process canceled.", fg="red")

        except subprocess.CalledProcessError as e:
            error_message = f"Error creating backup: {e}"
            feedback_label.config(text=error_message, fg="red")
            logging.error(error_message)
        except mysql.connector.Error as err:
            error_message = f"Error: {err}"
            feedback_label.config(text=error_message, fg="red")
            logging.error(error_message)

def proceed_to_import():
    selected_db = db_listbox.get(tk.ACTIVE)
    if selected_db:
        try:
            # Prompt the user to choose an SQL file for import
            sql_file_path = filedialog.askopenfilename(title="Select SQL File", filetypes=[("SQL Files", "*.sql")])
            if not sql_file_path:
                return  # User canceled file selection

            connection = mysql.connector.connect(
                host=host_entry.get(),
                port=port_entry.get(),
                user=username_entry.get(),
                password=password_entry.get(),
                database=selected_db
            )

            feedback_message = f"Selected database: {selected_db}\n\nDo you wish to proceed with import?"
            confirmation = messagebox.askyesno("Confirm Import", feedback_message)
            logging.info("User confirmed the import")

            if confirmation:
                feedback_label.config(text="Import in progress...", fg="blue")
                window.update()

                cmd = ["mysql", "-u", username_entry.get(), "--password=" + password_entry.get(), selected_db]
                with open(sql_file_path, "r") as sql_file:
                    subprocess.run(cmd, stdin=sql_file, stderr=subprocess.PIPE, check=True)

                feedback_label.config(text=f"Import to {selected_db} completed successfully", fg="green")
                logging.info(f"Import to {selected_db} completed successfully")
            else:
                feedback_label.config(text="Import process canceled.", fg="red")

        except subprocess.CalledProcessError as e:
            error_message = f"Error during import: {e}"
            feedback_label.config(text=error_message, fg="red")
            logging.error(error_message)
        except mysql.connector.Error as err:
            error_message = f"Error: {err}"
            feedback_label.config(text=error_message, fg="red")
            logging.error(error_message)

# Create the main application window
window = tk.Tk()
window.title("MySQL Database Backup and Import Tool")

frame = tk.Frame(window)
frame.pack()

frame_left = tk.Frame(frame)
frame_right = tk.Frame(frame)
frame_left.pack(side="left")
frame_right.pack(side="left")

tk.Label(frame_left, text="MySQL Host:").pack()
host_entry = tk.Entry(frame_right)
host_entry.pack()

tk.Label(frame_left, text="Database Port:").pack()
port_entry = tk.Entry(frame_right)
port_entry.pack()

tk.Label(frame_left, text="MySQL Username:").pack()
username_entry = tk.Entry(frame_right)
username_entry.pack()

tk.Label(frame_left, text="MySQL Password:").pack()
password_entry = tk.Entry(frame_right, show="*")
password_entry.pack()

connect_button = tk.Button(window, text="Connect to MySQL", command=connect_to_mysql)
connect_button.pack()

feedback_label = tk.Label(window, text="", fg="black")
feedback_label.pack()

db_frame = tk.Frame(window)
db_frame.pack()

db_label = tk.Label(db_frame, text="Available Databases:")
db_label.pack()

# Initially hide the list of available databases
db_frame.pack_forget()

# Create a scrolled listbox for available databases
db_listbox_frame = tk.Frame(db_frame)
db_listbox_frame.pack()
db_listbox = tk.Listbox(db_listbox_frame, selectmode=tk.SINGLE)
db_listbox.pack(side="left")

# Create a vertical scrollbar for the listbox
scrollbar = tk.Scrollbar(db_listbox_frame, command=db_listbox.yview)
scrollbar.pack(side="left", fill="y")
db_listbox.config(yscrollcommand=scrollbar.set)

# Create a frame for buttons
button_frame = tk.Frame(window)
button_frame.pack()

# Create the "Proceed to Backup" button
backup_button = tk.Button(button_frame, text="Proceed to Backup", command=proceed_to_backup)
backup_button.pack(side="left", padx=10)  # Add some padding to the left

# Create the "Proceed to Import" button
import_button = tk.Button(button_frame, text="Proceed to Import", command=proceed_to_import)
import_button.pack(side="left", padx=10)  # Add some padding to the left

# Create the "Quit" button
quit_button = tk.Button(button_frame, text="Quit", command=window.quit)
quit_button.pack(side="left")  # Position it to the left

# Function to show or hide the list of available databases
def toggle_db_frame():
    if connection_successful:
        db_frame.pack()
    else:
        db_frame.pack_forget()

# Bind the function to the connect button
connect_button.config(command=lambda: (connect_to_mysql(), toggle_db_frame()))

window.mainloop()
