import os
import importlib
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
from datetime import datetime
import zipfile

# Create a main window
root = tk.Tk()
root.title("Reconciliation App")
root.geometry("700x600")
root.configure(bg="#e7f1ff")

RECONCILIATION_MODULES = {
   
    'dummy': 'logic.dummy'
   
}

# Ensure the 'downloads' folder exists on the device
RESULT_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')

# Global variables to store selected file paths
file1_paths = []
file2_path = []

def clear_file1_fields():
    """Clear all file 1 selection labels."""
    file1_label1.config(text="No file selected for Source Data File 1.")
    file1_label2.config(text="")
    file1_label3.config(text="")

def update_file1_labels():
    """Update the file 1 labels based on the number of files selected."""
    clear_file1_fields()
    if len(file1_paths) > 0:
        file1_label1.config(text=os.path.basename(file1_paths[0]))
    if len(file1_paths) > 1:
        file1_label2.config(text=os.path.basename(file1_paths[1]))
    if len(file1_paths) > 2:
        file1_label3.config(text=os.path.basename(file1_paths[2]))

def clear_file2_fields():
    """Clear all file 2 selection labels."""
    file2_label1.config(text="No file selected for Source Data File 2.")
    file2_label2.config(text="")
    file2_label3.config(text="")     

def update_file2_labels():
    """Update the file 2 labels based on the number of files selected."""
    clear_file2_fields()
    if len(file2_path) > 0:
        file2_label1.config(text=os.path.basename(file2_path[0]))
    if len(file2_path) > 1:
        file2_label2.config(text=os.path.basename(file2_path[1]))
    if len(file2_path) > 2:
        file2_label3.config(text=os.path.basename(file2_path[2]))

def upload_file1():
    global file1_paths
    selected_module = module_combobox.get()

    if selected_module == 'other_dummy_2':
        if len(file1_paths) < 3:
            file = filedialog.askopenfilename(
                title="Select Source Data File 1 (other_dummy)",
                filetypes=[("CSV or Excel files", "*.csv *.xlsx")])
            if file:
                file1_paths.append(file)
                update_file1_labels()
                update_clear_button()
            else:
                messagebox.showerror("Error", "Please select a valid file.")
        else:
            messagebox.showwarning("Limit Reached", "You can upload a maximum of 3 files for Source Data File 1.")
    
    elif selected_module == 'other_dummy_2':
        zip_file = filedialog.askopenfilename(
            title="Select ZIP File for other_dummy",
            filetypes=[("ZIP files", "*.zip")])
        
        if zip_file:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    extracted_files = zip_ref.namelist()
                    valid_files = [f for f in extracted_files if f.endswith(('.csv', '.xlsx'))]

                    if len(valid_files) > 30:
                        messagebox.showerror("Error", "The ZIP contains more than 30 files. Please limit to 30.")
                    else:
                        zip_ref.extractall("extracted_other_dummy_files")
                        file1_paths = [os.path.join("extracted_other_dummy_files", f) for f in valid_files]
                        update_file1_labels()
                        update_clear_button()
            except zipfile.BadZipFile:
                messagebox.showerror("Error", "Invalid ZIP file. Please upload a valid ZIP file.")
        else:
            messagebox.showerror("Error", "Please select a ZIP file for Source Data File 1.")
    
    else:
        file = filedialog.askopenfilename(
            title="Select Source Data File 1",
            filetypes=[("CSV or Excel files", "*.csv *.xlsx")])
        if file:
            file1_paths = [file]  # Store the file in a list for consistency
            file1_label1.config(text=os.path.basename(file))
            update_clear_button()  # Update button status
        else:
            messagebox.showerror("Error", "Please select a file for Source Data File 1.")

def clear_file1_selection():
    global file1_paths
    file1_paths = []
    clear_file1_fields()
    update_clear_button()

def upload_file2():
    global file2_path
    selected_module = module_combobox.get()

    if selected_module == 'other_dummy':
        if len(file2_path) < 3:
            file = filedialog.askopenfilename(
                title="Select Source Data File 2 (other_dummy2)",
                filetypes=[("CSV or Excel files", "*.csv *.xlsx")])
            if file:
                file2_path.append(file)
                update_file2_labels()
                update_clear_button()  # Update button status for file2
            else:
                messagebox.showerror("Error", "Please select a valid file.")
        else:
            messagebox.showwarning("Limit Reached", "You can upload a maximum of 3 files for Source Data File 2.")
    else:
        file = filedialog.askopenfilename(
            title="Select Source Data File 2",
            filetypes=[("CSV or Excel files", "*.csv *.xlsx")])
        if file:
            file2_path = [file]  # Store the file in a list for consistency
            file2_label1.config(text=os.path.basename(file))
            update_clear_button()  # Update button status for file2
        else:
            messagebox.showerror("Error", "Please select a file for Source Data File 2.")

def clear_file2_selection():
    """Allow user to clear the list of selected files for Source Data File 2."""
    global file2_path
    file2_path = []
    clear_file2_fields()
    update_clear_button()  # Update the clear button for file1 as well

def generate_unique_filename(filename):
    """Generate a unique filename by appending a timestamp if the file already exists."""
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{base}_{timestamp}{ext}"
    return unique_filename

