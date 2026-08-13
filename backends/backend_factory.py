from backends.dds_backend import DDSBackend
#from backends.webrtc_backend import WebRTCBackend

# import logging

class BackendFactory:
	@staticmethod
	def load_backend(backend_name):
		if backend_name == "DDS":
			return DDSBackend()
		# elif backend_name == "WEBRTC":
		# 	return WebRTCBackend()
		else:
			raise ValueError("Invalid backend specified. Check config.py")
		
