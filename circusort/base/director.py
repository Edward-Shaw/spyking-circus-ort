import time
import logging

from .logger import Logger
from . import utils

# from circusort.base.process import Process
from circusort.base.process import create_process



class Director(object):

    def __init__(self, name=None, log_level=logging.INFO):

        # Start logging server
        self.name = name or "Director"
        self.log_level = log_level
        self.logger = Logger()
        # Get logger instance
        self.log = utils.get_log(self.logger.address, name=__name__, log_level=self.log_level)

        self.interface = utils.find_ethernet_interface()

        self.log.info("start director {d}".format(d=str(self)))
        
        self.managers = {}

    def __del__(self):
        self.log.info("stop director {d}".format(d=str(self)))

    @property
    def nb_managers(self):
        return len(self.managers)

    def get_logger(self):
        return self.logger

    def create_manager(self, name=None, host=None, log_level=None):
        '''Create a new manager process and return a proxy to this process.

        A manager is a process that manages workers.
        '''
        if name is None:
            manager_id = 1 + self.nb_managers
            name = "Manager_{}".format(manager_id)

        self.log.debug("{d} creates new manager {m}".format(d=str(self), m=name))

        process = create_process(host=host, log_address=self.logger.address, name=name)
        module = process.get_module('circusort.block.manager')
        log_level = log_level or self.log_level
        manager = module.Manager(name=name, log_address=self.logger.address, log_level=log_level, host=host)

        self.register_manager(manager)

        return manager

    def register_manager(self, manager):
        
        #self.managers.update({name: manager})
        self.log.debug("{d} registers {m}".format(d=str(self), m=manager.name))
        return

    def initialize_all(self):
        for manager in self.managers.itervalues():
            manager.initialize_all()
        return

    def start_all(self):
        for manager in self.managers.itervalues():
            manager.start_all()
        return

    def sleep(self, duration=None):
        self.log.debug("{d} sleeps {k} sec".format(d=str(self), k=duration))
        time.sleep(duration)
        return

    def stop_all(self):
        for manager in self.managers.itervalues():
            manager.stop_all()
        return

    def destroy_all(self):
        return

    def __str__(self):
        return "{d}[{i}]".format(d=self.name, i=self.interface)

    def list_managers(self):
        return self.managers.keys()

    def get_manager(self, key):
        assert key in self.list_managers(), "%s is not a valid manager" %key
        return self.managers[key]
