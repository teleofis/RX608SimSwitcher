'''
Copyright (c) 2013-2015, ОАО "ТЕЛЕОФИС"

Разрешается повторное распространение и использование как в виде исходного кода, так и в двоичной форме, 
с изменениями или без, при соблюдении следующих условий:

- При повторном распространении исходного кода должно оставаться указанное выше уведомление об авторском праве, 
  этот список условий и последующий отказ от гарантий.
- При повторном распространении двоичного кода должна сохраняться указанная выше информация об авторском праве, 
  этот список условий и последующий отказ от гарантий в документации и/или в других материалах, поставляемых 
  при распространении.
- Ни название ОАО "ТЕЛЕОФИС", ни имена ее сотрудников не могут быть использованы в качестве поддержки или 
  продвижения продуктов, основанных на этом ПО без предварительного письменного разрешения.

ЭТА ПРОГРАММА ПРЕДОСТАВЛЕНА ВЛАДЕЛЬЦАМИ АВТОРСКИХ ПРАВ И/ИЛИ ДРУГИМИ СТОРОНАМИ «КАК ОНА ЕСТЬ» БЕЗ КАКОГО-ЛИБО 
ВИДА ГАРАНТИЙ, ВЫРАЖЕННЫХ ЯВНО ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ИМИ, ПОДРАЗУМЕВАЕМЫЕ ГАРАНТИИ 
КОММЕРЧЕСКОЙ ЦЕННОСТИ И ПРИГОДНОСТИ ДЛЯ КОНКРЕТНОЙ ЦЕЛИ. НИ В КОЕМ СЛУЧАЕ НИ ОДИН ВЛАДЕЛЕЦ АВТОРСКИХ ПРАВ И НИ 
ОДНО ДРУГОЕ ЛИЦО, КОТОРОЕ МОЖЕТ ИЗМЕНЯТЬ И/ИЛИ ПОВТОРНО РАСПРОСТРАНЯТЬ ПРОГРАММУ, КАК БЫЛО СКАЗАНО ВЫШЕ, НЕ 
НЕСЁТ ОТВЕТСТВЕННОСТИ, ВКЛЮЧАЯ ЛЮБЫЕ ОБЩИЕ, СЛУЧАЙНЫЕ, СПЕЦИАЛЬНЫЕ ИЛИ ПОСЛЕДОВАВШИЕ УБЫТКИ, ВСЛЕДСТВИЕ 
ИСПОЛЬЗОВАНИЯ ИЛИ НЕВОЗМОЖНОСТИ ИСПОЛЬЗОВАНИЯ ПРОГРАММЫ (ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ПОТЕРЕЙ ДАННЫХ, ИЛИ 
ДАННЫМИ, СТАВШИМИ НЕПРАВИЛЬНЫМИ, ИЛИ ПОТЕРЯМИ ПРИНЕСЕННЫМИ ИЗ-ЗА ВАС ИЛИ ТРЕТЬИХ ЛИЦ, ИЛИ ОТКАЗОМ ПРОГРАММЫ 
РАБОТАТЬ СОВМЕСТНО С ДРУГИМИ ПРОГРАММАМИ), ДАЖЕ ЕСЛИ ТАКОЙ ВЛАДЕЛЕЦ ИЛИ ДРУГОЕ ЛИЦО БЫЛИ ИЗВЕЩЕНЫ О 
ВОЗМОЖНОСТИ ТАКИХ УБЫТКОВ.
'''

import sys
import MOD, MDM, GPIO

DEBUG = 0
TMP = 0
 
if(DEBUG):
    import SER
    SER.set_speed('9600')
     
    class SERstdout:
        def __init__(self):
            global TMP
            TMP = 1
        def write(self, s):
            SER.send('%d %s\r' % (MOD.secCounter(), s))
             
    sys.stdout = SERstdout()
    sys.stderr = SERstdout()
else:
    class TMPstdout:
        def __init__(self):
            global TMP
            TMP = 2
        def write(self, s):
            global TMP
            TMP = 3
             
    sys.stdout = TMPstdout()
    sys.stderr = TMPstdout()
 
print "Switcher Script started"

########################################################
# Constants
########################################################
NETWORK_WAIT_TIME = 120     # in seconds
MAIN_LOOP_PERIOD = 5        # in seconds

########################################################
# Variables
########################################################
ACTIVE_SIM = 1

