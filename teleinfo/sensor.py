import asyncio
import logging

import serial
import serial_asyncio

from homeassistant import config_entries, core
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import SensorEntity
from .utils import StatusRegisterParser
from .const import TELEINFO_KEY, START_FRAME_DELIMITER, END_FRAME_DELIMITER, DOMAIN, TeleinfoProtocolType, TeleinfoIndex, EURIDIS_MANUFACTURER, EURIDIS_DEVICE, TELEINFO_STATUS_REGISTER


logger = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    logger.info(f"Setup Teleinfo serial with config {config}")
    teleinfo_integration_initialyzed = asyncio.Event()

    integration = TeleinfoIntegration(port=config["port"], type=config["type"])
    integration.on_initialized_change = teleinfo_integration_initialyzed.set
    await integration.setup_serial()

    # Wait for the initialized event
    await teleinfo_integration_initialyzed.wait()
    logger.info(f"Setup complete of teleinfo platform, metrics list {integration.metrics}")

    sensors = integration.get_entities()
    async_add_entities(sensors)

class TeleinfoChecksumErrorSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = "Téléinfo"

    def __init__(self, **kwargs):
        self._state = 0
        self._device_info = kwargs.get("device_info")
        self._device_serial = kwargs.get("serial")
        self._attr_unique_id = f"teleinfo_{self._device_serial}_checksum_error"

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def name(self):
        return f"Teleinfo checksum errors"

    @property
    def state(self):
        return self._state
    
    def increment(self):
        self._state += 1
        self.async_write_ha_state()


class TeleinfoMetricSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = "Téléinfo"

    def __init__(self, key, value=None, **kwargs):
        self._key = key
        self._state = value
        self._device_info = kwargs.get("device_info")
        self._device_serial = kwargs.get("serial")
        self._attr_unique_id = f"teleinfo_standard_{self._device_serial}_{self._key}"

        if c := kwargs.get("property"):
            self.property = c
            self._attr_device_class = c._attr_device_class
            self._attr_native_unit_of_measurement = c._attr_native_unit_of_measurement
            self._attr_state_class = c._attr_state_class

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def name(self):
        return f"Teleinfo {self._key}"

    @property
    def state(self):
        return self._state
    
    def set_value(self, value):
        if self._state != value:
            self._state = value
            self.async_write_ha_state()
    
    def set_disabled(self):
        self._attr_entity_registry_enabled_default = False

    # async def async_added_to_hass(self):
    #     await self._integration.setup()

    # async def async_will_remove_from_hass(self):
    #     # Clean up any resources if needed
    #     pass

class TeleinfoStatusRegisterSensor(TeleinfoMetricSensor):

    def __init__(self, key, value=None, **kwargs):
        self._name = key
        try:
            self._value_mapping = TELEINFO_STATUS_REGISTER[key]
        except KeyError:
            logger.error(f"Unable to find value mapping for key {key}")
        super().__init__(key, value=value, **kwargs)
        self._attr_unique_id = f"teleinfo_standard_{self._device_serial}_status_register_{self._name}"

    @property
    def name(self):
        return f"Teleinfo {self._name.replace('_', ' ').title()}"

    @property
    def state(self):
        try:
            return self._value_mapping[int(self._state)]
        except (ValueError, TypeError):
            logger.warning(f"Unable to find state {self._state} in {self._value_mapping} for {self._name}")

class ChecksumValidationError(Exception):
    """Error on checksum line validation"""

