from .block import Block
import tempfile
import os
import numpy


class Spike_writer(Block):
    """Spike writer block.

    Attributes:
        spike_times: string
            Path to the location where spike times will be saved.
        amplitudes: string
            Path to the location where spike amplitudes will be saved.
        templates: string
            Path to the location where spike templates will be saved.
        rejected_times: string
            Path to the location where rejected times will be saved.
        rejected_amplitudes: string
            Path to the location where rejected amplitudes will be saved.
        directory: string
            Path to the location where spike attributes will be saved.

    """
    # TODO complete docstring.

    name = "Spike writer"

    params = {
        'spike_times': None,
        'amplitudes': None,
        'templates': None,
        'rejected_times': None,
        'rejected_amplitudes': None,
        'directory': None,
    }

    def __init__(self, **kwargs):

        Block.__init__(self, **kwargs)
        self.add_input('spikes')

    def _get_temp_file(self, basename=None):

        if self.directory is None:
            tmp_dir = tempfile.gettempdir()
        else:
            tmp_dir = self.directory
        if basename is None:
            tmp_file = tempfile.NamedTemporaryFile()
            tmp_basename = os.path.basename(tmp_file.name)
            tmp_file.close()
        else:
            tmp_basename = basename
        tmp_filename = tmp_basename + ".raw"
        data_path = os.path.join(tmp_dir, tmp_filename)

        return data_path

    def _initialize(self):

        self.recorded_data = {}
        self.data_file = {}

        self._initialize_data_file('spike_times', self.spike_times)
        self._initialize_data_file('amplitudes', self.amplitudes)
        self._initialize_data_file('templates', self.templates)
        self._initialize_data_file('rejected_times', self.rejected_times)
        self._initialize_data_file('rejected_amplitudes', self.rejected_amplitudes)

        return

    def _initialize_data_file(self, key, path):
        # TODO add docstring.

        if path is None:
            self.recorded_data[key] = self._get_temp_file(basename=key)
        else:
            self.recorded_data[key] = path
        self.log.info('{n} records {m} into {k}'.format(n=self.name, m=key, k=self.recorded_data[key]))
        self.data_file[key] = open(self.recorded_data[key], mode='wb')

        return

    def _process(self):

        batch = self.input.receive()

        if self.input.structure == 'array':
            self.log.error('{n} can only write spike dictionaries'.format(n=self.name))
        elif self.input.structure == 'dict':
            offset = batch.pop('offset')
            for key in batch:
                if key in ['spike_times']:
                    to_write = numpy.array(batch[key]).astype(numpy.int32)
                    to_write += offset
                elif key in ['templates']:
                    to_write = numpy.array(batch[key]).astype(numpy.int32)
                elif key in ['amplitudes']:
                    to_write = numpy.array(batch[key]).astype(numpy.float32)
                elif key in ['rejected_times']:
                    to_write = numpy.array(batch[key]).astype(numpy.int32)
                    to_write += offset
                elif key in ['rejected_amplitudes']:
                    to_write = numpy.array(batch[key]).astype(numpy.float32)
                else:
                    raise KeyError(key)
                self.data_file[key].write(to_write)
                self.data_file[key].flush()
        else:
            self.log.error("{n} can't write {s}".format(n=self.name, s=self.input.structure))

        return

    def __del__(self):

        for file in self.data_file.values():
            file.close()
