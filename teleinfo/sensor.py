import asyncio
import logging

import serial
import serial_asyncio

from homeassistant import config_entries, core
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import SensorEntity
from .utils import StatusRegisterParser
from .const import TELEINFO_KEY, DOMAIN, TeleinfoProtocolType, TeleinfoIndex, EURIDIS_MANUFACTURER, EURIDIS_DEVICE, TELEINFO_STATUS_REGISTER


logger = logging.getLogger(__name__)

# async def async_setup(hass, config) -> bool:
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the custom serial sensor platform."""
    # Create an asyncio Event
    teleinfo_integration_initialyzed = asyncio.Event()

    init_teleinfo_metadata()
    integration = TeleinfoIntegration(type=TeleinfoProtocolType.STANDARD, add_entities_function=async_add_entities)
    integration.on_initialized_change = teleinfo_integration_initialyzed.set
    await integration.setup_serial()

    # Wait for the initialized event
    await teleinfo_integration_initialyzed.wait()
    logger.info(f"Setup complete of teleinfo platform, metrics list {integration.metrics}")

    sensors = integration.get_entities()
    # sensor = TeleinfoMetricSensor(integration)
    async_add_entities(sensors)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    logger.info(f"Setupe Teleinfo serial with config {config}")
    teleinfo_integration_initialyzed = asyncio.Event()

    init_teleinfo_metadata()
    integration = TeleinfoIntegration(port=config["port"], type=config["type"])
    integration.on_initialized_change = teleinfo_integration_initialyzed.set
    await integration.setup_serial()

    # Wait for the initialized event
    await teleinfo_integration_initialyzed.wait()
    logger.info(f"Setup complete of teleinfo platform, metrics list {integration.metrics}")

    sensors = integration.get_entities()
    async_add_entities(sensors)

def init_teleinfo_metadata():
    # Calculate the length of payload to calculate checksum
    for k, v in TELEINFO_KEY.items():
        if v.get("timestamp", False):
            payload_length = len(k) + 1 + 13 + 1 + v["metric_length"] + 1
            v["payload_length"] = payload_length
        else:
            payload_length = len(k) + 1 + v["metric_length"] + 1
            v["payload_length"] = payload_length

class TeleinfoIntegration:

    SERIAL_PARITY = serial.PARITY_EVEN
    SERIAL_STOP_BITS = serial.STOPBITS_ONE
    SERIAL_BYTE_SIZE = serial.SEVENBITS

    START_FRAME_DELIMITER = b'\x02'
    END_FRAME_DELIMITER = b'\x03'

    @staticmethod
    def validate_checksum(data, check):
        chksum = sum([ord(c) for c in data])
        chksum = (chksum & 0x3F) + 0x20
        if chr(chksum) == check:
            return True
        else:
            return False

    def __init__(self, port='/dev/ttyUSB0', type=TeleinfoProtocolType.HISTORIQUE):
        self._serial_reader = None
        self.port = port
        self.device_id = None
        self._device = None
        self.metrics  = set()
        self._sensors = {}
        self._initialized = False
        self.on_initialized_change = None
        self._frame_buffer = b""
        self._frame_dict_buffer = dict()
        self._received_frames = 0
        self.checksum_sensor = None
        self.status_parser = StatusRegisterParser()
        
        if type == TeleinfoProtocolType.STANDARD:
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
            lambda: SerialProtocol(self.on_data_received),
            self.port,
            baudrate=self.BAUD_RATE,
            parity=self.SERIAL_PARITY,
            stopbits=self.SERIAL_STOP_BITS,
            bytesize=self.SERIAL_BYTE_SIZE
        )
        logger.info("Serial integration setup successful")

    def create_entities(self):
        self.parse_device_info()
        for key, value, timestamp in self.metrics:
            if not key == "STGE":
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
        self.checksum_sensor = TeleinfoChecksumErrorSensor(device_info=self.device_info, serial=self.device_id)
        self._sensors["checksum_errors"] = self.checksum_sensor
        self.set_initialized(True)

    def parse_device_info(self):
        if self.device_id:
            manufacturer_code = self.device_id[:2]
            model_code = self.device_id[4:6]
            logger.info(f"Device id is {self.device_id}, manufacturer code is {manufacturer_code} model code is {model_code}")
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

    def get_entities(self):
        return self._sensors.values()

    def on_data_received(self, data):
        # Append the received data to the frame buffer
        
        self._frame_buffer += data
        # logger.debug(f"Received data: {data}")
        # Check if a complete frame has been received
                
        if self.START_FRAME_DELIMITER in self._frame_buffer and self.END_FRAME_DELIMITER in self._frame_buffer: #
            if not self.initialyzed:# Clean buffer until receive start of frame
                start_frame_index = self._frame_buffer.find(self.START_FRAME_DELIMITER)
                end_frame_index = self._frame_buffer.find(self.END_FRAME_DELIMITER)
                # logger.debug(f"INITIALIZATION: start index {start_frame_index} end index {end_frame_index} {self._frame_buffer}")
                if end_frame_index < start_frame_index:
                    logger.debug(f"Strip buffer content: {self._frame_buffer[:start_frame_index]}")
                    self._frame_buffer = self._frame_buffer[start_frame_index:]
                    logger.debug(f"New buffer content: {self._frame_buffer}")
            # logger.debug(self._frame_buffer)
            frames = self._frame_buffer.split(self.END_FRAME_DELIMITER+self.START_FRAME_DELIMITER)
            complete_frames = frames[:-1]
            self._frame_buffer = frames[-1]
            # Process the complete frames and update the sensor
            for frame in complete_frames:
                self._received_frames += 1
                sensor_value = self.parse_frame(frame[1:-1]) # Strip START_FRAME_DELIMITER and END_FRAME_DELIMITER
                # self.update_sensor(sensor_value)

    def parse_frame(self, frame):
        # Parse the frame and extract the sensor value
        # Return the extracted sensor value
        # logger.debug(frame)
        frame_str = frame.decode("ascii")
        if self.initialyzed:
            metrics_lines = frame_str.split("\r\n")
            for l in metrics_lines:
                if metric := self.parse_metric_line(l):
                    self.update_entity(*metric)
        else: # List the metrics to create Entities
            if frame_str.startswith("\n"):
                logger.debug("Frame start with a \\n char")
                frame_str = frame_str[1:]
            metrics_lines = frame_str.split("\r\n")
            logger.debug(f"Initialyze frame: {frame_str}")
            logger.debug(f"Splitted frame: {metrics_lines}")
            for l in metrics_lines:
                if metric := self.parse_metric_line(l):
                    # logger.debug(f"Metric key {metric[0]} {metric[1]}")
                    if metric[0] == "ADSC":
                        self.device_id = metric[1]
                        logger.info("Set teleinfo device id")
                    elif not metric[0] in ("DATE", "VTIC"): # , "STGE"
                        self.metrics.add(metric)
            self.create_entities()

    def parse_metric_line(self, line):
        ar = line.split("\t")
        key = ar[0]
        metric_length = len(ar)
        # logger.debug(ar)
        if key in TELEINFO_KEY:
            try:
                # if ar[0] == "ADSC":
                #     logger.info(f"Received {ar} for ADSC key")
                metadata = TELEINFO_KEY[key]
                payload_length = metadata["payload_length"]
                # If line contain timestamp
                if metric_length == 4:
                    ts = ar[1]
                    value = ar[2]
                    checksum = ar[3]
                elif metric_length == 3:
                    value = ar[1]
                    checksum = ar[2]
                    ts = None
                else:
                    logger.debug(f"Error in line {ar}, not composed by 3 or 4 elements")
                    return None
                if self.validate_checksum(line[:payload_length], checksum):
                    try:
                        value = value.strip()
                        value = metadata["content_type"](value)
                    except ValueError:
                        logger.error(f'Unable to parse value for {key} {value} in type {metadata["content_type"]}')
                    # if key == 'DATE':
                    #     value = ts_tz 
                    return (key, value, ts)
                else:
                    self.checksum_sensor.increment()
                    # logger.debug(f"Error in checksum for {ar}")
            except IndexError:
                logger.warning(f"Error in parsing of line in {ar}")
        else:
            logger.debug(f"Found unknown key: {key} | {ar}")
            
    async def cleanup(self):
        if self._serial_reader:
            self._serial_reader.close()
            await self._serial_reader.wait_closed()


    def update_entity(self, key, value, timestamp):
        # Update the sensor entity with the new value
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


class SerialProtocol(asyncio.Protocol):
    def __init__(self, callback):
        self._callback = callback

    def data_received(self, data):
        if self._callback:
            self._callback(data)

    def connection_lost(self, exc):
        # Handle connection lost event if needed
        pass


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

    async def async_will_remove_from_hass(self):
        # Clean up any resources if needed
        pass

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
