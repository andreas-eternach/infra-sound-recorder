import sys
import gzip
import shutil
import numpy as np
import datetime
import os
import math
from matplotlib.figure import Figure
import matplotlib

class FrequencyImageGenerator(object):
    """Computes the short time fourier transform of a signal

    How to use:
    1.) Pass the signal into the class,
    2.) Call stft() to get the transformed data
    3.) Call freq_axis() and time_axis() to get the freq and time values for each index in the array

    """
    def __init__(self, data, startTimeAsEpoch, endTimeAsEpoch, fs, win_size, fft_size, overlap_fac=0.1):
        """Computes a bunch of information that will be used in all of the STFT functions"""
        self.data = np.array(data, dtype=np.float32)
        self.startTimeAsEpoch = startTimeAsEpoch
        self.endTimeAsEpoch = endTimeAsEpoch
        self.fs = np.int32(fs)
        self.win_size = np.int32(win_size)
        self.fft_size = np.int32(fft_size)
        self.overlap_fac = np.float32(1 - overlap_fac)

        self.hop_size = np.int32(np.floor(self.win_size * self.overlap_fac))
        self.pad_end_size = self.fft_size
        self.total_segments = np.int32(np.ceil(len(self.data) / np.float32(self.hop_size)))
        self.t_max = len(self.data) / np.float32(self.fs)

    # 0 db = 0.00002 Pa 0.02, 1
    def stft(self, scale='lin', ref= 0.02, clip=None):
        """Perform the STFT and return the result"""

        # Todo: changing the overlap factor doens't seem to preserve energy, need to fix this
        # window = np.hanning(self.win_size) * self.overlap_fac * 2
        window = np.hanning(self.win_size)
        inner_pad = np.zeros((self.fft_size * 2) - self.win_size)

        proc = np.concatenate((self.data, np.zeros(self.pad_end_size)))
        result = np.empty((self.total_segments, int(self.fft_size)), dtype=np.float32)

        for i in range(self.total_segments):
            current_hop = self.hop_size * i
            segment = proc[current_hop:current_hop+self.win_size]
            windowed = segment * window
            padded = np.append(windowed, inner_pad)
            spectrum = np.fft.fft(padded)
            # half for hanning, other half for ???
            autopower = np.abs(np.divide(spectrum, self.win_size / 4))
            
            result[i, :] = autopower[: self.fft_size]

        # print("Maximum in first sample: " + str(np.max(result[0])))
        if scale == 'log':
            result = self.dB(result, ref)

        if clip is not None:
            np.clip(result, clip[0], clip[1], out=result)

        # print(np.max(result[0]))
        return result

    def dB(self, data, ref):
        """Return the dB equivelant of the input data"""
        return 20*np.log10(data / ref)

    def freq_axis(self):
        """Returns a list of frequencies which correspond to the bins in the returned data from stft()"""
        return np.arange(self.fft_size) / np.float32(self.fft_size * 2) * self.fs

    def time_axis(self):
        """Returns a list of times which correspond to the bins in the returned data from stft()"""
        return np.arange(self.total_segments) / np.float32(self.total_segments) * self.t_max

    def create_ticks_optimum(axis, num_ticks, resolution, return_errors=False):
        """ Try to divide <num_ticks> ticks evenly across the axis, keeping ticks to the nearest <resolution>"""
        max_val = axis[-1]
        hop_size = max_val / np.float32(num_ticks)

        indicies = []
        ideal_vals = []
        errors = []

        for i in range(num_ticks):
            current_hop = resolution * round(float(i*hop_size)/resolution)
            index = np.abs(axis-current_hop).argmin()

            indicies.append(index)
            ideal_vals.append(current_hop)
            errors.append(np.abs(current_hop - axis[index]))

        if return_errors:
            return indicies, ideal_vals, errors
        else:
            return indicies, ideal_vals
        
    def freq_axis(self):
        """Returns a list of frequencies which correspond to the bins in the returned data from stft()"""
        return np.arange(self.fft_size) / np.float32(self.fft_size * 2) * self.fs

    def create_ticks_optimum(self, axis, num_ticks, resolution, return_errors=False):
        """ Try to divide <num_ticks> ticks evenly across the axis, keeping ticks to the nearest <resolution>"""
        max_val = axis[-1]
        hop_size = max_val / np.float32(num_ticks)

        indicies = []
        ideal_vals = []
        errors = []

        for i in range(num_ticks):
            current_hop = resolution * round(float(i*hop_size)/resolution)
            index = np.abs(axis-current_hop).argmin()

            indicies.append(index)
            ideal_vals.append(current_hop)
            errors.append(np.abs(current_hop - axis[index]))

        if return_errors:
            return indicies, ideal_vals, errors
        else:
            return indicies, ideal_vals

    def createTimeCaption(self):
        startTime = datetime.datetime.fromtimestamp(self.startTimeAsEpoch / 1000)
        endTime = datetime.datetime.fromtimestamp(self.endTimeAsEpoch / 1000)
        return str(startTime.strftime('%d.%m.%Y %H:%M:%S')) + "(unten)-" + str(endTime.strftime('%H:%M:%S') + "(oben)")

    def createFrequencyImage(self):
        result = self.stft(clip=(0, 60))
        x_ticks, x_tick_labels = self.create_ticks_optimum(self.freq_axis(), 30, 5)

        fig = Figure()
        fig.clear()
        ax = fig.add_subplot(111)

        img = ax.imshow(result, origin='lower', cmap='jet', interpolation='none', aspect='auto')
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_tick_labels)

        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel(self.createTimeCaption())

        fig.colorbar(img)
        fig.tight_layout()
        return fig

