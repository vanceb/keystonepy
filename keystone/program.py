import logging
import os

from keystone.operation_failed_error import OperationFailedError

class Program(object):
    def __init__(self, radio, mode, index):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialised Program Class")
        self.radio = radio
        self.interface = radio.interface
        self.mode = mode
        self.index = index

    def play(self):
        self.logger.info("Playing channel " + str(self.index) + " " + str(self.name))
        if self.interface.play_stream(self.mode, self.index) != True:
            self.logger.error("Could not play stream: " + str(self.index) + " " + str(self.name))
            raise OperationFailedError("Could not play stream: " + str(self.index))

        self.radio.currently_playing = self

    def stop(self):
        self.logger.info("Stopping channel " + str(self.index) + " " + str(self.name))
        if self.interface.stop_stream() != True:
            self.logger.error("Could not stop stream: " + str(self.index) + " " + str(self.name))
            raise OperationFailedError("Could not stop stream: " + str(self.index))

        self.radio.currently_playing = None

    @property
    def name(self):
        """
        Returns the name of the program
        """
        prog = unicode(self.interface.get_program_name(self.mode, self.index, 1))
        self.logger.debug("Returning program name for index="+ str(self.index) + ": " + prog)
        return prog

    @property
    def type(self):
        """
        Returns the type of the program
        """
        progtype = self.interface.get_program_type(self.mode, self.index)
        self.logger.debug("Returning program type for index=" + str(self.index) + ": " + str(progtype))
        return progtype

    @property
    def text(self):
        """
        Returns the current DAB text. Often used for current song information
        """
        txt = self.interface.get_program_text()
        if txt is not None:
            txt = unicode(txt)
            self.logger.debug("Retuning currently playing text: " + txt)
        return txt

    @property
    def application_type(self):
        """
        Returns the programs application type
        """
        apptype = self.interface.get_application_type(self.index)
        self.logger.debug("Returning the application type for index=" + str(self.index) + ": " + str(apptype))
        return apptype

    @property
    def info(self):
        """
        Returns information about the program
        """
        info = unicode(self.interface.get_program_info(self.index))
        self.logger.debug("Returning info for index=" + str(self.index) + ": " + info)
        return info

    def mot_query(self):
        """
        Query Mot to get images and other interesting files
        Returns True if successful, False if not
        """
        motq = self.interface.mot_query()
        self.logger.debug("Querying for Mot files/images: " + str(motq))
        return motq

    def mot_reset(self, mode):
        """
        Resets the Mot state

        Keyword arguments:
        mode: MOT_HEADER_MODE or MOT_DIRECTORY_MODE
        """
        self.logger.info("Resetting Mot (files/images)")
        self.interface.mot_reset(mode)


    @property
    def image(self):
        """
        Returns the DAB image. This is an image blob that can be decoded using an appropriate library
        """
        self.logger.info("Getting an image from the radio")
        filename = self.interface.get_image()
        img = None
        f = open(filename, 'r')
        img = f.read()
        f.close()
        os.unlink(filename)
        return img

    @property
    def image_filename(self):
        """
        Returns a filename pointing at the current DAB image.
        The contents of this file will have an image that can be opened
        """
        filename = self.interface.get_image()
        self.logger.debug*"Returning image filename: " + str(filename)
        return filename
