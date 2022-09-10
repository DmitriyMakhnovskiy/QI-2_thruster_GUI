import init
import time
from Functions import *
import numpy as np
from pynput import keyboard
from datetime import datetime
from UI import Ui_MainWindow

def set_par(self,series,shunt,c,up,down,current,channel,thr,file_name):
    init.R_series_setting = series
    init.R_shunt_setting = shunt
    init.C_setting = c
    init.factor_up_setting = up
    init.factor_down_setting = down
    init.current_range_setting = current
    init.ch_setting =channel
    init.thrust_setting = thr
    init.name_setting = file_name
    R_series = init.R_series_setting
    msg = self.msg_browser
    msg.append('R_series is '+str(R_series)+' MOhms')
    R_shunt = init.R_shunt_setting
    msg.append('R_shunt is '+str(R_shunt)+' MOhms')
    C = init.C_setting
    msg.append('Capacitance is '+str(C)+' uF')
    current_range = init.current_range_setting
    msg.append('Current range is '+str(current_range))
    Ch = init.ch_setting
    msg.append('Channel: '+str(Ch))
    factor_up = init.factor_up_setting
    msg.append('factor up is '+str(factor_up))
    factor_down = init.factor_down_setting
    msg.append('factor down is '+str(factor_down))
    name = init.name_setting
    msg.append('File name is '+str(name)+'.txt')

    ## Main code starts here
    # Rescaling the measurement parameters
    R_series = R_series * 1.0e+6  # MOhms to Ohms
    R_shunt = R_shunt * 1.0e+6  # MOhms to Ohms
    C = C * 1.0e-6  # uF to F

    # Initial configuration of the device
    GPIO_OFF()
    write_pot(0x00)  # nulling the output of digital potentiometer
    OpAmp_ES('OFF')  # OpAmp is OFF

    # Capacitor charging and discharging characteristic times
    tau_up = R_series * C  # charging characteristic time in seconds
    tau_down = (R_series + R_shunt) * C  # discharging characteristic time in seconds
    initial_discharge = factor_down * tau_down
    msg.append('')
    Ui_MainWindow.printf(self,'Wait for the initial safety discharge of capacitor...'+str(int(initial_discharge))+' s')
    Ui_MainWindow.printf(self,'')
    time.sleep(initial_discharge)
    # Starting measurements
    Ui_MainWindow.printf(self,'Wait, we are calibrating the current sensor...')
    msg.append('')
    # Calibration of the current sensor
    CurrentSensorRange(current_range)
    bias = 0.0
    for i in range(10):
        bias = bias + Read_ADC(self,Ch)
    bias = bias / 10.0
    Ui_MainWindow.printf(self,'Bias voltage measured at the current sensor output = '+str(bias)+' V')
    Ui_MainWindow.printf(self,'')

    Ui_MainWindow.printf(self,'To stop the program, push the "Esc" button')
    Ui_MainWindow.printf(self,'To increase or decrease the voltage by one step push the "Shift" or "Ctrl" button respectively')
    Ui_MainWindow.printf(self,'After each push, wait for the indication!')

    OpAmp_ES('ON')  # OpAmp is ON
    Previous_NS = 0
    HV_start = 0.0

    # Data and time stamp for the file name extension
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y %H:%M")

    folder = '/home/UoPi/Desktop/QI tests'  # The folder where all experiments are saved
    full_name = folder + '/' + name + '.txt'  # Full path to the file
    with open(full_name, "a+") as file:
        l1 = '# QI thruster based on Raspberry Pi 4B\n'
        l2 = '# File name: ' + name + '.txt\n'
        l3 = '# Date and time: ' + timestampStr + '\n'
        l4 = '# Columns: ' + 'OpAmp output (V), HV output (kV), current (uA), thrust (your units)\n'
        l5 = '# Note: Negative values must be treated as invalid\n'
        l6 = '\n'
        file.writelines([l1, l2, l3, l4, l5, l6])
    Ui_MainWindow.printf(self,'')
    Ui_MainWindow.printf(self,'Enter the thrust reading (any units) from the electronic scale into "Thrust" box. Then press SHIFT, CTRL or ESC')
    Ui_MainWindow.printf(self,'')
    with keyboard.Events() as events:
        for event in events:
            result = []
            if event.key == keyboard.Key.esc:
                Ui_MainWindow.printf(self,'The program has been terminated by your request.')
                Ui_MainWindow.printf(self,'Warning: Wait until the capacitor is fully discharged before disconnecting it!')
                GPIO_OFF()
                write_pot(0x00)
                OpAmp_ES('OFF')
                Previous_NS = 0
                HV_start = 0.0
                exit()
            elif event.key == keyboard.Key.shift:
                if str(event) == 'Press(key=Key.shift)':
                    th_box = self.thrust_box.clear()
                    NS_stop, OpAmp, HV_actual = HV_up(self,Previous_NS, factor_up * tau_up)
                    Previous_NS = NS_stop
                    Current = CurrentSensor(self,bias, Ch)
                    Ui_MainWindow.printf(self,'Current through the capacitor = '+str(Current)+' uA')
                    try:
                        thrust = self.thrust_box.value()
                        Ui_MainWindow.printf(self,'Thrust is: '+str(thrust)+' mg')
                        Ui_MainWindow.printf(self,'')
                        Ui_MainWindow.printf(self,'Type in "Thrust box". Then enter SHIFT, CTRL or ESC')
                    except:
                        Ui_MainWindow.printf(self,'')
                        Ui_MainWindow.printf(self,'You entered the number incorrectly')
                        Ui_MainWindow.printf(self,'Try one more time... If incorrectly, the program will be terminated.')
                        Ui_MainWindow.printf(self,'')
                        try:
                            thrust = self.thrust_box.value()
                            Ui_MainWindow.printf(self,'Thrust is: '+str(thrust)+' mg')
                            Ui_MainWindow.printf(self,'Type in "Thrust box". Then enter SHIFT, CTRL or ESC')
                        except:
                            Ui_MainWindow.printf(self,'')
                            Ui_MainWindow.printf(self,'The program was terminated due to an invalid value for the thrust')
                            GPIO_OFF()
                            write_pot(0x00)
                            OpAmp_ES('OFF')
                            exit()
                    result = np.column_stack([OpAmp, HV_actual, Current, thrust])
                    with open(full_name, "a+") as file:
                        np.savetxt(file, result)
                    print('')
            elif event.key == keyboard.Key.ctrl:
                if str(event) == 'Press(key=Key.ctrl)':
                    th_box = self.thrust_box.clear()
                    NS_stop, OpAmp, HV_actual = HV_down(self,Previous_NS, factor_down * tau_down)
                    Previous_NS = NS_stop
                    Current = CurrentSensor(self,bias, Ch)
                    Ui_MainWindow.printf(self,'Current through the capacitor = '+str(Current)+' uA')
                    try:
                        thrust = self.thrust_box.value()
                        Ui_MainWindow.printf(self,'Thrust is: '+str(thrust)+' mg')
                        Ui_MainWindow.printf(self,'')
                        Ui_MainWindow.printf(self,'Type in "Thrust box". Then enter SHIFT, CTRL or ESC')
                    except:
                        Ui_MainWindow.printf(self,'')
                        Ui_MainWindow.printf(self,'You entered the number incorrectly')
                        Ui_MainWindow.printf(self,'Try one more time... If incorrectly, the program will be terminated.')
                        Ui_MainWindow.printf(self,'')

                        try:
                            thrust = self.thrust_box.value()
                            Ui_MainWindow.printf(self,'Thrust is: '+str(thrust)+' mg')
                            Ui_MainWindow.printf(self,'')
                            Ui_MainWindow.printf(self,'Type in "Thrust box". Then enter SHIFT, CTRL or ESC')
                        except:
                            Ui_MainWindow.printf(self,'')
                            Ui_MainWindow.printf(self,'The program was terminated due to an invalid value for the thrust')
                            GPIO_OFF()
                            write_pot(0x00)
                            OpAmp_ES('OFF')
                            exit()
                    result = np.column_stack([OpAmp, HV_actual, Current, thrust])
                    with open(full_name, "a+") as file:
                        np.savetxt(file, result)
                    print('')




