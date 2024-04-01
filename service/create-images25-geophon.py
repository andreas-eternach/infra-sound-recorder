import sys
import gzip
import shutil
import numpy as np
import datetime
import os
import math
from matplotlib.figure import Figure
import matplotlib

class Stft(object):
    """Computes the short time fourier transform of a signal

    How to use:
    1.) Pass the signal into the class,
    2.) Call stft() to get the transformed data
    3.) Call freq_axis() and time_axis() to get the freq and time values for each index in the array

    """
    def __init__(self, data, fs, win_size, fft_size, overlap_fac=0.1):
        """Computes a bunch of information that will be used in all of the STFT functions"""
        self.data = np.array(data, dtype=np.float32)
        self.fs = np.int32(fs)
        self.win_size = np.int32(win_size)
        self.fft_size = np.int32(fft_size)
        self.overlap_fac = np.float32(1 - overlap_fac)

        self.hop_size = np.int32(np.floor(self.win_size * self.overlap_fac))
        self.pad_end_size = self.fft_size
        self.total_segments = np.int32(np.ceil(len(self.data) / np.float32(self.hop_size)))
        self.t_max = len(self.data) / np.float32(self.fs)

    # 0 db = 0.00002 Pa 0.02, 1
    def stft(self, scale='log', ref= 0.02, clip=None):
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
            # autopower = np.abs(spectrum * np.conj(spectrum))
            autopower = np.abs(np.divide(spectrum, self.win_size / 4))
            
            result[i, :] = autopower[: self.fft_size]
            result[i] = np.multiply(np.divide(result[i], 1.2), 0.707)

        print("Maximum in first sample: " + str(np.max(result[0])))
        # if scale == 'log':
        #    result = self.dB(result, ref)

        if clip is not None:
            np.clip(result, clip[0], clip[1], out=result)

        print(np.max(result[0]))
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

def createDbImage(data_values_buffer, y_caption):
    ft = Stft(data_values_buffer, 128, win_size=2500, fft_size=2500, overlap_fac=0.9)
    result = ft.stft(clip=(0, 60))
    x_ticks, x_tick_labels = create_ticks_optimum(ft.freq_axis(), num_ticks=30, resolution=5)
    y_ticks, y_tick_labels = create_ticks_optimum(ft.time_axis(), num_ticks=10, resolution=1)

    fig = Figure()
    fig.clear()
    ax = fig.add_subplot(111)

    img = ax.imshow(result, origin='lower', cmap='jet', interpolation='none', aspect='auto')
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)
    #ax.set_yticks(y_ticks)
    #ax.set_yticklabels(y_tick_labels)

    ax.set_xlabel('Frequency [Hz]')
    ax.set_ylabel(y_caption)

    fig.colorbar(img)
    fig.tight_layout()
    return fig

def writeDbImageForHour(hour, count, data_values_buffer, date_values_buffer, targetFolder):
    datetime_obj=datetime.datetime.fromtimestamp(date_values_buffer[0] / 1000)
    datetime_obj_to=datetime.datetime.fromtimestamp(date_values_buffer[count - 1] / 1000)
 
    dirname = targetFolder + str(datetime_obj.strftime('%Y%m%d'))
    if (not os.path.isdir(dirname)):
        os.mkdir(dirname)

    day = str(datetime_obj.strftime('%Y%m%d'))
    time = str(datetime_obj.strftime('%H%M%S'))

    fig = createDbImage(data_values_buffer[0:count - 1], str(datetime_obj.strftime('%d.%m.%Y %H:%M:%S')) + "(unten)-" + str(datetime_obj_to.strftime('%H:%M:%S') + "(oben)"))
    print(day + "_" + time + ".jpg")
    fig.savefig(dirname + "/" + "geophon_" + day + "_" + time + ".jpg", dpi=250)
 
def handleFileInternal(f_in, targetFolder):
    values = np.arange(0, int(3600 * 1.28 * 110), dtype=float)
    date_values = np.arange(0, int(3600 * 1.28 * 110), dtype=np.uint64)
    count = 0
    hour = -1
    #with gzip.open(fileName, 'rb') as f_in:
    while True:
     
        # Get next line from file
        line = f_in.readline()
     
        # if line is empty
        # end of file is reached
        if not line:
            break
        linestring = str(line, encoding="utf-8")
        # in case its a comment
        if (linestring.startswith('#')):
            continue
        next_value = float(linestring.split(";")[0])
        next_date_value = float(linestring.split(";")[1]) 
        # in case its the first data row
        if (hour < 0):
            hour = int(math.floor(next_date_value / 1000 / 3600))
        # in case we reached the next hour
        if (count == int(3600 * 1.28 * 110)):
            writeDbImageForHour(hour, count, values, date_values)
            hour = int(math.floor(next_date_value / 1000 / 3600))
            count = 0
        if (hour < int(math.floor(next_date_value / 1000 / 3600))):
            writeDbImageForHour(hour, count, values, date_values)
            hour = int(math.floor(next_date_value / 1000 / 3600))
            count = 0
        values[count] = next_value
        date_values[count] = next_date_value
        count += 1

    
    # handle remaining stuff
    if (count > 1000):
        writeDbImageForHour(hour, count, values, date_values, targetFolder)

def handleFile(fileName, targetFolder):
    with open(fileName, 'rb') as f_in:
        handleFileInternal(f_in, targetFolder)

def handleGzFile(fileName, targetFolder):
    with gzip.open(fileName, 'rb') as f_in:
        handleFileInternal(f_in, targetFolder)

os.nice(19)
matplotlib.rcParams.update({'font.size': 5})
#for file in os.listdir("/home/andreas/i2c/raspberry/i2c/data/"):
targetFolder = sys.argv[2]
for file in [sys.argv[1]]:
# for file in ["/home/andreas/i2c/raspberry/i2c/data/test/data.csv.gz"]:
    if (file.endswith(".csv.gz")):
        handleGzFile(file)
    elif (file.endswith(".csv")):
        handleFile(file, targetFolder)

