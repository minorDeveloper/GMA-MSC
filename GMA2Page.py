from GMA2Executor import GMA2Executor

class GMA2Page:
    def __init__(self, _pageNumber, _executors = []):
        self.pageNumber = _pageNumber
        self.executors = _executors
    
    def updateExecutor(self, _executor):
        for e in self.executors:
            if e.number == _executor.number:
                e.update(_executor)
                return
        
        self.executors.append(_executor)

    def sortExecutors(self):
        self.executors.sort(key=lambda x:x.number)

    def serialise(self):
        self.sortExecutors()
        
        serialExecutors = {}

        for e in self.executors:
            eNumber, eData = e.serialise()
            serialExecutors[str(eNumber)] = eData

        return self.pageNumber, serialExecutors