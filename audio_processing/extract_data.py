import datetime
import numpy
import os
import scipy.io.wavfile as wavfile

class ExtractData():
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
        
        self.SAMPLE_SIZE_IN_SECONDS = 4 
        self.NOISE_THRESHOLD = numpy.iinfo(self.sound_array.dtype).max * 0.5 #50% threshold for noise
        self.GRAPH_THRESHOLD = numpy.iinfo(self.sound_array.dtype).max * 0.1 #10% threshold for the graph
        self.rec_datetime = rec_datetime
        self.graph_data = []
        self.audio_data = numpy.array([], dtype=numpy.int16)
        self.helpers = helpers
      
    
    
        
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
    def run_through_data(self):
        last_sample = numpy.array([], dtype=numpy.int16)
        sound_data_generator = self.get_sound_data()
        for samplerate, data in sound_data_generator:
            concatenated_data = numpy.concatenate((last_sample, data), axis=None)
            sample_list = self.get_data_samples(samplerate, concatenated_data)
            last_sample = sample_list[-1]
            self.process_data_samples(sample_list)
        
        self.helpers.create_JSON(self.graph_data)
        self.helpers.remove_wav_files()
    
    def get_data_samples(self, samplerate, data):
        stop = len(data)
        sample_size = int(self.SAMPLE_SIZE_IN_SECONDS * samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    
    
    
    # Process samples to extract data
    def process_data_samples(self, recording_data):
        for recording_data in recording_data_list[:-1]:
            if numpy.amax(recording_data) > self.NOISE_THRESHOLD:
                self.audio_data = numpy.append(self.audio_data, recording_data)
        
            self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
            if self.rec_datetime >= self.day + datetime.timedelta(days=1):
                mp3_name = datetime.datetime.strftime(self.day, '%Y-%m-%d') + '.mp3'
                mp3_link = self.utilities.create_mp3_audio_files(self.samplerate, self.sound_array, mp3_name)
                
                self.day = self.rec_datetime.replace(hour=0, minute=0, second=0)
                self.reset_array()
    
   
            
    def filter_data_points(self):
        daily_data = self.graph_data[self.day.isoformat()] = []
        for i, point in enumerate(self.data_points):
            if( point['maxLoudness'] > self.GRAPH_THRESHOLD ):
                if(self.data_points[i-1]['maxLoudness'] < self.GRAPH_THRESHOLD and i > 0):
                    daily_data.append({
                        'time': self.data_points[i-1]['time'],
                        'maxLoudness':0
                    })
                    
                daily_data.append(point)
                
                if(self.data_points[i+1]['maxLoudness'] < self.GRAPH_THRESHOLD and i < len(self.data_points)):
                    daily_data.append({
                        'time': self.data_points[i+1]['time'],
                        'maxLoudness':0
                    })
           
        
    