# IDE_Kivy_Exp
Experiment of run Python script using kivy app for android 
Here simple python code are running well 





But problem is with python multiprocessing 

i was tring to run 
```python
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
```

###
By default there was missing 
files/app/lib/python3.11/lib-dynload/ 
there is no 
multiprocessing.cpython-311.so  _queue.cpython-311.so   _struct.cpython-311.so
_pickle.cpython-311.so           select.cpython-311.so
_posixsubprocess.cpython-311.so  _socket.cpython-311.so
###


But i multiprocessing fails 
so i did maual copied to app using adb commnad 
so i make a directory name lib-dynload and copied manually using adb shell command to that app package 

cp /data/local/tmp/_struct.cpython-311.so files/app/lib/python3.11/                                                                                                     
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/select.cpython-311.so   files/app/lib/python3.11/lib-dynload/                                                                                       >
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/_socket.cpython-311.so   files/app/lib/python3.11/lib-dynload/                                                                                       
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/_multiprocessing.cpython-311.so files/app/lib/python3.11/lib-dynload/                                                                                
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/select.cpython-311.so   files/app/lib/python3.11/lib-dynload/                                                                                       >
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/_pickle.cpython-311.so  files/app/lib/python3.11/lib-dynload/                                                                                       >
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/_queue.cpython-311.so   files/app/lib/python3.11/lib-dynload/                                                                                        
RMX3085L1:/data/user/0/org.test.idekivy $ cp /data/local/tmp/_posixsubprocess.cpython-311.so   files/app/lib/python3.11/lib-dynload/                                                                             >
RMX3085L1:/data/user/0/org.test.idekivy $ ls -l files/app/l                                                                            

after doing these cpied things 
i got in kivy app TextInput
Hello from embedded script!
Python version: 3.11.5 (main, Jun 23 2025, 13:46:46) [Clang 14.0.6 (https://android.googlesource.com/toolchain/llvm-project 4c603efb0
Script path: /data/user/0/org.test.idekivy/files/script.py

But i dont know is multiprocessing running or it silently fails ?

Note this approch is runing simple python code . 
