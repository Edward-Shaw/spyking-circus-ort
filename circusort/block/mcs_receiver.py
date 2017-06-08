import errno
import numpy as np
import Queue
import socket
import threading

from .block import Block



class Mcs_receiver(Block):
    '''TODO add docstring'''

    name = "Mcs_receiver"

    params = {
        'dtype'        : 'uint16',
        'nb_channels'  : 261,
        # 'nb_samples'   : 1024,
        'nb_samples'   : 2000,
        # 'sampling_rate': 20000,
    }


    def __init__(self, **kwargs):

        Block.__init__(self, **kwargs)
        self.add_output('data')


    def _initialize(self):
        '''TODO add docstring.'''

        self.output.configure(dtype=self.dtype, shape=(self.nb_channels, self.nb_samples))

        self.queue = Queue.Queue()
        self.size = 261 * 2000 * 2 # i.e. nb_chan * nb_step * size(uint16)

        def recv_target(queue, size, host, port):
            # Define the address of the input socket.
            address = (host, port)
            # Bind an input socket.
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Create a connection to this address.
            s.connect(address)
            # Receive data.
            while True:
                try:
                    recv_string = s.recv(size, socket.MSG_WAITALL)
                except socket.error as e:
                    if e.errno == errno.ECONNRESET:
                        # Discard error message.
                        break
                    else:
                        raise e
                queue.put(recv_string)

        # Prepare background thread for data acquisition.
        args = (self.queue, self.size, self.transmitter_host, self.transmitter_port)
        self.recv_thread = threading.Thread(target=recv_target, args=args)
        self.recv_thread.deamon = True

        # Launch background thread for data acquisition.
        self.log.info("Launch background thread for data acquisition...")
        self.recv_thread.start()

        return


    def _process(self):
        '''TODO add docstring.'''

        recv_string = self.queue.get()

        nb_recv_chan = 261
        recv_dtype = 'uint16'
        recv_shape = (-1, nb_recv_chan)
        recv_data = np.fromstring(recv_string, dtype=recv_dtype)
        recv_data = np.reshape(recv_data, recv_shape)
        recv_data = np.transpose(recv_data)

        self.output.send(recv_data)

        return