from datetime import datetime, timedelta
import numpy
import os
import scipy.io.wavfile as wavfile

class extractData():
    def __init__(self, rec_datetime, helpers):
        """Extract information from audio files for its use in a sound chart
        
        Process audio files, segmenting them in samples of SAMPLE_SIZE_IN_SECONDS 
        length. The maximum loudness is extracted and an MP3 file is
        generated and stored in the S3 quietavenue.com bucket from each of the segments.
        The maximum loudness, a link to the mp3 file, and the date and time in ISO 8601
        format of the sample, are appended in a list (data_point_list). Once all the audio
        files have been processed, the maximum loudness is normalized to a 0-1 range by
        dividing all the loudnees values in the list by the maximum loudnees value of all 
        the processed segments. 
        
        The list is converted to a json file and stored in the quietavenue.com bucket
        and a link to the json file is stored in DynamoDB.
        
        While processing the audio files a second list is created were the days of the recordings
        are appended in ISO 8601 format to it.
        """
        
        self.SAMPLE_SIZE_IN_SECONDS = 300
        self.SAMPLE_SPLIT_SIZE_IN_SECONDS = 3
        self.NOISE_THRESHOLD = 0.43 #50% threshold for noise
        self.rec_datetime = rec_datetime
        self.day = self.rec_datetime.replace(hour=0, minute=0, second=0)
        self.daily_sound_data = numpy.array([], dtype=numpy.int16)
        self.audio_data = {}
        self.daily_graph_data = []
        self.last_sample = numpy.array([], dtype=numpy.int16)
        self.data_max_value = numpy.iinfo(self.last_sample.dtype).max
        self.helpers = helpers
        self.samplerate = 14400
        self.sound_start_in_seconds = 0
    
    def get_sound_data(self):
        wav_files = self.sort_wave_files()
        for file in wav_files:
            print(file)
            yield wavfile.read(file)
            
    def sort_wave_files(self):
        wav_files = []
        for file in os.listdir():
            if file.endswith(('.WAV', '.wav')):
                wav_files.append(file)
        wav_files.sort()
        return wav_files
        
    # Extract Samples
    def extract_data(self):
        sound_data_generator = self.get_sound_data()
        
        for self.samplerate, data in sound_data_generator:
            concatenated_data = numpy.concatenate((self.last_sample, data), axis=None)
            data_sample_list = self.array_split(concatenated_data, self.SAMPLE_SIZE_IN_SECONDS)
            last_samples = data_sample_list[-1]
            for data_sample in data_sample_list[:-1]:
                self.rec_datetime += timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
                self.organize_data_by_day(data_sample)
        
        self.store_data()
        self.helpers.create_JSON(self.audio_data)
        
    def organize_data_by_day(self, data_sample):
        if self.rec_datetime > self.day + timedelta(days=1):
            self.store_data()
        data_point = {
            'time': self.rec_datetime.isoformat()
        }
        self.analize_data(data_sample, data_point)
        self.daily_graph_data.append(data_point)
    
    def store_data(self):
        mp3_name = datetime.strftime(self.day, '%Y-%m-%d') + '.mp3'
        mp3_link = self.helpers.create_mp3_audio_files(self.samplerate, self.daily_sound_data, mp3_name)
        self.audio_data[self.day.isoformat()] = {'mp3Link': mp3_link}
        self.audio_data[self.day.isoformat()]['graphData'] = self.daily_graph_data.copy()
        self.daily_graph_data.clear()
        self.daily_sound_data = numpy.array([], dtype=numpy.int16)
        self.day = self.rec_datetime.replace(hour=0, minute=0, second=0)
        self.sound_start_in_seconds = 0
            
    def analize_data(self, data_sample, data_point):
        parts = self.array_split(data_sample, self.SAMPLE_SPLIT_SIZE_IN_SECONDS)
        maximum = numpy.amax(parts,axis=1)
        data_point['maxLoudness'] = float(numpy.mean(maximum)/self.data_max_value)
        self.get_sounds_from_samples(parts, data_point)
        
    def get_sounds_from_samples(self, parts, data_point):
        sound_duration_in_seconds =  0
        for part in parts:
            if (numpy.amax(part) > self.NOISE_THRESHOLD * self.data_max_value):
                sound_duration_in_seconds += self.SAMPLE_SPLIT_SIZE_IN_SECONDS
                self.daily_sound_data = numpy.append(self.daily_sound_data, part)
        if sound_duration_in_seconds:
            data_point['soundStart'] = self.sound_start_in_seconds
            data_point['soundEnd'] = self.sound_start_in_seconds + sound_duration_in_seconds
            self.sound_start_in_seconds += sound_duration_in_seconds
        
    def array_split(self, data, split_size_in_seconds):
        split_size = int(split_size_in_seconds * self.samplerate)
        return numpy.array_split(data, range(split_size, len(data), split_size))