def reconcile_files():
    selected_module = module_combobox.get()

    if not selected_module:
        messagebox.showerror("Error", "Please select a reconciliation module.")
        return

    if not file1_paths or not file2_path:
        messagebox.showerror("Error", "Please upload both Source Data File 1 and Source Data File 2.")
        return

    try:
        module_name = RECONCILIATION_MODULES.get(selected_module)
        if not module_name:
            raise ValueError("Invalid reconciliation module selected.")

        reconciliation_module = importlib.import_module(module_name)

        if selected_module == 'other_dummy':
            if len(file1_paths) < 1 or len(file1_paths) > 3:
                messagebox.showerror("Error", "Please upload between 1 and 3 files for Source Data File 1 (other_dummy).")
                return
            sheet_dict = reconciliation_module.reconcile_data(file1_paths, file2_path)
        else:
            sheet_dict = reconciliation_module.reconcile_data(file1_paths, file2_path)

        result_filename = f'reconciliation_result_{selected_module}.xlsx'
        result_path = os.path.join(RESULT_FOLDER, result_filename)

        if os.path.exists(result_path):
            result_filename = generate_unique_filename(result_filename)
            result_path = os.path.join(RESULT_FOLDER, result_filename)

        with pd.ExcelWriter(result_path, engine='xlsxwriter') as writer:
            for sheet_name, df in sheet_dict.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        messagebox.showinfo("Success", f"Reconciliation completed.\nFile saved to {result_path}")

    except PermissionError:
        messagebox.showerror("Permission Error", "Permission denied. Please ensure you have write access to the Downloads folder.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def update_clear_button():
    """Update the clear button's state based on the presence of selected files."""
    if file1_paths:
        clear_files_button.config(state='normal')  # Enable the button for file1
    else:
        clear_files_button.config(state='disabled')  # Disable the button for file1

    if file2_path:  # Check for file2 selections
        clear_file2_button.config(state='normal')  # Enable the button for file2
    else:
        clear_file2_button.config(state='disabled')  # Disable the button for file2

def on_module_change(event):
    """Update the UI based on the selected reconciliation module."""
    selected_module = module_combobox.get()
    clear_file1_fields()  # Reset file names when module changes

    file1_label2.pack_forget()
    file1_label3.pack_forget()

    if selected_module == 'other_dummy':
        file1_button.config(text="Upload Source Data File 1 (other_dummy) - Max 3 Files")
        file1_label1.pack(pady=5, after=file1_button)
        file1_label2.pack(pady=5, after=file1_label1)
        file1_label3.pack(pady=5, after=file1_label2)

    elif selected_module == 'other_dummy':
        file1_button.config(text="Upload Source Data File 1 (other_dummy) - Zip Files")
        file1_label1.pack(pady=5, after=file1_button)

    elif selected_module == 'other_dummy':
        file1_button.config(text="Upload Source Data File 1 (Qris other_dummy2) - Max 3 Files")
        file1_label1.pack(pady=5, after=file1_button)
        file1_label2.pack(pady=5, after=file1_label1)
        file1_label3.pack(pady=5, after=file1_label2)

        file2_button.config(text= "Upload Source Data File 2 (Qris other_dummy2) - Max 3 Files")
        file2_label1.pack(pady=5, after=file2_button)
        file2_label2.pack(pady=5, after=file2_label1)
        file2_label3.pack(pady=5, after=file2_label2)

    else:
        file1_button.config(text="Upload Source Data File 1")
        file1_label1.pack(pady=5, after=file1_button)

    update_clear_button()  # Update the clear button status

# Create a label and dropdown for selecting the reconciliation module
module_label = tk.Label(root, text="Select Reconciliation Module:")
module_label.pack(pady=10)

module_combobox = ttk.Combobox(root, values=list(RECONCILIATION_MODULES.keys()), state='readonly')
module_combobox.pack(pady=10)
module_combobox.bind("<<ComboboxSelected>>", on_module_change)

# Create buttons to upload Source Data File 1 and File 2
file1_button = tk.Button(root, text="Upload Source Data File 1", command=upload_file1)
file1_button.pack(pady=10)

# Initialize clear files button for file1
clear_files_button = tk.Button(root, text="Clear Source Data File 1 Selections", command=clear_file1_selection, state='disabled')
clear_files_button.pack(pady=10)

# Create labels to display the selected files for Source Data File 1
file1_label1 = tk.Label(root, text="No file selected for Source Data File 1.")
file1_label1.pack(pady=5)

file1_label2 = tk.Label(root, text="")
file1_label3 = tk.Label(root, text="")

file2_button = tk.Button(root, text="Upload Source Data File 2", command=upload_file2)
file2_button.pack(pady=10)

# Initialize clear files button for file2
clear_file2_button = tk.Button(root, text="Clear Source Data File 2 Selections", command=clear_file2_selection, state='disabled')
clear_file2_button.pack(pady=10)

# Create labels to display the selected files for Source Data File 2
file2_label1 = tk.Label(root, text="No file selected for Source Data File 2.")
file2_label1.pack(pady=5)

file2_label2 = tk.Label(root, text="")
file2_label3 = tk.Label(root, text="")

# Create a button to trigger reconciliation
reconcile_button = tk.Button(root, text="Reconcile Files", command=reconcile_files)
reconcile_button.pack(pady=20)

# Start the Tkinter main loop
root.mainloop()
