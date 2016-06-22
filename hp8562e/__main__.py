import serial
import numpy as np


class hp8562e(object):
    """Handles communication with the HP8562e spectrum analyzer via a
    PROLOGIX GPIB to USB convertor.

    All commands starting with a ++ talk to the controller and not the
    spectrum analyzer.
    """
    def __init__(self, address):
        super(hp8562e, self).__init__()
        self.address = address
        baudrate = 57600  # baudrate does not matter for PROLOGIX controller
        timeout = 2

        self.device = serial.Serial(self.address, baudrate=baudrate,
                                    timeout=timeout)
        self.device.flush()

        # PROLOGIX: disable read after write
        self.device.write('++auto 0\r\n')

        # switch to single sweep mode
        self.device.write('SNGLS\r\n')

    def get_trace_parameters(self):
        command_string = "FA?;FB?;RL?;RB?;VB?;ST?;LG?;AUNITS?;\r\n"
        # command_string = "FA?;\r\n"
        self.device.write(command_string)
        read_list = [self.readline() for i in range(command_string.count('?'))]
        float_parms = ['start_frequency', 'stop_frequency', 'reference_level',
                       'resolution_bandwidth', 'view_bandwidth', 'sweep_time',
                       'log_scale']

        trace_info = {}
        for i, f in enumerate(float_parms):
            trace_info[f] = float(read_list[i])
        trace_info['units'] = read_list[7].split('\n')[0]
        return trace_info

    def get_trace_data(self):
        """Get data in measuremnt units.

        faster, but need to convert to real units.
        Use the convenience function get_xy to get both frequency and power
        arrays."""
        self.device.write('TS; TDF M;TRA?\r\n')
        data_string = self.readline()
        data = np.fromstring(data_string, dtype='float', sep=',')
        return data

    def get_xy(self):
        trace_info = self.get_trace_parameters()
        y_raw = self.get_trace_data()

        fa = trace_info['start_frequency']
        fb = trace_info['stop_frequency']
        N = len(y_raw)

        freq = fa + (fb-fa)/N * np.arange(N)
        power = (trace_info['reference_level'] +
                 (y_raw - 600.)/60.*trace_info['log_scale'])
        return (freq, power)

    def readline(self):
        self.device.write('++read eoi\r\n')
        read_string = self.device.readline()
        return read_string

    def set_trace_parameters(self, start_freq, stop_frequency, rbw):
        """Set basic trace parameters.

        If you need to change other parameters, switch the spectrum analyzer
        to local control to change them."""
        write_string = 'FA {0:d}; FB {1:d}\r\n; RB {2:d}'.format(start_freq,
                       stop_frequency, rbw)
        print(write_string)
        self.device.write(write_string)


    def close(self):
        """Close connection to GPIB controller."""
        # Switch spectrum analyzer to continuous mode
        self.device.write('CONTS\r\n')
        self.device.close()

