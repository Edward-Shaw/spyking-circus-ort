# Test to measure the computational efficiency of two operations in one block
# associated to one manager.

import circusort
import settings
import logging


host = '127.0.0.1' # to run the test locally
# host = settings.host # to run the test remotely

size = 2 # square root of number of electrodes (for buffer)
nb_samples = 100 # number of time samples (for buffer)
data_type = 'float32' # data type (for buffer)
nb_buffer = 1000 # number of buffers to process


# TODO for each trial
    # TODO create director

interface = circusort.utils.find_interface_address_towards(host)
director = circusort.create_director(interface=interface, log_level=logging.INFO)
    # TODO create manager
manager = director.create_manager(host=host, log_level=logging.INFO)
    # TODO create block with read & send operations

reader = manager.create_block('reader', log_level=logging.INFO, size=size, nb_samples=nb_samples, dtype=data_type, force=True)
    # TODO create block with two operations (serial composition)
computer = manager.create_block('computer_1_2')
    # TODO create block with receive & write operations
writer = manager.create_block('writer')

    # TODO initialize blocks

manager.initialize()
#reader.initialize()
#computer.initialize()
#writer.initialize()
    # TODO connect blocks
manager.connect(reader.output, computer.input)

manager.connect(computer.output, writer.input)
    # TODO connect block again
    # TODO start blocks

manager.start()

    # TODO wait blocks stop
manager.join()

    # TODO retrieve computational time
t_comp = writer.t_comp
# TODO save computational times to file
director.sleep(duration=1.0)
print("computational time: {} s".format(t_comp))