class TeleinfoIntegration:

    SERIAL_PARITY = serial.PARITY_EVEN
    SERIAL_STOP_BITS = serial.STOPBITS_ONE
    SERIAL_BYTE_SIZE = serial.SEVENBITS

    START_FRAME_DELIMITER = b'\x02'
    END_FRAME_DELIMITER = b'\x03'

    @staticmethod
    def _validate_checksum(data, check):
        chksum = sum([ord(c) for c in data])
        chksum = (chksum & 0x3F) + 0x20
        if chr(chksum) == check:
            return True
        else:
            raise ChecksumValidationError()

    def validate_checksum(self, data, check):
        if self._checksum_control_mode and self._checksum_control_mode == 2:
            return self._validate_checksum(data, check)
        elif self._checksum_control_mode and self._checksum_control_mode == 1:
            return self._validate_checksum(data[:-1], check)
        else:
            try:
                result = self._validate_checksum(data, check)
                if result:
                    self._checksum_control_mode = 2
                    logger.debug("Set checksum control methode to mode 2")
                return result 
            except ChecksumValidationError:
                result = self._validate_checksum(data[:-1], check)
                if result:
                    self._checksum_control_mode = 1
                    logger.debug("Set checksum control methode to mode 1")
                    return result
                else:
                    raise

    def __init__(self, port='/dev/ttyUSB0', type=TeleinfoProtocolType.HISTORIQUE):
        self._serial_reader = None
        self.port = port
        self.device_id = None
        self.type = type
        self._device = None
        self.metrics  = set()
        self._sensors = {}
        self._initialized = False
        self.on_initialized_change = None
        self._frame_buffer = b""
        self._frame_dict_buffer = dict()
        self._received_frames = 0
        self._checksum_control_mode = None
        self.checksum_sensor = None
        self.status_parser = StatusRegisterParser()
        
        if self.type == TeleinfoProtocolType.STANDARD:
            self.BAUD_RATE = 9600
        else:
            self.BAUD_RATE = 1200

    @property
    def initialyzed(self):
        return self._initialized
    
    @property
    def device_info(self):
        return self._device
    
    def set_initialized(self, value):
        self._initialized = value
        if self.on_initialized_change:
            self.on_initialized_change()

    async def setup_serial(self):
        # Start the serial reader
        self._serial_reader = await serial_asyncio.create_serial_connection(
            asyncio.get_running_loop(),
            # lambda: SerialProtocol(self.on_data_received),
            lambda: SerialProtocol(self.on_frame_received),
            self.port,
            baudrate=self.BAUD_RATE,
            parity=self.SERIAL_PARITY,
            stopbits=self.SERIAL_STOP_BITS,
            bytesize=self.SERIAL_BYTE_SIZE
        )

    def get_entities(self):
        return self._sensors.values()

    def on_frame_received(self, frame):
        # logger.debug(f"New frame received: {frame}")
        sensor_value = self.parse_frame(frame[1:-1])

    # def on_data_received(self, data):
    #     # Append the received data to the frame buffer
        
    #     self._frame_buffer += data
    #     # logger.debug(f"Received data: {data}")
    #     # Check if a complete frame has been received
                
    #     if self.START_FRAME_DELIMITER in self._frame_buffer and self.END_FRAME_DELIMITER in self._frame_buffer: #
    #         if not self.initialyzed:# Clean buffer until receive start of frame
    #             start_frame_index = self._frame_buffer.find(self.START_FRAME_DELIMITER)
    #             end_frame_index = self._frame_buffer.find(self.END_FRAME_DELIMITER)
    #             # logger.debug(f"INITIALIZATION: start index {start_frame_index} end index {end_frame_index} {self._frame_buffer}")
    #             if end_frame_index < start_frame_index:
    #                 logger.debug(f"Strip buffer content: {self._frame_buffer[:start_frame_index]}")
    #                 self._frame_buffer = self._frame_buffer[start_frame_index:]
    #                 logger.debug(f"New buffer content: {self._frame_buffer}")
    #         # logger.debug(self._frame_buffer)
    #         frames = self._frame_buffer.split(self.END_FRAME_DELIMITER+self.START_FRAME_DELIMITER)
    #         complete_frames = frames[:-1]
    #         self._frame_buffer = frames[-1]
    #         # Process the complete frames and update the sensor
    #         for frame in complete_frames:
    #             self._received_frames += 1
    #             sensor_value = self.parse_frame(frame[1:-1]) # Strip START_FRAME_DELIMITER and END_FRAME_DELIMITER
    #             # self.update_sensor(sensor_value)

    def parse_frame(self, frame):
        # Parse the frame and extract the sensor value
        # Return the extracted sensor value
        # logger.debug(frame)
        frame_str = frame.decode("ascii")
        if self.initialyzed:
            for l in frame_str.split("\r\n"):
                if metric := self.parse_line(l):
                    self.update_entity(*metric)
        else: # List the metrics to create Entities
            logger.debug(f"Initialization frame received: {frame_str}")
            self.setup_entities(frame_str)
            
    def parse_line(self, line):
        ar = line.split() # Standard = "\t" historique = " "
        key = ar[0]
        metric_parts_length = len(ar)
        try:
            metadata = TELEINFO_KEY[key]
            payload_length = metadata["payload_length"]
            # If line contain timestamp
            if metric_parts_length == 4:
                ts = ar[1]
                value = ar[2]
                checksum = ar[3]
            elif metric_parts_length == 3:
                value = ar[1]
                checksum = ar[2]
                ts = None
            else:
                logger.debug(f"Error in line {ar}, not composed by 3 or 4 elements")
                return None
            self.validate_checksum(line[:payload_length], checksum)
            # if self.type == TeleinfoProtocolType.STANDARD: # TODO: Implement checksum control for historique
            #     self.validate_checksum(line[:payload_length], checksum)
            # else:
            #     logger.debug(f"Historique data to control: |{line[:payload_length]}|checksum chr: {checksum}")
            value = value.strip()
            value = metadata["content_type"](value)
            return (key, value, ts)
        except KeyError:
            logger.debug(f"Found unknown key: {key} | {ar}")
        except ValueError:
            logger.debug(f'Unable to parse value for {key} {value} in type {metadata["content_type"]}')
        except IndexError:
            logger.debug(f"Error in parsing of line in {ar}")
        except ChecksumValidationError:
            try:
                self.checksum_sensor.increment()
            except AttributeError:
                pass # Checksum sensor is not initialyzed yet
            # logger.debug(f"Error in checksum for {ar}")
        

    def update_entity(self, key, value, timestamp):
        # Update the sensor entity with the new value
        try:
            if key != "STGE":
                entity = self._sensors.get(key)
                if entity:
                    # logger.debug(f"Update sensor {key} with value {value}")
                    entity.set_value(value)
            else:
                self.status_parser.parse_str(value)
                for status_key in TELEINFO_STATUS_REGISTER.keys():
                    entity = self._sensors.get(f"status_register|{status_key}")
                    entity.set_value(getattr(self.status_parser, status_key))
        except Exception:
            logger.debug(f"Unable to update entity key {key} with value: {value}")

    def setup_entities(self, frame_str):
        metrics_lines = frame_str.split("\r\n")
        logger.debug(f"Initialyze frame: {frame_str}")
        logger.debug(f"Splitted frame: {metrics_lines}")
        for l in metrics_lines:
            if metric := self.parse_line(l):
                if metric[0] in ("ADCO", "ADSC"):
                    self.device_id = metric[1]
                    logger.info("Set teleinfo device id")
                    self.set_device_info()
                elif not metric[0] in ("DATE", "VTIC"): # , "STGE"
                    self.metrics.add(metric)
        self.set_entities()

    def set_device_info(self):
        if self.device_id:
            manufacturer_code = self.device_id[:2]
            model_code = self.device_id[4:6]
            logger.debug(f"Device id is {self.device_id}, manufacturer code is {manufacturer_code} model code is {model_code}")
            manufacturer_name = EURIDIS_MANUFACTURER.get(manufacturer_code)
            model_name = EURIDIS_DEVICE.get(model_code)
            self._device = DeviceInfo(
            identifiers={
                (DOMAIN, self.device_id)
            },
            name=f"PRM_{self.device_id}",
            manufacturer=manufacturer_name,
            model=model_name
        )

    def set_entities(self):
        for key, value, timestamp in self.metrics:
            if not key == "STGE": # Manage alla lines that are not status register
                properties = TELEINFO_KEY[key]
                properties_class = properties.get("class")
                sensor = TeleinfoMetricSensor(key, value, device_info=self.device_info, serial=self.device_id, property=properties_class)
                if properties_class == TeleinfoIndex and int(value) == 0: #Avoid to create sensor for unused index
                    sensor.set_disabled()
                self._sensors[key] = sensor
            else: # Manage status register differently since it host multiple sensors
                self.status_parser.parse_str(value)
                for status_key in TELEINFO_STATUS_REGISTER.keys():
                    status_value = getattr(self.status_parser, status_key)
                    # logger.debug(f"Init status {status_key}, with value {status_value}")
                    sensor = TeleinfoStatusRegisterSensor(status_key, value=status_value, device_info=self.device_info, serial=self.device_id)
                    # logger.info(f"Parse status register and check contact sec status {self.status_parser.contact_sec}")
                    self._sensors[f"status_register|{status_key}"] = sensor
        # Setup base checksum error sensor to count checksum error
        self.checksum_sensor = TeleinfoChecksumErrorSensor(device_info=self.device_info, serial=self.device_id)
        self._sensors["checksum_errors"] = self.checksum_sensor
        self.set_initialized(True)
            
    async def cleanup(self):
        if self._serial_reader:
            self._serial_reader.close()
            await self._serial_reader.wait_closed()