########################################################
# Functions
########################################################
def sendAT(request, response = 'OK', timeout = 3):
    MDM.send(request + '\r', 2)
    result = -2
    data = ''
    timer = MOD.secCounter() + timeout
    while(MOD.secCounter() < timer):
        rcv = MDM.read()
        if(len(rcv) > 0):
            data = data + rcv
            if(data.find(response) != -1):
                result = 0
                break
            if(data.find('ERROR') != -1):
                result = -1
                break
    return (result, data)

def reboot():
    sendAT('AT#ENHRST=1,0')
    sys.exit()

def checkCREG():
    r, s = sendAT('AT+CREG?')
    if(r == 0):
        if(s.find('+CREG: 0,1') != -1):
            return 0
    return -1

def checkCSQ():
    r, s = sendAT('AT+CSQ')
    if(r == 0):
        pos = s.find('+CSQ:')
        if(pos != -1):
            val = int(s[pos+6:].strip().split(',')[0])
            return val
    return -1

# def readCCID():
#     r, s = sendAT('AT#CCID')
#     if(r == 0):
#         pos = s.find('#CCID:')
#         if(pos != -1):
#             val = s[pos+7:pos+25]
#             return val
#     return "ERROR"
    
def initGPIO():
    GPIO.setIOdir(5, 0, 1)
    
def initAT():
    sendAT('ATE0')
    sendAT('ATS0=0')
    sendAT('AT\\R0')

def turnOnSim1():
    GPIO.setIOvalue(5, 0)
    
def turnOnSim2():
    GPIO.setIOvalue(5, 1)

def disableSIM():
    sendAT('AT#SIMDET=0')
    MOD.sleep(40)

def enableSIM():
    sendAT('AT#SIMDET=1')
    MOD.sleep(20)
    
def resetWatchdog():
    MOD.watchdogReset()
    sendAT('AT#ENHRST=1,10')

########################################################
# Main loop
########################################################
try:
    global NETWORK_WAIT_TIME
    global MAIN_LOOP_PERIOD
    global ACTIVE_SIM
    
    print 'TELEOFIS RX608-L4U SIM Card Switcher'
    
    MOD.watchdogEnable(300) # 300 sec = 5 min

    initAT()
    initGPIO()
    print 'GPIO init OK, AT init OK'
    
    print 'Switch to SIM1'
    ACTIVE_SIM = 1
    disableSIM()
    turnOnSim1()
    enableSIM()
    
#     SIM_NOTFOUND = 1
    
    timer = MOD.secCounter() + NETWORK_WAIT_TIME
    
    while(1):
        resetWatchdog()
        
        ring = MDM.getRI()
        if(ring == 1):
            print 'Incoming connection, sleep'
            timer = MOD.secCounter() + NETWORK_WAIT_TIME
            MOD.sleep(MAIN_LOOP_PERIOD * 10)
            continue
        
#         ccid = readCCID()
#         if(ccid.find("ERROR") != -1):
#             SIM_NOTFOUND = 1
#         else:
#             SIM_NOTFOUND = 0
            
#         print 'Active SIM: %d Timer: %d CCID: %s' % (ACTIVE_SIM, timer - MOD.secCounter(), ccid)
        print 'Active SIM: %d Timer: %d' % (ACTIVE_SIM, timer - MOD.secCounter())
        
        creg = checkCREG()
        if(creg == 0):
            csq = checkCSQ()
            print 'REGISTERED CSQ: %d' % (csq)
            if(csq > 10):
                print "CSQ > 10, updating timer"
                timer = MOD.secCounter() + NETWORK_WAIT_TIME
            else:
                print "CSQ <= 10, wait to reconnect"
        else:
            print "NOT REGISTERED"
            
#         if((MOD.secCounter() > timer) or (SIM_NOTFOUND == 1)):
        if(MOD.secCounter() > timer):
            print 'NETWORK_WAIT_TIME timeout'
            if(ACTIVE_SIM == 1):
                print 'Switch to SIM2'
                ACTIVE_SIM = 2
                disableSIM()
                turnOnSim2()
                enableSIM()
                timer = MOD.secCounter() + NETWORK_WAIT_TIME
                continue
            if(ACTIVE_SIM == 2):
                print 'Switch to SIM1'
                ACTIVE_SIM = 1
                disableSIM()
                turnOnSim1()
                enableSIM()
                timer = MOD.secCounter() + NETWORK_WAIT_TIME
                continue
            
        MOD.sleep(MAIN_LOOP_PERIOD * 10)
except Exception, e:
    print 'Exception'
    reboot()
