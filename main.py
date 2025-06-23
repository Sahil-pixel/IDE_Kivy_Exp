from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from jnius import autoclass
import os
import shutil
# Embedded Python script to run
SCRIPT_CODE = """
import sys
import os

# Patch __spec__ to fix multiprocessing on Android
if getattr(sys.modules['__main__'], '__spec__', None) is None:
    sys.modules['__main__'].__spec__ = type('Spec', (), {'name': '__main__'})()

print("Hello from embedded script!", flush=True)
print("Python version:", sys.version, flush=True)
print("Script path:", __file__, flush=True)

from multiprocessing import Process
import time

def worker():
    print("In subprocess: PID =", os.getpid(), flush=True)
    for i in range(3):
        print(f"Subprocess count: {i}", flush=True)
        time.sleep(0.5)

if __name__ == '__main__':
    print("In main process: PID =", os.getpid(), flush=True)
    p = Process(target=worker)
    p.start()
    p.join()
    print("Subprocess finished", flush=True)
"""


SCRIPT_CODE2 = """
import os
import sys
import time
import traceback
from multiprocessing import Process, set_start_method
print("Hello from embedded script!", flush=True)
print("Python version:", sys.version, flush=True)
print("Script path:", __file__, flush=True)
def worker():
    try:
        print(f"[✓] In subprocess: PID={os.getpid()}", flush=True)
        for i in range(3):
            print(f"Subprocess count: {i}", flush=True)
            time.sleep(0.5)
    except Exception:
        print("❌ Subprocess failed:")
        traceback.print_exc()

if __name__ == '__main__':
    try:
        try:
            set_start_method('spawn', force=True)
        except RuntimeError as e:
            print(f"⚠️ set_start_method: {e}", flush=True)

        print(f"[✓] In main process: PID={os.getpid()}", flush=True)
        p = Process(target=worker)
        p.start()
        p.join()
        print("[✓] Subprocess finished", flush=True)

    except Exception:
        print("❌ Exception in __main__ block:", flush=True)
        traceback.print_exc()



"""

SCRIPT_CODE1="""
import sys
import os
import traceback
print("Hello from embedded script!", flush=True)
print("Python version:", sys.version, flush=True)
print("Script path:", __file__, flush=True)

from multiprocessing import Process,set_start_method
import time
import os

def worker():
    print("In subprocess: PID =", os.getpid(), flush=True)
    for i in range(3):
        print(f"Subprocess count: {i}", flush=True)
        time.sleep(0.5)

if __name__ == '__main__':
    print("In main process: PID =", os.getpid(), flush=True)
    try:
        set_start_method('spawn', force=True)
        p = Process(target=worker)
        p.start()
        p.join()
    except Exception:
        print("❌ Exception in __main__ block:", flush=True)
        traceback.print_exc()

    print("Subprocess finished", flush=True)



"""

"""
print("Hello from embedded script!")
import sys
print("Python version:", sys.version)
print("2 + 2 =", 2 + 2)
print("Python IDE runs python scripts")
for i in range(5):
    print("Python IDE Using Kivy")
"""

import zipfile

def extract_stdlib_if_needed(stdlib_zip_path, target_dir):
    if not os.path.exists(os.path.join(target_dir, 'encodings', '__init__.pyc')):
        try:
            with zipfile.ZipFile(stdlib_zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
                print(f"Extracted stdlib.zip to {target_dir}")
        except Exception as e:
            print(f"Failed to extract stdlib.zip: {e}")



class PythonRunner(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.output = TextInput(readonly=True, size_hint_y=1.0, font_size=40)
        self.add_widget(self.output)
        Clock.schedule_once(self.run_script, 1)

    def run_script(self, *args):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            files_dir = context.getFilesDir().getAbsolutePath()
            lib_dir = context.getApplicationInfo().nativeLibraryDir

            stdlib_zip_path = os.path.join(files_dir, 'app/_python_bundle/stdlib.zip')
            stdlib_extract_path = os.path.join(files_dir, 'app/lib/python3.11')
            extract_stdlib_if_needed(stdlib_zip_path, stdlib_extract_path)


            # Paths
            script_path = os.path.join(files_dir, 'script.py')
            mini_python_src = os.path.join(lib_dir, 'libmini_python.so')
            print("====##====",mini_python_src)
            #os.chmod(mini_python_src, 0o755)
            

            mini_python_exec = os.path.join(files_dir, 'mini_python')


            # Save script
            with open(script_path, 'w') as f:
                f.write(SCRIPT_CODE)

            # Copy binary if needed
            if not os.path.exists(mini_python_exec):
                shutil.copyfile(mini_python_src, mini_python_exec)
                os.chmod(mini_python_exec, 0o755)
                print("here == ",mini_python_exec)

            # Run with ProcessBuilder
            ArrayList = autoclass('java.util.ArrayList')
            cmd = ArrayList()
            cmd.add(mini_python_src)
            cmd.add(script_path)

            ProcessBuilder = autoclass('java.lang.ProcessBuilder')
            pb = ProcessBuilder(cmd)
            pb.redirectErrorStream(True)
            env = pb.environment()
            

            #PythonActivity = autoclass('org.kivy.android.PythonActivity')
            #context = PythonActivity.mActivity
            #files_dir = context.getFilesDir().getAbsolutePath()
            env_vars = {
                "PYTHONHOME": f"{files_dir}/app",
                "PYTHONPATH": ":".join([
                    f"{files_dir}/app",
                    f"{files_dir}/app/lib",
                    f"{files_dir}/app/lib/python3.11",
                    f"{files_dir}/app/lib/python3.11/lib-dynload",
                    f"{files_dir}/app/_python_bundle/site-packages"
                ]),
                "LD_LIBRARY_PATH": ":".join([
                    f"{files_dir}/app/lib",  # where _struct.so lives
                    lib_dir                  # where libpython3.11.so lives
                ]),
                "TMPDIR": f"{files_dir}"
            }


            # env_vars = {
            #     "PYTHONHOME": f"{files_dir}/app",
            #     "PYTHONPATH": ":".join([
            #         f"{files_dir}/app",
            #         f"{files_dir}/app/lib",
            #         f"{files_dir}/app/lib/python3.11",
            #         f"{files_dir}/app/lib/python3.11/lib-dynload",
            #         f"{files_dir}/app/_python_bundle/site-packages"
            #     ]),
            #     "LD_LIBRARY_PATH": f"{files_dir}/app/lib",
            #     "TMPDIR": f"{files_dir}"
            #     }
            for key, value in env_vars.items():
                env.put(key, value)


            process = pb.start()

            #Scanner = autoclass('java.util.Scanner')
            #scanner = Scanner(process.getInputStream()).useDelimiter("\\A")
            #output = scanner.next() if scanner.hasNext() else 'No output.'
            #self.output.text = output

            BufferedReader = autoclass('java.io.BufferedReader')
            InputStreamReader = autoclass('java.io.InputStreamReader')

            reader = BufferedReader(InputStreamReader(process.getInputStream()))
            output_lines = []
            line = reader.readLine()
            while line is not None:
                output_lines.append(line)
                line = reader.readLine()

            self.output.text = '\n'.join(output_lines) or 'No output.'

        except Exception as e:
            self.output.text = f"[Error] {e}"

class MiniPythonApp(App):
    def build(self):
        return PythonRunner()

if __name__ == '__main__':
    MiniPythonApp().run()
