import pytest
import logging

from GMA2 import GMA2

# ['f0', '7f', '0', '2', '1', '1', '30', '2e', '33', '35', '30', 'f7']
# ['f0', '7f', '0', '2', '1', '4', '0', '0', '0', '0', '0', '30', '2e', '33', '31', '30', 'f7']

logger = logging.getLogger('GMA2_test')

@pytest.fixture
def gma2():
    return GMA2(logger)

def test_init_deviceID(gma2):
    assert gma2.deviceID == '00'

def test_init_deviceState(gma2):
    assert gma2.deviceState == {}

def test_validateHexArray(gma2):
    assert gma2.validateHexArray(['00', '00', '00', '00', '00', '00', '00', '00']) == False
    assert gma2.validateHexArray(['00', '00', '00', '00', '00', '00', '00', '00', '00']) == False
    assert gma2.validateHexArray(['F0', '00', '00', '00', '00', '00', '00', '00', '00']) == False
    assert gma2.validateHexArray(['F0', '7F', '00', '00', '00', '00', '00', '00', '00']) == False
    assert gma2.validateHexArray(['F0', '7F', '00', '02', '00', '00', '00', '00', '00']) == False
    assert gma2.validateHexArray(['f0', '7f', '00', '02', '00', '00', '00', '00', 'F7']) == True
    assert gma2.validateHexArray(['f0', '7f', '00', '02', '01', '04', '00', '00', '00', '00', '00', '30', '2e', '33', '31', '30', 'f7']) == True
    assert gma2.validateHexArray(['f0', '7f', '00', '02', '01', '01', '30', '2e', '33', '35', '30', 'f7']) == True

def test_abListToNumericString(gma2):
    string1 = "123"
    string2 = "456"
    assert gma2.abListToNumericString(string1, string2) == "123.456"

    assert gma2.abListToNumericString("", string2) == "0.456"

    assert gma2.abListToNumericString(string1, "") == "123.0"

    assert gma2.abListToNumericString("","") == "0.0"

def test_removeFirstChar(gma2):
    list1 = ['f0', '7f', '00', '02']
    list2 = ['f0', 'f', '00', '02']
    list3 = ['f0', 'f', '0', '02']
    removedList = ['0','f','0','2']

    assert gma2.removeFirstChar(list1) == removedList
    assert gma2.removeFirstChar(list2) == removedList
    assert gma2.removeFirstChar(list3) == removedList

def test_getExecutorNumber(gma2):
    assert gma2.getExecutorNumber(['32', '22', '31']) == -1
    assert gma2.getExecutorNumber(['32', '2e', '31']) == (1, 2)
    assert gma2.getExecutorNumber(['32', '2e', '31', '34']) == (14, 2)
    assert gma2.getExecutorNumber(['32', '35', '2e', '31']) == (1, 25)
    assert gma2.getExecutorNumber(['32', '35', '2e', '31', '34']) == (14, 25)


def test_processHexArray_noExecutorGo():
    gma2_local = GMA2(logger)

    hexArray = ['f0', '7f', '7f', '02', '7F', '03', '30', '2E', '30', '30', '30', 'F7']

    assert gma2_local.processHexArray(hexArray) == True

    assert gma2_local.deviceState != {}