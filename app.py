import time
from smbus import SMBus
from zope.interface.interface import Method
from I2C_ADC1115 import I2C_ADC1115
from Lcd_I2C import Lcd_I2C
from RPi import GPIO

import threading
import enum

from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from flask import Flask, jsonify, request
from repositories.DataRepository import DataRepository

endpoint = '/api/v1'

## global variables
installatieID = 1

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
I2C = SMBus()
I2C.open(1)
ADC = I2C_ADC1115(I2C, 0x48)

lcd = Lcd_I2C(0x38, 5, 6)
lcd_time_not_used = 0
sleep_drempel = 10
backlight = 19

btn = 12
portA = 25
portB = 21


lijn = 0
scherm = 0



# enum om de code iets overzichtelijker te krijgen.


class schermen(enum.Enum):
    start = 0
    info = 1
    instellingen = 2
    water = 3
    licht = 4


aantal_lijnen = {"start": 2, "info": 3,
                 "instellingen": 3, "water": 100, "licht": 100}


waterstand = 0
vochtigheid = 0
licht_waarde = 0
lampAan = False

# instellingen
spaarstand = True
drempel_vochtigheid = 70
drempel_licht = 30

Naam = "Wolfy's plantbak"


# attuctuators
lamp = 16
water = 20

# start up code (setting averyting right before doing anyting else).
start_data = DataRepository.read_installation_data(installatieID)

spaarstand = start_data["Spaarstand"]
drempel_vochtigheid = start_data["WaterDrempel"]
drempel_licht = start_data["LichtDrempel"]
Naam = start_data["Naam"]

lampdata = DataRepository.read_last_data(installatieID, 4)
lampAan = lampdata["Waarde"]

# Code voor Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'geheim!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False,
                    engineio_logger=False, ping_timeout=1)

CORS(app)


@socketio.on_error()        # Handles the default namespace
def error_handler(e):
    print(e)

# Code voor Hardware


def pulseIn(pin, on):
    duur = 0
    timeoutduur = 0
    pulse_start = time.time()
    while not GPIO.input(pin) == on:
        
        
        
        pulse_end = time.time()
        print( pulse_end - pulse_start)
        if( pulse_end - pulse_start >= 1):
            return 0
    pulse_start=time.time()
    timeoutduur = 0
    while GPIO.input(pin) == on:
        pulse_end = time.time()
        
    pulse_duration = pulse_end - pulse_start
    return pulse_duration


def write_to_lcd():

    global scherm
    global drempel_vochtigheid
    global drempel_licht
    global lijn
    print(schermen.start.value)
    print(scherm == schermen.start.value)
    if(scherm == schermen.start.value):
        lijnen = ["Info", "Instellingen"]

        lcd.set_cursor(0, lijn)
        lcd.print(f"> {lijnen[lijn]}  ")
        lcd.set_cursor(0, lijn-1)
        lcd.print(f"{lijnen[lijn-1]}  ")

    elif(scherm == schermen.info.value):
        lijnen = [f"Waterstand: {waterstand:.0f}%",
                  f"Vochtigheid: {vochtigheid:.0f}%", f"Licht: {licht_waarde:.0f}%"]
        clear_lcd()
        lcd.set_cursor(0, 0)
        lcd.print(f"{lijnen[lijn]}")
        lcd.set_cursor(0, 1)
        lcd.print(f"{lijnen[lijn+1]}")


    elif(scherm == schermen.instellingen.value):
        clear_lcd()
        lijnen = [f"Terug...",
                  f"Water: {drempel_vochtigheid}%", f"Licht: {drempel_licht}%"]

        lcd.set_cursor(0, 0)
        lcd.print(f"> {lijnen[lijn]}")
        lcd.set_cursor(0, 1)
        lcd.print(f"{lijnen[lijn+1]}")

    elif(scherm == schermen.water.value):
        drempel_vochtigheid = lijn
        lcd.set_cursor(0, 0)
        lcd.print(f"+ Water vanaf:")
        lcd.set_cursor(0, 1)
        lcd.print(f"Vochtigheid <{drempel_vochtigheid}%")

    elif(scherm == schermen.licht.value):

        drempel_licht = lijn
        lcd.set_cursor(0, 0)
        lcd.print(f"Lamp Aan vanaf:")
        lcd.set_cursor(0, 1)
        lcd.print(f"Buitenlicht <{drempel_licht}%")


