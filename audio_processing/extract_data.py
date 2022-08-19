import datetime
import numpy
import os

class ExtractData():
    def __init__(self, rec_datetime, utilities):
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
        
        
        #Global variables
        self.SAMPLE_SIZE_IN_SECONDS = 4 # 60 % SAMPLE_SIZE_IN_SECONDS = 0
        self.rec_datetime = rec_datetime
        self.sound_array = numpy.array([], dtype=numpy.int16)
        self.NOISE_THRESHOLD = numpy.iinfo(self.sound_array.dtype).max * 0.5 #50% threshold for noise
        self.GRAPH_THRESHOLD = numpy.iinfo(self.sound_array.dtype).max * 0.1 #10% threshold for the graph
        self.day = self.rec_datetime.replace(hour=0, minute=0, second=0)
        
        self.data_points = []
        self.graph_data = {}
        
        #Execute the program
        self.utilities = utilities
        self.wav_files = utilities.sort_wave_files()
        self.recodrings_data_generator = utilities.get_sound_data(self.wav_files)
        self.run_through_data()
        
    # Extract Samples
    def run_through_data(self):
        self.samplerate, data = self.recodrings_data_generator.__next__()
        sample_list = self.get_data_samples(data)
        
        while sample_list:
            for array in sample_list[:-1]:
                self.process_data_samples(array)
                
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data)
    
    def get_data_samples(self, data):
        stop = len(data)
        sample_size = int(self.SAMPLE_SIZE_IN_SECONDS * self.samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    def append_data_to_sound_array(self, last_sample):
        try:
            samplerate, data = self.recodrings_data_generator.__next__()
            data = numpy.append(last_sample, data)
            return data
        except StopIteration:
            json_file = self.utilities.create_JSON(self.graph_data)
            link_to_json_file = self.utilities.upload_file_to_bucket(json_file)
            self.utilities.upload_link_to_data_to_dynamodb(link_to_json_file)
            self.utilities.remove_wav_files(json_file)
            exit()
    
    # Process samples to extract data
    def process_data_samples(self, recording_data):
        self.data_points.append({
            'time': self.rec_datetime.isoformat(),
            'maxLoudness': numpy.amax(recording_data).item()
        })
        
        if numpy.amax(recording_data) > self.NOISE_THRESHOLD:
            self.sound_array = numpy.append(self.sound_array, recording_data)
        
        self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
        if self.rec_datetime >= self.day + datetime.timedelta(days=1):
            mp3_name = datetime.datetime.strftime(self.day, '%Y-%m-%d') + '.mp3'
            mp3_link = self.utilities.create_mp3_audio_files(self.samplerate, self.sound_array, mp3_name)
            self.filter_data_points()
            self.day = self.rec_datetime.replace(hour=0, minute=0, second=0)
            self.reset_array()
    
    def reset_array(self):
        self.sound_array = numpy.array([], dtype=numpy.int16)
        self.data_points = []
            
    def filter_data_points(self):
        daily_data = self.graph_data[self.day.isoformat()] = []
        for i, point in enumerate(self.data_points):
            try:
                if( 
                    point['maxLoudness'] > self.GRAPH_THRESHOLD or
                    self.data_points[i-2]['maxLoudness'] > self.GRAPH_THRESHOLD or
                    self.data_points[i-1]['maxLoudness'] > self.GRAPH_THRESHOLD or
                    self.data_points[i+1]['maxLoudness'] > self.GRAPH_THRESHOLD or
                    self.data_points[i+2]['maxLoudness'] > self.GRAPH_THRESHOLD
                ):
                    daily_data.append(point)
            except: 
                daily_data.append(point)
    