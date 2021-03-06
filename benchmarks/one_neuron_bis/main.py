from logging import DEBUG
import os

import circusort
import utils


# Parameters

host = '127.0.0.1'  # i.e. run the test locally

cell_obj = {'r': 'r_ref'}
cells_args = [cell_obj]
cells_params = {'r_ref': 1.0}  # firing rate [Hz]

tmp_dir = os.path.join('/', 'tmp', 'spyking_circus_ort', 'one_neuron_bis')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)
hdf5_path = os.path.join(tmp_dir, 'synthetic.h5')
probe_path = os.path.join('..', 'mea_16.prb')
data_path = os.path.join(tmp_dir, 'data.raw')
mad_path = os.path.join(tmp_dir, 'mad.raw')
peak_path = os.path.join(tmp_dir, 'peaks.raw')


# Define the elements of the Circus network.

director = circusort.create_director(host=host)

manager = director.create_manager(host=host)

generator = manager.create_block('synthetic_generator',
                                 cells_args=cells_args,
                                 cells_params=cells_params,
                                 hdf5_path=hdf5_path,
                                 probe=probe_path,
                                 log_level=DEBUG)
filtering = manager.create_block('filter',
                                 cut_off=100.0,
                                 log_level=DEBUG)
# whitening = manager.create_block('whitening',
#                                  log_level=DEBUG)
signal_writer = manager.create_block('writer',
                                     data_path=data_path,
                                     log_level=DEBUG)
mad_estimator = manager.create_block('mad_estimator',
                                     log_level=DEBUG)
mad_writer = manager.create_block('writer',
                                  data_path=mad_path,
                                  log_level=DEBUG)
peak_detector = manager.create_block('peak_detector',
                                     threshold_factor=7.0,  # 5.710,
                                     log_level=DEBUG)
peak_writer = manager.create_block('peak_writer',
                                   neg_peaks=peak_path,
                                   log_level=DEBUG)


# Initialize the elements of the Circus network.

director.initialize()


# Connect the elements of the Circus network.

director.connect(generator.output, filtering.input)
# director.connect(filtering.output, whitening.input)
# director.connect(whitening.output, [mad_estimator.input,
#                                     peak_detector.get_input('data')])
director.connect(filtering.output, [mad_estimator.input,
                                    peak_detector.get_input('data'),
                                    signal_writer.input])
director.connect(mad_estimator.output, [peak_detector.get_input('mads'),
                                        mad_writer.input])
director.connect(peak_detector.get_output('peaks'), peak_writer.input)

# Launch the Circus network.

director.start()
director.sleep(duration=20.0)
director.stop()
# director.join()


# Analyze the results.

ans = utils.Results(generator, signal_writer, mad_writer, peak_writer, probe_path)