def draaiDetect(channel):
    global lijn
    global lcd_time_not_used
    global backlight
    lcd_time_not_used = 0 
    lcd.send_instruction(0x0C)
    GPIO.output(backlight, GPIO.HIGH)
    if GPIO.input(portA) == 0 and GPIO.input(portB) == 0:

        if(lijn < aantal_lijnen[schermen(scherm).name]-1):
            lijn += 1
        print("rechts")
    elif GPIO.input(portA) == 0 and GPIO.input(portB) == 1:
        if(lijn > 0):
            lijn -= 1
        print("Links")
    write_to_lcd()


def klikDetect(channel):
    
    global scherm
    global lijn
    global drempel_vochtigheid
    global drempel_licht
    global lcd_time_not_used
    global sleep_drempel
    
    if(lcd_time_not_used < sleep_drempel):
        if(scherm == schermen.start.value):
            if(lijn == 0):
                scherm = 1
            elif(lijn == 1):
                scherm = 2
            lijn = 0
            clear_lcd()
            write_to_lcd()

        elif(scherm == schermen.info.value):
            scherm = 0
            lijn = 0
            clear_lcd()
            write_to_lcd()

        elif(scherm == schermen.instellingen.value):
            if(lijn == 0):
                scherm = 0
                lijn = 0
            elif(lijn == 1):
                scherm = 3
                lijn = drempel_vochtigheid
            elif(lijn == 2):
                scherm = 4
                lijn = drempel_licht

            clear_lcd()
            write_to_lcd()

        elif(scherm == schermen.water.value):
            response = DataRepository.Update_installatie(
                installatieID, Naam, spaarstand,  drempel_licht, drempel_vochtigheid)
            scherm = 0
            lijn = 0
            clear_lcd()
            write_to_lcd()

        elif(scherm == schermen.licht.value):
            response = DataRepository.Update_installatie(
                installatieID, Naam, spaarstand,  drempel_licht, drempel_vochtigheid)
            scherm = 0
            lijn = 0
            clear_lcd()
            write_to_lcd()


def clear_lcd():
    lcd.set_cursor(0, 0)
    lcd.print(" "*16)
    lcd.set_cursor(0, 1)
    lcd.print(" "*16)


