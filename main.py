import serial
import time
import libscrc
import json
from paho.mqtt import client as mqtt_client

def mobus_crc_checksum(package):
	data = ''
	for i in range(0, 13):
		data = data + package[i]
	print(data)
	bytes_check = libscrc.modbus(bytearray.fromhex(data))
	bytes_checksum_convert = package[14] + package[13]
	bytes_checksum_int = int(bytes_checksum_convert, 16)
	if(hex(bytes_check) == hex(bytes_checksum_int)):
		print('data: ',hex(bytes_check),' bytes_check: ', hex(bytes_checksum_int))
		return True
	else:
		return False

def publish_message(wind_speed, wind_direction, temperature, humidity, pressure):
	msg_publish = {
		"wind_speed": wind_speed,
		"wind_direction": wind_direction,
		"temperature": temperature,
		"humidity": humidity,
		"pressure": pressure
	}
	print(msg_publish)
	client.publish("weather_sensor_value", json.dumps(msg_publish))
	# print(json.dumps(msg_publish))

send = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

broker = '192.168.88.2'
port = 1883
client = mqtt_client.Client('weather_sensor')
client.connect(broker, port)
print('connect_mqtt')

print('complete initialize serial port')
readValue =  [0x01, 0x03,0x00 ,0x00, 0x00, 0x05, 0x85, 0xC9]
arr = []

while True:
	print('reset buffer')
	send.reset_input_buffer()
	send.write(serial.to_bytes(readValue))
	for i in range(0,3):
		data = send.read().hex()
		# print(data)
		if(data != ''):
#			hex_data = str(data)
			arr.append(data)
	if(len(arr) != 0):
		if(arr[0] == '01'):
			if(arr[1] == '03'):
				if(arr[2] == '0a'):
					for i in range(0, 12):
						# print('hello from inner loop')
						data = send.read().hex()
						# print(data)
						hex_data = int(data, 16)
						arr.append(data)
		# print(arr)
#		arr = ['01','03','0a','01','00','00','00','01','04','03','28','27','3f','55','66']
	if(len(arr) == 15):
		checksum = mobus_crc_checksum(arr)
		if checksum:
			# print('Checksum: ', checksum)
			wind_speed_H = int(arr[3], 16) << 8
			wind_speed_L = int(arr[4], 16)
			wind_speed = (wind_speed_H + wind_speed_L)/100
			wind_direction_H = int(arr[5], 16) << 8
			wind_direction_L = int(arr[6], 16)
			wind_direction = wind_direction_H + wind_direction_L
			temperature_H = int(arr[7], 16) << 8
			temperature_L = int(arr[8], 16)
			temperature = (temperature_H + temperature_L)/10
			humidity_H = int(arr[9], 16) << 8
			humidity_L = int(arr[10], 16)
			humidity = (humidity_H + humidity_L)/10
			pressure_H = int(arr[11], 16) << 8
			pressure_L = int(arr[12], 16)
			pressure = (pressure_H + pressure_L)/10
			print('wind_speed: ', wind_speed, ' m/s')
			print('wind_direction: ', wind_direction, ' degree')
			print('temperature: ', temperature, ' C')
			print('humidity: ', humidity, ' %')
			print('pressure: ', pressure, ' mbar')
			publish_message(wind_speed, wind_direction, temperature, humidity, pressure)
	arr.clear()
	time.sleep(1)
send.close()
