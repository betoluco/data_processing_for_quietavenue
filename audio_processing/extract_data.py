import datetime
import numpy
import scipy.io.wavfile as wavfile
import os

class ExtractData():
    def __init__(self, rec_datetime, utilities):
        """Extract information from audio files for its use in a sound chart
        
        Process audio files, segmenting them in samples of SAMPLE_SIZE_IN_SECONDS 
        (one minute) length. The maximum loudness is extracted and an MP3 file is
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
        
        
        #Global variables
        self.SAMPLE_SIZE_IN_SECONDS = 4 # 60 % SAMPLE_SIZE_IN_SECONDS = 0
        self.MIN_REPRESENTATION_UNIT = 60
        self.MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        
        self.rec_datetime = rec_datetime
        self.sound_loudness_limit = 3276
        self.data_point_list = []
        self.sound_array = numpy.array([], dtype=numpy.int16)
        self.sound_time_array = []
        
        #Execute the program
        self.utilities = utilities
        self.wav_files = utilities.sort_wave_files()
        self.sound_data_generator = utilities.get_sound_data(self.wav_files)
        self.run_through_data()
        
        
    def run_through_data(self):
        self.samplerate, data = self.sound_data_generator.__next__()
        sample_list = self.get_data_samples(data)
        
        while sample_list:
            for array in sample_list[:-1]:
                self.extract_sound(array)
                self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
                
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data)

    def extract_sound(self, array):
        
        if numpy.amax(array) > self.sound_loudness_limit:
            self.sound_time_array.append(self.rec_datetime)
            self.sound_array = numpy.append(self.sound_array, array)
            
        if self.sound_time_array:
            time_since_first_noise = (self.rec_datetime - self.sound_time_array[0]).total_seconds()
            if time_since_first_noise >= self.MIN_REPRESENTATION_UNIT:
                self.append_data_to_data_point_list()
            
        if (self.rec_datetime.time() == self.MIDNIGHT and self.sound_time_array):
            self.append_data_to_data_point_list()
    
    def append_data_to_data_point_list(self):
        mp3_name = datetime.datetime.strftime(self.sound_time_array[0], '%Y-%m-%d_%H-%M-%S') + '.mp3'
        mp3_link = self.utilities.create_mp3_audio_files(self.samplerate, self.sound_array, mp3_name)
        self.data_point_list.append({
            'time': self.sound_time_array[0].isoformat(),
            'maxLoudness': numpy.amax(self.sound_array),
            'mp3Link': mp3_link
        })
        self.sound_array = numpy.array([], dtype=numpy.int16)
        self.sound_time_array = []
            
    def get_data_samples(self, data):
        stop = len(data)
        sample_size = int(self.SAMPLE_SIZE_IN_SECONDS * self.samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    def append_data_to_sound_array(self, last_array):
        try:
            samplerate, data = self.sound_data_generator.__next__()
        except StopIteration:
            json_file = self.utilities.create_JSON(self.data_point_list)
            link_to_json_file = self.utilities.upload_file_to_bucket(json_file)
            self.utilities.upload_link_to_data_to_dynamodb(link_to_json_file)
            for file in self.wav_files:
                os.remove(file)
            os.remove(json_file)
            exit()
        
        data = numpy.append(last_array, data)
        return data
        
    
       
    