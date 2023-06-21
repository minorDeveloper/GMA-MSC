from GMA2Page import GMA2Page

class GMA2State():
    def __init__(self):
        self.pages = []
    

    def updateExecutor(self, _pageNumber, _executor):
        for p in self.pages:
            if p.pageNumber == _pageNumber:
                p.updateExecutor(_executor)
                return
        
        self.pages.append(GMA2Page(_pageNumber, [_executor]))

    def sortPages(self):
        self.pages.sort(key=lambda x:x.pageNumber)

    def serialise(self):
        self.sortPages()

        serialPages = {}

        for p in self.pages:
            pNumber, pData = p.serialise()
            serialPages[str(pNumber)] = pData

        return {"state": "initialised", "data": serialPages}