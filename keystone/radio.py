import logging

from keystone.constants import *
from keystone.interface import Interface
from keystone.program import Program
from keystone.invalid_device_error import InvalidDeviceError
from keystone.operation_failed_error import OperationFailedError

# It appears that the Keystone interface returns incorrect (Large) values of channels on occasion
# This value stops the consumption of large amounts of memory in these cases
MAX_DAB_CHANNELS = 128

"""Radio"""
class Radio(object):
    def __init__(self, device, mode = DAB, usehardmute = True):
        """
        Initializes the Radio object.

        Keyword arguments:

        device       -- Path to the serial device. eg /dev/ttyACM0
        mode         -- Either the DAB or FM constant (Note: FM is not implemented yet) (default: DAB)
        userhardmute -- Use hard mute. Boolean (default: True)
        """

        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialised Radio Class")
        self.interface = Interface()
        self.device = device
        self.mode = mode
        self.usehardmute = usehardmute
        self.currently_playing = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    # Initialization functions
    def open(self):
        """
        Open the radio port. Note if you call open directly, you should call close explicitly.
        The preferred way is to initialize the object is:

        with radio.Radio("/dev/ttyACM0") as r:
            r.programs

        raise InvalidDeviceError if the the path can't be opened for what ever reason
        """
        self.logger.info("Opening connection to Keystone DAB Radio")
        if self.interface.open_radio_port(self.device, self.usehardmute) != True:
            self.logger.error("Unable to open DAB Radio on " + self.device)
            raise InvalidDeviceError(self.device)

    def close(self):
        """
        Close the radio port. You only need to do this if your call open explicitly
        """
        self.logger.info("Closing connection to Keystone DAB Radio")
        self.interface.close_radio_port

    def comm_version(self):
        """
        Returns the version of the communication protocol. Possibly not that interesting in everyday use.
        """
        version =  self.interface.comm_version()
        self.logger.debug("Returning communication protocol version: " + str(version))
        return version

    def reset(self):
        """
        Reset the radio
        """
        self.logger.info("Resetting DAB Radio")
        if self.interface.hard_reset_radio() != True:
            self.logger.error("Failed to reset the DAB Radio")
            raise OperationFailedError("Reset failed")

    def is_system_ready(self):
        """
        Returns true when the radio is ready to accept control messages
        """
        ready = self.interface.is_sys_ready() == 1
        self.logger.debug("Returning radio ready state: " + str(ready))
        return ready

    # Volume functions
    def mute(self):
        """
        Mutes the radio
        """
        self.info("Muting the DAB Radio")
        self.interface.volume_mute()

    @property
    def volume(self):
        """
        Returns the current volume. Range: 0-16
        """
        volume = self.interface.get_volume()
        self.logger.debug("Returning current volume: " + str(volume))
        return volume

    @volume.setter
    def volume(self, value):
        """
        Set the current volume.

        Range is 0-16

        Example:

        r.volume = 10

        Raises OperationFailedError if the volume can't be set
        """
        self.logger.debug("Setting volume to: " + str(value))
        if value >= 0 and value <= 16:
            if self.interface.set_volume(value) == -1:
                self.logger.error("Set volume failed")
                raise OperationFailedError("Set volume failed")
            else:
                self.logger.info("Set volume to: " + str(value))
        else:
            self.logger.warning("Attempt to set volume outside allowable range of 0-16, ignoring request")

    # Control functions
    def prev_stream(self):
        """
        Plays the previous stream in the ensemble

        Raises OperationFailedError if the previous stream can't be selected
        """
        self.logger.info("Changing to previous stream/channel")
        if self.interface.prev_stream != True:
            self.logger.error("Could not select the previous stream/channel")
            raise OperationFailedError("Could not select the previous stream")

    def next_stream(self):
        """
        Plays the next stream in the ensemble

        Raises OperationFailedError if the next stream can't be selected
        """
        self.logger.info("Changing to next stream/channel")
        if self.interface.next_stream != True:
            self.logger.error("Could not select next stream/channel")
            raise OperationFailedError("Could not select the next stream")

    def dab_auto_search(self, start_index, end_index, clear = True):
        """
        Searches for radio programs

        Keyword arguments:

        start_index: DAB index to start searching from. 0 is probably a good start.
        end_index: DAB index to end searching to. 40 is a nice number
        clear: If True, the internal channel table will be cleared before the search starts. (default: True)

        Raises OperationFailedError if the previous stream can't be selected
        """
        self.logger.info("Performing a DAB Autosearch (Retune)")
        if clear:
            self.logger.info("Clearing the existing channel database")
            if self.interface.dab_auto_search(start_index, end_index) == False:
                self.logger.error("Auto-search failed")
                raise OperationFailedError("Auto-search failed")
        else:
            if self.interface.dab_auto_search_no_clear(start_index, end_index) == False:
                self.logger.error("Auto-search failed")
                raise OperationFailedError("Auto-search failed")

    def ensemble_name(self, index, namemode):
        """
        Returns the ensemble name of the ensemble at the supplied index.

        Keyword arguments:

        index: DAB index to check
        namemode: DAB or FM (only DAB supported at the moment)

        Returns the name of the ensemble
        """
        ensemble = self.interface.get_ensemble_name(index, namemode)
        self.logger.debug("Returning ensemble name for channel index=" + str(index) + ": " + str(ensemble))
        return ensemble

    def clear_database(self):
        """
        Clear the internal radio database. This probably clears the channel list and any presets...

        Raises OperationFailedError if the database couldn't be cleared
        """
        self.logger.info("Clearing internal radio database")
        if self.interface.clear_database() == False:
            self.logger.error("Clear database failed")
            raise OperationFailedError("Clear database failed")

    @property
    def bbeeq(self):
        """
        Returns the current bbeeq. Whatever that is.

        Returns BBEEQ object
        """
        bbe = self.interface.get_bbeeq()
        self.logger.debug("Returning BBEEQ: " + str(bbe))
        return bbe

    @bbeeq.setter
    def bbeeq(self, bbe):
        """
        Sets the bbeeq

        Keyword arguments:

        bbe: the BBEEQ object to set
        """
        self.logger.debug("Setting BBEEQ to: " + str(bbe))
        self.interface.set_bbeeq(bbe)

    @property
    def headroom(self):
        """
        Returns the current headroom
        """
        headroom = self.interface.get_headroom()
        self.logger.debug("Returning headroom: " + str(headroom))
        return headroom

    @headroom.setter
    def headroom(self, headroom):
        """
        Sets the headroom
        """
        self.logger.info("Setting headroom to: " + str(headroom))
        self.interface.set_headroom(headroom)

    @property
    def status(self):
        """
        Returns the current play status

        TODO: Work out what the values are
        """
        status =  self.interface.get_play_status()
        self.logger.debug("Returning play status: " + str(status))
        return status

    @property
    def data_rate(self):
        """
        Returns the current data rate (in kbs)
        """
        rate = self.interface.get_data_rate()
        self.logger.debug("Returning data rate for audio stream: " + str(rate) + "kbs")
        return rate

    @property
    def stereo(self):
        """
        Returns True if the stream is stereo
        """
        stereo = self.interface.get_stereo_mode() == 1
        self.logger.debug("Returning stereo mode: " + str(stereo))
        return stereo

    @stereo.setter
    def stereo(self, value):
        """
        Request a stereo stream

        Keyword arguments
        value: True for stereo, False for mono
        """
        self.logger.info("Setting stereo mode: " + str(value))
        if value == True:
            self.interface.set_stereo_mode(1)
        else:
            self.interface.set_stereo_mode(0)

    @property
    def signal_strength(self):
        """
        Returns the current signal strength (0-100)
        """
        strength = self.interface.get_signal_strength()
        self.logger.debug("Returning signal strength: " + str(strength))
        return strength

    @property
    def dab_signal_quality(self):
        """
        Returns the current DAB signal quality. Possibly in dB?

        TODO: Find out
        """
        dabquality = self.interface.get_dab_signal_quality()
        self.logger.debug("Returning dab signal quality: " + str(dabquality))
        return dabquality

    @property
    def programs(self):
        """
        Returns a list of Program objects

        Programs refer to actual stations
        """
        programs = self.interface.get_total_program()
        self.logger.debug("Returning " + str(programs) + " dab radio channels")
        objs = []
        if programs < MAX_DAB_CHANNELS:
            for i in range(0, programs):
                objs.append(Program(self, self.mode, i))
        else:
            self.logger.warning("Too many DAB channels: " + str(programs) + " > MAX_DAB_CHANNELS=" + str(MAX_DAB_CHANNELS))

        return objs
