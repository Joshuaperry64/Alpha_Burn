import os
import sys
import time
import subprocess
import pycdlib
from PyQt6.QtCore import QThread, pyqtSignal

class BurnWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, drive, file_list, iso_path):
        super().__init__()
        self.drive = drive
        self.file_list = file_list
        self.iso_path = iso_path

    def run(self):
        try:
            # Stage 1: Create ISO
            self.progress.emit("Creating ISO 9660 disc image...")
            iso = pycdlib.PyCdlib()
            iso.new(joliet=True)
            
            for filepath in self.file_list:
                basename = os.path.basename(filepath)
                iso_path_on_disc = f'/{basename.upper()}'
                iso.add_file(filepath, joliet_path=iso_path_on_disc)
            
            iso.write(self.iso_path)
            iso.close()

            # Stage 2: Burn ISO to disc
            self.progress.emit(f"Burning {os.path.basename(self.iso_path)} to drive {self.drive}...")
            
            if sys.platform == "win32":
                # Assumes 'cdburn.exe' is in the system PATH or project root
                command = ['cdburn', self.drive, self.iso_path]
            elif sys.platform == "linux":
                command = ['wodim', '-v', f'dev={self.drive}', self.iso_path]
            else:
                raise NotImplementedError("Burning is not supported on this OS.")

            # --- REAL BURN LOGIC ---
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            
            # Real-time progress reporting from the command line tool
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress.emit(output.strip())
            
            return_code = process.poll()
            if return_code != 0:
                stderr_output = process.stderr.read()
                raise subprocess.CalledProcessError(return_code, command, stderr=stderr_output)
            
            self.finished.emit("Burn completed successfully.")

        except FileNotFoundError:
            self.error.emit("Burn command not found. Ensure a command-line burning utility (e.g., cdburn.exe) is in your system's PATH.")
        except subprocess.CalledProcessError as e:
            self.error.emit(f"Burner failed with error: {e.stderr}")
        except Exception as e:
            self.error.emit(f"An error occurred during burning: {e}")
        finally:
            if os.path.exists(self.iso_path):
                try:
                    os.remove(self.iso_path)
                except OSError as e:
                    self.progress.emit(f"Could not remove temporary ISO file: {e}")
