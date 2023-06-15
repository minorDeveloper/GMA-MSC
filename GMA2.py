from enum import Enum
from datetime import datetime


class MSCCommandFormat(Enum):
    GeneralLighting = 1
    MovingLights = 2
    All = 127

class MSCCommand(Enum):
    Invalid = 0
    Go = 1
    Stop = 2
    Resume = 3
    Timed_Go = 4
    Set = 6
    Fire = 7
    Go_Off = 11

class GMA2():
    ## Tested
    def __init__(self, logger):
        self.deviceID = '00'
        self.deviceState = {}
        self.logger = logger
        pass

    def processHexArray(self, hexArray):
        hexArray = [x.lower() for x in hexArray]

        if not self.validateHexArray(hexArray): return False

        self.deviceID = hexArray[2]
        commandFormat = MSCCommandFormat(int(hexArray[4],16))
        commandType = MSCCommand(int(hexArray[5],16))
        data = hexArray[6:-2]

        return self.processData(commandType, data)


    # Tested
    def validateHexArray(self, hexArray):
        hexArray = [x.lower() for x in hexArray]

        # Something about the length
        # Assume minimum length of array is 8, with 1 octet for data
        if (len(hexArray) < 8): return False

        # First octet must be 'F0'
        if (hexArray[0] != 'f0'): return False

        # Second octet must be '7F'
        if (hexArray[1] != '7f'): return False

        # Fourth octet must be '02'
        if (hexArray[3] != '02'): return False

        # Fifth octet is the command format

        # Sixth octed is the command type

        # Data validation

        # Last byte must be 'F7'
        if (hexArray[-1] != 'f7'): return False

        return True

    def processData(self, commandType, data):
        
        match commandType:
            case MSCCommand.Go:
                return self.processGo(data)
            case MSCCommand.Stop:
                pass
            case MSCCommand.Resume:
                pass
            case MSCCommand.Timed_Go:
                pass
            case MSCCommand.Set:
                pass
            case MSCCommand.Fire:
                pass
            case MSCCommand.Go_Off:
                pass
        
        return False

    def processGo(self, data):
        # Data will either be 6 or 10 octets long for a valid go
        # TODO check this assumption is valid
        if (len(data) != 6) and (len(data) != 10): return False

        if len(data == 6): 
            cue = self.getCueNumber(data)
            page, executor = ""
        else:
            if (data.count('00') == 0): return False
            
            separatorIndex = data.index('00')
            cue = self.getCueNumber(data[0:separatorIndex])
            page, executor = self.getExecutorNumber(data[separatorIndex+1:])

        if (page == -1 or executor == -1): return False

        self.deviceState["pages"][str(page)][str(executor)]["currentCue"] = cue
        self.deviceState["pages"][str(page)][str(executor)]["lastUpdate"] = datetime.now()

        return True

    def getCueNumber(self, cueData):
        # Confirm that the list contains a valid separator
        if (cueData.count('2e') == 0): return -1

        separatorIndex = cueData.index('2e')
        
        # Separate the cue data list, then remove the first character, and map the strings to ints
        integerList = self.removeFirstChar(cueData[:separatorIndex])
        decimalList = self.removeFirstChar(cueData[separatorIndex+1:])
        
        cueString = self.abListToNumericString(integerList, decimalList)
        cueFloat = float(cueString)

        return cueFloat


    def getExecutorNumber(self, execData):
        # Confirm that the list contains a valid separator
        validSeparatorFound = False
        separatorString = ''
        if (execData.count('2e') != 0):
            validSeparatorFound = True
            separatorString = '2e'
        
        if (execData.count('20') != 0):
            validSeparatorFound = True
            separatorString = '20'
        
        if not validSeparatorFound: return -1

        separatorIndex = execData.index(separatorString)

        execList = self.removeFirstChar(execData[:separatorIndex])
        pageList = self.removeFirstChar(execData[separatorIndex+1:])

        execString = self.listToString(execList)
        pageString = self.listToString(pageList)

        execNum = int(execString)
        pageNum = int(pageString)

        return pageNum, execNum

    # Tested
    def removeFirstChar(self, lst):
        charLst = lst

        for idX, x in enumerate(lst):
            lstX = list(x)
            if len(lstX) == 1: 
                charLst[idX] = lstX[0]
            else:
                try:
                    charLst[idX] = lstX[1:][0]
                except IndexError:
                    self.logger.error("Index Error in remove_first_char")
        
        return charLst
    
    # So simple, not testing
    def listToString(self, aList):
        tempString = ""
        for a in aList:
            tempString += str(a)

        return tempString
    
    # Tested
    def abListToNumericString(self, aList, bList):
        tempString = ""
        if len(aList) == 0: tempString += "0"

        for a in aList:
            tempString += str(a)
        
        tempString += "."

        if len(bList) == 0: tempString += "0"

        for b in bList:
            tempString += str(b)

        return tempString