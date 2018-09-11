import RiffReader
import RiffDataPlayer
import pyaudio
import time
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QFileDialog, QLabel
from PyQt5 import QtCore, QtGui, Qt

class RiffUI(QWidget):

    def __init__(self):
        super().__init__()
        self.riffReader = None
        self.player = RiffDataPlayer.RiffDataPlayer()
        self.fileName = None
        self.pauseButton = None
        self.initUI()

    def initUI(self):
        self.fileName = QLabel(self)
        self.fileName.setGeometry(100, 50, 420, 24)
        self.fileName.setAlignment(QtCore.Qt.AlignRight)
        self.fileName.setText("")

        openButton = QPushButton('Open', self)
        openButton.clicked.connect(self.playFile)
        openButton.resize(openButton.sizeHint())
        openButton.move(20, 50)

        self.pauseButton = QPushButton('Pause', self)
        self.pauseButton.clicked.connect(self.pausePlay)
        self.pauseButton.resize(openButton.sizeHint())
        self.pauseButton.move(20, 100)

        self.resize(550, 300)
        self.move(300, 300)
        self.setWindowTitle("Riff Reader")
        self.show()

    #callback routine for obtaining more wave data
    def riffCallback(self, in_data, frame_count, time_info, status):
        (size, data) = self.riffReader.readBytes(4 * frame_count)
        return (data, pyaudio.paContinue)

    #open a file
    def playFile(self):
        self.fileName.setText("")
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        #dlg.setFilter("Wave files (*.wav)")

        openFile = ""
        if dlg.exec_():
            fileList = dlg.selectedFiles()
            if len(fileList) > 0:
                openFile = dlg.selectedFiles()[0]

        if len(openFile) > 0:
            self.fileName.setText(openFile)
            self.player.stop()
            self.riffReader = RiffReader.RiffReader()

            try:
                mainID = self.riffReader.open(openFile)
                if mainID != None:
                    self.player.setFormat(self.riffReader.getFormat())
                    self.player.play(self.riffCallback)
            except Exception as ex:
                openFile = ""

    #pause or resume playing
    def pausePlay(self):
        self.player.pause();

    def stopPlayer(self):
        self.player.stop();


app = QApplication(sys.argv)
riffUI = RiffUI()
exitValue = app.exec_()
riffUI.stopPlayer()
sys.exit(exitValue)


