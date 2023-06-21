from datetime import datetime
from enum import Enum

class MSCCommand(Enum):
    Invalid = 0
    Go = 1
    Stop = 2
    Resume = 3
    Timed_Go = 4
    Set = 6
    Fire = 7
    Go_Off = 11

class GMA2Executor:
    def __init__(self, _number, _cue = -1, _fader = -1, _lastCommand = MSCCommand.Invalid, _lastUpdate = datetime.now()):
        self.number = _number
        self.cue = _cue
        self.fader = _fader
        self.lastCommand = _lastCommand
        self.lastUpdate = _lastUpdate


    def update(self, _executor):
        if _executor.number != self.number:
            return
        
        if _executor.cue != -1:
            self.cue = _executor.cue

        if _executor.fader != -1:
            self.fader = _executor.fader
        
        self.lastUpdate = _executor.lastUpdate

    def updateCue(self, _cue):
        self.cue = _cue
        self.lastUpdate = datetime.now()

    def updateFader(self, _fader):
        self.fader = _fader
        self.lastUpdate = datetime.now()

    def serialise(self):
        return self.number, {
            "executorNumber": self.number, 
            "cue": self.cue, 
            "fader": self.fader, 
            "lastCommand": self.lastCommand, 
            "lastUpdate": self.lastUpdate
        }