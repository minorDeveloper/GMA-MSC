from enum import Enum
from datetime import datetime
import json

from GMA2Executor import GMA2Executor
from GMA2Executor import MSCCommand
from GMA2State import GMA2State

class MSCCommandFormat(Enum):
    GeneralLighting = 1
    MovingLights = 2
    All = 127





class GMA2():
    ## Tested
    def __init__(self, logger):
        self.deviceID = '00'
        self.deviceState = GMA2State()
        self.logger = logger
        pass

    def processHexArray(self, hexArray):
        hexArray = [x.lower() for x in hexArray]

        if not self.validateHexArray(hexArray): return False

        self.deviceID = hexArray[2]
        commandFormat = MSCCommandFormat(int(hexArray[4],16))
        if int(hexArray[5],16) in MSCCommand._value2member_map_:
            commandType = MSCCommand(int(hexArray[5],16))
        else:
            return False
        data = hexArray[6:-1]

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
                self.logger.warn("Stop command - not implemented")
                return
            case MSCCommand.Resume:
                self.logger.warn("Resume command - not implemented")
                pass
            case MSCCommand.Timed_Go:
                self.logger.warn("Timed Go command - not implemented")
                pass
            case MSCCommand.Set:
                return self.processSet(data)
                pass
            case MSCCommand.Fire:
                self.logger.warn("Fire command - not implemented")
                pass
            case MSCCommand.Go_Off:
                self.logger.warn("Go Off command - not implemented")
                pass
        
        return False
    
    def processSet(self, data):
        if len(data) != 4: return False

        fader = -1
        page = int(data[1], 16)
        executor = int(data[0], 16) + 1

        coarse = int(data[3], 16)
        fine = int(data[2], 16)

        fader = (coarse + fine) / 128.0

        gma2Executor = GMA2Executor(executor)
        gma2Executor.fader = fader
        gma2Executor.lastCommand = MSCCommand.Set
        
        self.deviceState.updateExecutor(page, gma2Executor)
        

        return True
    
    def processTimedGo(self, data):
        return False

        

        return True

    def processGo(self, data):
        # Data will either be 6 or 10 octets long for a valid go
        # TODO check this assumption is valid
        if (len(data) != 9) and (len(data) != 11): return False

        cue = -1
        page = -1
        executor = -1

        if len(data) == 6: 
            cue = self.getCueNumber(data)
            page, executor = "0"
        else:
            if (data.count('00') == 0): return False
            
            separatorIndex = data.index('00')
            cue = self.getCueNumber(data[0:separatorIndex])
            page, executor = self.getExecutorNumber(data[separatorIndex+1:])

        if (page == -1 or executor == -1): return False

        gma2Executor = GMA2Executor(executor)
        gma2Executor.cue = cue
        gma2Executor.lastCommand = MSCCommand.Go
        
        self.deviceState.updateExecutor(page, gma2Executor)
        
           # self.deviceState.update({str(page): {str(executor): {"currentCue": cue, "lastUpdate": datetime.now()}}})
        
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
    
    