class SerialProtocol(asyncio.Protocol):
    def __init__(self, callback):
        self._callback = callback
        self._buffer = b""
        self._incomplete_frame = True

    # def data_received(self, data):
    #     if self._callback:
    #         self._callback(data)

    def data_received(self, data):
        self._buffer += data
        self.process_buffer()

    def process_buffer(self):
        while START_FRAME_DELIMITER in self._buffer:
            start_index = self._buffer.find(START_FRAME_DELIMITER)
            self._buffer = self._buffer[start_index:]

            end_index = self._buffer.find(END_FRAME_DELIMITER)
            if end_index != -1:
                complete_frame = self._buffer[1:end_index]
                self._callback(complete_frame)
                self._buffer = self._buffer[end_index + 1:]
                self.incomplete_frame = False
            else:
                self.incomplete_frame = True
                break

    #     if START_FRAME_DELIMITER in self._buffer and END_FRAME_DELIMITER in self._buffer: #
    #         start_frame_index = self._buffer.find(START_FRAME_DELIMITER)
    #         end_frame_index = self._buffer.find(END_FRAME_DELIMITER)
    #         # logger.debug(f"INITIALIZATION: start index {start_frame_index} end index {end_frame_index} {self._buffer}")
    #         if end_frame_index < start_frame_index:
    #             # logger.debug(f"Strip buffer content: {self._buffer[:start_frame_index]}")
    #             self._frame_buffer = self._buffer[start_frame_index-2:]
    #             # logger.debug(f"New buffer content: {self._buffer}")
    #         # logger.debug(self._frame_buffer)
    #             frames = self._buffer.split(END_FRAME_DELIMITER)
    #         else:
    #             frames = self._buffer.split(END_FRAME_DELIMITER+START_FRAME_DELIMITER)
    #         complete_frames = frames[:-1]
    #         self._buffer = frames[-1]
    #         # Process the complete frames and update the sensor
    #         for frame in complete_frames:
    #             self._callback(frame[1:-1])
                # sensor_value = self.parse_frame(frame[1:-1]) # Strip START_FRAME_DELIMITER and END_FRAME_DELIMITER
        # while True:
        #     start_index = self._buffer.find(START_FRAME_DELIMITER)
        #     end_index = self._buffer.find(END_FRAME_DELIMITER)
        #     if start_index != -1 and end_index != -1:
        #         complete_frame = self._buffer[start_index + 1:end_index]
        #         asyncio.ensure_future(self._callback(complete_frame))
        #         self._buffer = self._buffer[end_index + 1:]
        #     else:
        #         break