def code_electonics():
    print("Electonics Started")
    tijd = 5
    minuten = 30
    seconden = 0
    gemiddelde_licht = 0
    gemiddelde_vochtigheid = 0
    gemiddelde_waterstand = 0

    GPIO.setup((btn, portA, portB), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(portA, GPIO.FALLING,
                          callback=draaiDetect, bouncetime=100)
    GPIO.add_event_detect(btn, GPIO.FALLING,
                          callback=klikDetect, bouncetime=1000)
    

    GPIO.setup((16, 20), GPIO.OUT)
    GPIO.setup((23), GPIO.OUT)
    GPIO.setup((27), GPIO.IN)
    data = I2C.read_i2c_block_data(0x48, 0x00, 2)
    data = ADC.get_value(0)
    licht = (((data[0] << 8)+data[1])/32768.0)*100.0
    write_to_lcd()

    global waterstand
    global vochtigheid
    global licht_waarde
    global lampAan
    global drempel_vochtigheid
    global drempel_licht
    global spaarstand
    global lcd_time_not_used
    global sleep_drempel
    global backlight
    GPIO.setup((backlight), GPIO.OUT)
    GPIO.output(lamp, GPIO.HIGH)
    GPIO.output(backlight, GPIO.HIGH)
    while True:
        
        # licht sensor en vochtigheid sensor metingen
        data = I2C.read_i2c_block_data(0x48, 0x00, 2)
        data = ADC.get_value(0)
        licht_waarde = (((data[0] << 8)+data[1])/32768.0)*100.0
        gemiddelde_licht += licht_waarde

        data = ADC.get_value(1)
        vochtigheid = (((((data[0] << 8)+data[1])/65536.0)*200.0))
        gemiddelde_vochtigheid += vochtigheid

        if(scherm == schermen.info.value):
            write_to_lcd()

        # afstand/ hoeveelheid water sensor
        GPIO.output(23, False)
        time.sleep(2)
        GPIO.output(23, True)
        time.sleep(0.00001)
        GPIO.output(23, False)
        duration = pulseIn(27, GPIO.HIGH)
        distance = duration * 17150
        if (distance != 0):
            distance = round(distance, 2)
        
            # 50cm lange buis 0.2(voor de moment random) voor afstand tussen vol water en sensor
            waterstand = (1.2-(distance/50)) * 100
            if waterstand < 0:
                waterstand = 0
            if waterstand > 100:
                waterstand = 100 
        else:
            waterstand = 0
       
        gemiddelde_waterstand += waterstand

        
        with app.test_request_context('/'):
            emit("B2F_Home", {"sensors": {"sensorlicht": {"Sensor_ActuatorId": 3, "Waarde": round(licht_waarde)},
                                          "sensorvochtigheid": {"Sensor_ActuatorId": 2, "Waarde": round(vochtigheid)},
                                          "sensorwatervat": {"Sensor_ActuatorId": 1, "Waarde": round(waterstand)}}}, namespace='/', broadcast=True)
        

        # om de zoveel tijd kijk je naar de sensors
        time.sleep(tijd - 2)
        seconden += tijd
        if(seconden >= 60*minuten):

            if(gemiddelde_licht/((60*minuten)/tijd) < drempel_licht):
                
                GPIO.output(lamp, GPIO.HIGH)
                lampAan = True
                response = DataRepository.add_log(
                    installatieID, 4, 100)
               
            elif(gemiddelde_licht/((60*minuten)/tijd) > drempel_licht):
                
                GPIO.output(lamp, GPIO.LOW)
                lampAan = False
                response = DataRepository.add_log(
                    installatieID, 4, 0)
               

            if(gemiddelde_vochtigheid/((60*minuten)/tijd) < drempel_vochtigheid):
                GPIO.output(water, GPIO.HIGH)
                response = DataRepository.add_log(
                    installatieID, 5, 100)
               
            else:
                GPIO.output(water, GPIO.LOW)
                response = DataRepository.add_log(
                    installatieID, 5, 0)
                

            response = DataRepository.add_log(
                installatieID, 1, gemiddelde_waterstand/((60*minuten)/tijd))
            

            response = DataRepository.add_log(
                installatieID, 2, gemiddelde_vochtigheid/((60*minuten)/tijd))
            

            response = DataRepository.add_log(
                installatieID, 3, gemiddelde_licht/((60*minuten)/tijd))
            

            with app.test_request_context('/'):
                emit("B2F_Lamp", {"lamp": lampAan},
                     namespace='/', broadcast=True)

            gemiddelde_licht = 0
            gemiddelde_vochtigheid = 0
            gemiddelde_waterstand = 0
            seconden = 0
        

        #slaapstand lcd na 5 min
        
        if(lcd_time_not_used >= sleep_drempel ):
            lcd.send_instruction(8)
            GPIO.output(backlight, GPIO.LOW)
        else:
            lcd_time_not_used += tijd
        


thread_electonics = threading.Thread(target=code_electonics)
thread_electonics.start()


def hold_current_data():
    
    global spaarstand
    global drempel_vochtigheid
    global drempel_licht
    global Naam
    global lampAan

    start_data = DataRepository.read_installation_data(installatieID)
    spaarstand = start_data["Spaarstand"]
    drempel_vochtigheid = start_data["WaterDrempel"]
    drempel_licht = start_data["LichtDrempel"]
    Naam = start_data["Naam"]
    
    lampdata = DataRepository.read_last_data(installatieID, 4)
    lampAan = lampdata["Waarde"]
    return {"sensors": {"sensorlicht": {"Sensor_ActuatorId": 3, "Waarde": round(licht_waarde)},
                                    "sensorvochtigheid": {"Sensor_ActuatorId": 2, "Waarde": round(vochtigheid)},
                                    "sensorwatervat": {"Sensor_ActuatorId": 1, "Waarde": round(waterstand)}},
                                    "intallatie": {"Naam": Naam}, "lamp": lampAan}

    # haal alle data op
    # stuur alle data naar de front end





# Backend
print("**** Program started ****")

# API ENDPOINTS


@app.route('/')
def hallo():
    return "Server is running, er zijn momenteel geen API endpoints beschikbaar."


@socketio.on('connect')
def initial_connection():
    print('A new client connect')
    
    

    


@app.route('/api/v1/home')
def home():
    return jsonify(hold_current_data())

@app.route(endpoint +'/licht')
def getlicht():

    global spaarstand
    global drempel_vochtigheid
    global drempel_licht
    global Naam
    
    start_data = DataRepository.read_installation_data(installatieID)
    spaarstand = start_data["Spaarstand"]
    drempel_vochtigheid = start_data["WaterDrempel"]
    drempel_licht = start_data["LichtDrempel"]
    Naam = start_data["Naam"]

    datalicht = DataRepository.read_history_of_sensorid(installatieID, 3)
    datalamp = DataRepository.read_history_of_sensorid(installatieID, 4)
    #print("l")
    return jsonify( {"data":{"grafieklicht": datalicht, "grafieklamp":datalamp, "spaarstand":spaarstand, "lichtdrempel": drempel_licht, "lamp": lampAan} })

    # 
    # # print(data)
    # emit("B2F_Grafiek_lamp", data)

@app.route(endpoint +'/water')
def getwater():

    global spaarstand
    global drempel_vochtigheid
    global drempel_licht
    global Naam
    
    start_data = DataRepository.read_installation_data(installatieID)
    spaarstand = start_data["Spaarstand"]
    drempel_vochtigheid = start_data["WaterDrempel"]
    drempel_licht = start_data["LichtDrempel"]
    Naam = start_data["Naam"]
    
    data_vocht = DataRepository.read_history_of_sensorid(installatieID, 2)
    
    # print(data)
    

    data_watergeven = DataRepository.read_history_of_sensorid(installatieID, 5)
    # print(data)
    

    data_opslag = DataRepository.read_history_of_sensorid(installatieID, 1)
    # print(data)
    

    return jsonify({"data":{"grafiekvocht": data_vocht, "grafiekklep":data_watergeven,"grafiekopslag":data_opslag, "waterdrempel": drempel_vochtigheid}})

@app.route(endpoint +'/installatie/lichtdrempel', methods=['PUT'])
def updatelichtdrempel():
  #  global drempel_licht
    gegevens = DataRepository.json_or_formdata(request)
    #print(gegevens["lichtdrempel"])
    
    response = DataRepository.Update_installatie(installatieID, Naam, spaarstand,  gegevens["lichtdrempel"], drempel_vochtigheid)
   # drempel_licht = gegevens["lichtdrempel"]
    return jsonify(antwoord = response)

@app.route(endpoint +'/installatie/drempel_vochtigheid', methods=['PUT'])
def updatewaterdrempel():
  #  global drempel_licht
    gegevens = DataRepository.json_or_formdata(request)
    #print(gegevens["waterdrempel"])
    
    response = DataRepository.Update_installatie(installatieID, Naam, spaarstand,  drempel_licht , gegevens["waterdrempel"])
   # drempel_licht = gegevens["lichtdrempel"]
    return jsonify(antwoord = response)

# ANDERE FUNCTIES
if __name__ == '__main__':
    socketio.run(app, debug=False, port=5000, host='0.0.0.0')
