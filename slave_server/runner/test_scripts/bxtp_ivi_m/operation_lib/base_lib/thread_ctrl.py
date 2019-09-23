import thread,time
import threading
import os

class FuncThread(threading.Thread):
    
    def __init__(self, func, *params, **paramMap):
        threading.Thread.__init__(self)
        self.func = func
        self.params = params
        self.paramMap = paramMap
        self.rst = None
        self.finished = False

    def run(self):
        self.rst = self.func(*self.params, **self.paramMap)
        self.finished = True

    def getResult(self):
        return self.rst

    def isFinished(self):
        return self.finished

class cmd_port_thread (threading.Thread):
	"""
	class control_ignition_thread
	"""

	def __init__(self, cmd, time):
		"""
		control_ignition_thread __init__
		"""
		threading.Thread.__init__(self)
		self.cmd = cmd
		self.time = time

	def run(self):
		"""
		threading run
		"""
		print self.cmd
		time.sleep(self.time)
		os.system(str(self.cmd))
		print ""
