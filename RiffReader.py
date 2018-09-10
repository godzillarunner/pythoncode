import os

class RiffException(Exception):
   def __init__(self, arg):
      self.args = [arg]

class RiffFormat:

    def __init__(self):
        self.formatTag = 0
        self.channels = 0
        self.samplesPerSecond = 0
        self.avgBytesPerSecond = 0
        self.blockAlign = 0
        self.bitsPerSample = 0
        self.cbSize = 0

    def clone(self):
        format = RiffFormat()
        format.formatTag = self.formatTag
        format.channels = self.channels
        format.samplesPerSecond = self.samplesPerSecond
        format.avgBytesPerSecond = self.avgBytesPerSecond
        format.blockAlign = self.blockAlign
        format.bitsPerSample = self.bitsPerSample
        format.cbSize = self.cbSize
        return format


class RiffReader:

    INT_SIZE = 4
    SHORT_SIZE = 2
    ID_SIZE = 4
    BUFF_SIZE = 2048

    # chunk id's
    RIFF_ID = "RIFF"
    RIFX_ID = "RIFX"
    WVPK_ID = "WVPK"

    WAVE_ID = "WAVE"
    WAVL_ID = "WAVL"
    AVI_ID = "AVI"

    FACT_ID = "FACT"
    FMT_ID = "FMT "
    DATA_ID = "DATA"
    JUNK_ID = "JUNK"
    LIST_ID = "LIST"
    SLNT_ID = "SLNT"
    INFO_ID = "INFO"

    def __init__(self):
        self.fileStream = None
        self.buffer = None
        self.filePath = ""
        self.fileName = ""
        self.fileHeaderID = "    "
        self.rootChunk = ""
        self.fileSize = 0
        self.fileSizeLeft = 0
        self.chunkID = None
        self.chunkSize = 0
        self.chunkSizeLeft = 0
        self.riffFormat = RiffFormat()

    def getFormat(self):
        return self.riffFormat.clone()

    def getFileType(self):
        return self.fileHeaderID

    def open(self, filePath):
        size = 0
        id = None

        try:
            self.filePath = os.path.abspath(filePath)
            self.fileName = os.path.basename(filePath)
            self.fileSize = os.path.getsize(filePath)
            self.fileSizeLeft = self.fileSize
            self.__close()

            self.fileStream = open(filePath, "rb")

        except IOError:
            raise RiffException("{filePath} may not exist.".format(filePath = self.filePath))
        except:
            raise RiffException("File problem with {filePath}.".format(filePath = self.filePath))

        self.rootChunk = self.__readID()
        if not self.rootChunk.casefold() == RiffReader.RIFF_ID.casefold() and \
            not self.rootChunk.casefold() == RiffReader.RIFX_ID.casefold():
            raise RiffException("Unknown root ID, {rootChunk}.".format(rootChunk = self.rootChunk))
        size = self.__readSize()
        if size > self.fileSizeLeft:
            raise RiffException("Data size of main id is too big, {size}".format(size = size))
        self.fileHeaderID = self.__readID()
        id = self.__nextChunk()
        return id


    def readAll(self, filePath):
        buffer = bytearray()
        totalSize = 0

        try:
            id = self.open(filePath)
            while id!=None and id.casefold() == RiffReader.DATA_ID.casefold():
                (size, readBuffer) = self.__readChunk()
                if size > 0:
                    totalSize += size
                    buffer += readBuffer
                id = self.__nextChunk()
        except Exception as ex:
            totalSize = 0
            buffer = None

        self.__close()
        return (totalSize, buffer)


    def readBytes(self, size):
        readSize = 0
        buffer = None

        while self.chunkID != None:
            if self.chunkSizeLeft > 0:
                (readSize, buffer) = self.__readChunk(size)
                break
            else:
                self.__nextChunk()
        return (readSize, buffer)

    def __close(self):
        if self.fileStream != None:
            try:
                self.fileStream.flush()
                self.fileStream.close()
            except:
                pass

    def __nextChunk(self):
        id = None
        size = 0

        if self.chunkSizeLeft > 0:
            self.fileStream.seek(self.chunkSizeLeft, 1)
            self.fileSizeLeft -= self.chunkSize
            self.chunkSize = 0
            self.chunkSizeLeft = 0
            self.chunkID = None

        while True:
            if self.fileSizeLeft > (RiffReader.INT_SIZE + RiffReader.INT_SIZE):
                id = self.__readID()
                if self.__isList(id):
                    dirSize = self.__readSize()
                    dirHeaderID = self.__readID()
                    if self.__isInfo(dirHeaderID):
                        self.__readInfo(dirSize - RiffReader.ID_SIZE)
                elif self.__isFmt(id):
                    size = self.__readSize()
                    self.__readFmt(size)
                elif self.__isJunk(id):
                    size = self.__readSize()
                    self.__readJunk(size)
                else:
                    self.chunkID = id
                    self.chunkSize = self.__readSize()
                    self.chunkSizeLeft = self.chunkSize
                    break
            else:
                self.chunkID = None
                self.chunkSize = 0
                self.chunkSizeLeft = 0
                id = None
                break

        if id != None:
            id = id.upper()
        return id

    def __readChunk(self, readLen):
        buffer = None

        if readLen > self.chunkSizeLeft:
            readLen = self.chunkSizeLeft

        if readLen > 0:
            buffer = self.fileStream.read(readLen)
            self.fileSizeLeft -= readLen
            self.chunkSizeLeft -= readLen

        return (readLen, buffer)

    def __readFmt(self, readLen):
        if readLen < 16:
            raise RiffException("Format chunk is too small, {readLen}.".format(readLen = readLen))
        self.riffFormat.formatTag = self.__readShort();
        self.riffFormat.channels = self.__readShort();
        self.riffFormat.samplesPerSecond = self.__readInt();
        self.riffFormat.avgBytesPerSecond = self.__readInt();
        self.riffFormat.blockAlign = self.__readShort();
        self.riffFormat.bitsPerSample = self.__readShort();
        if readLen >= 18:
            self.riffFormat.cbSize = self.__readShort()

    def __readInfo(self, readLen):
        while readLen > 8:
            id = self.__readID()
            size = self.__readSize()
            readLen -= (RiffReader.INT_SIZE + RiffReader.INT_SIZE)
            if size > readLen:
                raise RiffException("Info string size, {size}, greater than directory size.".format(size=size))
            str = self.__readStr(size)
            readLen -= size

    def __readJunk(self, readLen):
        self.fileStream.seek(readLen, 1) # seek from current position

    def __readStr(self, readLen):
        strLen = readLen
        charList = []
        self.__readRawBytes(readLen)
        for i in range(readLen-1, 0, -1):
            if self.buffer[i] == 0:
                strLen -= 1
        for i in range(strLen):
            charList.append(chr(self.buffer[i]))
        retVal = "".join(charList)
        return retVal


    def __readID(self):
        retVal = ""
        try:
            cBuffer = self.fileStream.read(RiffReader.ID_SIZE)
            if RiffReader.ID_SIZE != len(cBuffer):
                raise RiffException("Error in id read size, {readLen}.".format(readLen = len(cBuffer)))
            self.fileSizeLeft -= RiffReader.ID_SIZE
            retVal = "".join((chr(cBuffer[0]), chr(cBuffer[1]), chr(cBuffer[2]), chr(cBuffer[3])))
        except:
            raise RiffException("Error reading an id.")
        return retVal

    def __readSize(self):
        size = self.__readInt()
        if (size & 1) == 1:
            size += 1
        if size > self.fileSizeLeft:
            raise RiffException("Chunk size is too large, {size}.".format(size = size))
        return size

    def __readShort(self):
        retVal = 0
        try:
            iBuffer = self.fileStream.read(RiffReader.SHORT_SIZE)
            if RiffReader.SHORT_SIZE != len(iBuffer):
                raise RiffException("Error in short read size, {readLen}.".format(readLen = len(iBuffer)))
            self.fileSizeLeft -= RiffReader.SHORT_SIZE
            retVal = int((iBuffer[1] << 8) | iBuffer[0])
        except:
            raise RiffException("Error reading a short.")
        return retVal

    def __readInt(self):
        retVal = 0
        try:
            iBuffer = self.fileStream.read(RiffReader.INT_SIZE)
            if RiffReader.INT_SIZE != len(iBuffer):
                raise RiffException("Error in int read size, {readLen}.".format(readLen = len(iBuffer)))
            self.fileSizeLeft -= RiffReader.INT_SIZE
            retVal = int((iBuffer[3] << 24) | (iBuffer[2] << 16) | (iBuffer[1] << 8) | iBuffer[0])
        except:
            raise RiffException("Error reading an int.")
        return retVal

    def __readRawBytes(self, readLen):
        if readLen > RiffReader.BUFF_SIZE:
            raise RiffException("number of bytes, {readLen} too large for internal buffer".format(readLen=readLen))
        try:
            self.buffer = bytearray(self.fileStream.read(readLen))
            size = len(self.buffer)
            if readLen != size:
                raise RiffException("Read length, {readLen}, does not match size, {size}, returned".format(readLen=readLen, size=size))
            self.fileSizeLeft -= readLen
        except:
            raise RiffException("Error reading file")

    def __isList(self, id):
        if id.casefold() == RiffReader.LIST_ID.casefold():
            return True
        return False

    def __isInfo(self, id):
        if id.casefold() == RiffReader.INFO_ID.casefold():
            return True
        return False

    def __isFmt(self, id):
        if id.casefold() == RiffReader.FMT_ID.casefold():
            return True
        return False

    def __isJunk(self, id):
        if id.casefold() == RiffReader.JUNK_ID.casefold():
            return True
        return False






