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
        self.NOISE_THRESHOLD = 0.43 #43% threshold for noise
        self.SECONDS_IN_A_DAY = 24 * 60 *60
        self.NUMPY_ARRAY_INT16_MAX_VALUE = numpy.iinfo(numpy.array([], dtype=numpy.int16).dtype).max
        self.audio_data = {}
        self.helpers = helpers
        self.extract_data(rec_datetime)
    
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
    def extract_data(self, current_time):
        self.current_day = current_time.replace(hour=0, minute=0, second=0)
        day_duration_in_sec = (self.current_day - current_time).seconds
        sound_data_array = numpy.array([], dtype=numpy.int16)
        sound_data_generator = self.get_sound_data()
        for self.samplerate, data in sound_data_generator:
            sound_data_array = numpy.concatenate((sound_data_array, data))
            if sound_data_array.size > day_duration_in_sec * self.samplerate:
                day_data_array = self.array_split(sound_data_array, day_duration_in_sec)
                self.analize_data(day_data_array[0], current_time)
                sound_data_array = numpy.array([], dtype=numpy.int16)
                sound_data_array = numpy.append(sound_data_array, day_data_array[1])
                day_duration_in_sec = self.SECONDS_IN_A_DAY # The consecutive day after the first have the same duration or the generator finishes
                current_time = self.current_day = self.current_day + timedelta(hours=24)
        
        self.analize_data(sound_data_array, current_time)
        self.helpers.create_JSON(self.audio_data)
    
    def analize_data(self, data_array, start_time):
        sound_data_array = numpy.array([], dtype=numpy.int16)
        graph_data_points_array = []
        data_samples_list = self.array_split(data_array, self.SAMPLE_SIZE_IN_SECONDS)
        for data_sample in data_samples_list:
            parts_list = self.array_split(data_sample, self.SAMPLE_SPLIT_SIZE_IN_SECONDS)
            parts_max_loudness_list, part_audio_data_array = self.filter_sample_audio_data(parts_list)
            
            data_point = {
                'maxLoudness': float(numpy.mean(parts_max_loudness_list)/self.NUMPY_ARRAY_INT16_MAX_VALUE),
                'time': start_time.isoformat()
            }
            if part_audio_data_array.size != 0:
                data_point['soundStart'] = sound_data_array.size/self.samplerate
            
            sound_data_array = numpy.append(sound_data_array, part_audio_data_array)
            graph_data_points_array.append(data_point)
            start_time += timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
        self.store_data(sound_data_array, graph_data_points_array)
    
    def filter_sample_audio_data(self, parts):
        sound_data_concentration_array = numpy.array([], dtype=numpy.int16)
        max_list = []
        for part in parts:
            part_max = numpy.amax(part)
            max_list.append(part_max)
            if (part_max > self.NOISE_THRESHOLD * self.NUMPY_ARRAY_INT16_MAX_VALUE):
                sound_data_concentration_array = numpy.append(sound_data_concentration_array, part)
        return max_list, sound_data_concentration_array
    
    def store_data(self, audio_data_array, graph_data_points_array):
        mp3_name = datetime.strftime(self.current_day, '%Y-%m-%d') + '.mp3'
        mp3_link = self.helpers.create_mp3_audio_files(self.samplerate, audio_data_array, mp3_name)
        self.audio_data[self.current_day.isoformat()] = {'mp3Link': mp3_link}
        self.audio_data[self.current_day.isoformat()]['graphData'] = graph_data_points_array.copy()
    
    def array_split(self, data, split_size_in_seconds):
        split_size = int(split_size_in_seconds * self.samplerate)
        return numpy.array_split(data, range(split_size, len(data), split_size))