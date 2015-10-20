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
import MOD, MDM

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

print "Watchdog Script started"

########################################################
# Variables
########################################################
reboot_counter = 0
reboot_counter_max = 2880

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
    
def reset_watchdog():
    sendAT('AT#ENHRST=1,10')

########################################################
# Main loop
########################################################
try:
    global reboot_counter
    global reboot_counter_max
    
    while(1):
        print 'RebootCounter: %d Max: %d' % (reboot_counter, reboot_counter_max)
        reset_watchdog()
        MOD.sleep(300)
        reboot_counter = reboot_counter + 1
        if(reboot_counter > reboot_counter_max):
            reboot()
except Exception, e:
    reboot()
