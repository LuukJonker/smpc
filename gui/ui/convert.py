import os
import glob

def convert_ui_files_to_python_files(directory):
    ui_files = glob.glob(f"{directory}/*.ui")
    for ui_file in ui_files:
        os.system(f"pyuic5 {ui_file} -o {ui_file.replace('.ui', '.py')}")
    print(f"Converted {len(ui_files)} UI files to Python files.")

convert_ui_files_to_python_files(os.path.dirname(__file__))