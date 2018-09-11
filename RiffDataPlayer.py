import RiffReader
import pyaudio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

class RiffDataPlayer:

    def __init__(self):
        self.player = pyaudio.PyAudio()
        self.format = self.player.get_format_from_width(2)
        self.channels = 2
        self.framerate = 44100
        self.stream = None
        self.executor = ThreadPoolExecutor(3)
        self.stopFlag = False

    #set the format for the file
    def setFormat(self, riffFormat):
        self.format = self.player.get_format_from_width(int(riffFormat.bitsPerSample / 8))
        self.channels = riffFormat.channels
        self.framerate = riffFormat.samplesPerSecond

    def __playThread(self, callback):
        try:
            if self.stream != None:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

                # close PyAudio
                self.player.terminate()

            self.player = pyaudio.PyAudio()
            self.stream = self.player.open(format=self.format, channels=self.channels, rate=self.framerate,
                                           output=True, stream_callback=callback)
            # start the stream
            self.stream.start_stream()

            # wait for stream to finish or stopFlag to be true
            while not self.stopFlag and (self.stream.is_active() or self.stream.is_stopped()):
                time.sleep(0.1)

            # stop stream
            self.stream.stop_stream()
            self.stream.close()

            # close PyAudio
            self.player.terminate()
            self.stream = None
        except Exception as ex:
            self.stream = None

    def __pauseThread(self):
        if self.stream != None:
            try:
                if self.stream.is_stopped():
                    self.stream.start_stream()
                else:
                    self.stream.stop_stream()
            except Exception as ex:
                self.stream = None

    #play the file on a separate thread
    def play(self, callback):
        try:
            self.stopFlag = False
            result = self.executor.submit(self.__playThread, callback)
        except Exception as ex:
            self.stream = None

    def stop(self):
        try:
            self.stopFlag = True
            while self.stream != None:
                time.sleep(0.1)

        except Exception as ex:
            self.stream = None

    def pause(self):
        result = self.executor.submit(self.__pauseThread)



