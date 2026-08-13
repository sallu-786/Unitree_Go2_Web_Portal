import threading
import time
from rclpy.node import Node

class AudioSubscriber(Node):

    def __init__(self,backend_clients):
        super().__init__('audio_subscriber')
        
        
        self.backend_clients = backend_clients

        self.audio_client = self.backend_clients['audio']

        self.latest_command = None
        self._lock = threading.Lock()

        self.get_logger().info("AudioSubscriber initialized")

        self._thread = threading.Thread(target=self._process_commands, daemon=True)
        self._thread.start()

    # -------------------------------
    # PLAY → queued (async)
    # -------------------------------
    def play_sound(self, sound_name: str):
        with self._lock:
            self.latest_command = ("play", sound_name)


    def stop_sound(self):
        self.audio_client.stop_sound()


    def change_volume(self, volume: int):
        try:
            self.get_logger().info(f"Setting volume: {volume}")
            self.audio_client.change_volume(volume)
        except Exception as e:
            self.get_logger().error(f"Volume change failed: {e}")

    def mic_stream(self,audio):
        if audio is None:
            return "No audio"

        sr, data = audio

        self.audio_client.play_raw_audio(data, sr)

        return "🎤 Streaming..."

    # -------------------------------
    # Worker thread (ONLY for play)
    # -------------------------------
    def _process_commands(self):
        while True:
            if self.latest_command:
                with self._lock:
                    cmd, value = self.latest_command
                    self.latest_command = None

                if cmd == "play":
                    try:
                        self.get_logger().info(f"Playing: {value}")
                        threading.Thread(
                            target=self.audio_client.play_sound,
                            args=[value],
                            daemon=True
                        ).start()
                    except Exception as e:
                        self.get_logger().error(f"Play failed: {e}")

            time.sleep(0.05)