import boto3
import datetime
import json
import numpy
import scipy.io.wavfile as wavfile
import os
import subprocess

class ExtractData():
    def __init__(self, destination_bucket_folder, rec_datetime, dynamodb_item_key):
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
        self.SAMPLE_SIZE_IN_SECONDS = 5 # 60 % SAMPLE_SIZE_IN_SECONDS = 0
        self.SOUND_LOUDNESS_PERCENTAGE_LIMIT = 0.1
        self.MAX_SILENCE_DURATION_IN_SECONDS = 60
        self.MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        self.prefix = destination_bucket_folder
        self.rec_datetime = rec_datetime
        self.dynamodb_item_key = dynamodb_item_key
        self.sound_loudness_limit = 0
        self.data_max_loudness = 0
        self.wav_files = []
        self.data_point_list = []
        self.sound_array = numpy.array([], dtype=numpy.int16)
        self.sound_time_array = []
        #Execute the program
        self.sort_wave_files()
        self.sound_data_generator = self.get_sound_data()
        self.run_through_data()
        
    def sort_wave_files(self):
        for file in os.listdir():
            if file.endswith('.wav'):
                self.get_data_max_loudness(file)
                self.wav_files.append(file)
        self.wav_files.sort()
        self.sound_loudness_limit = self.data_max_loudness * self.SOUND_LOUDNESS_PERCENTAGE_LIMIT

    def get_data_max_loudness(self, file):
        self.samplerate, data = wavfile.read(file)
        max_loudness = numpy.amax(data)
        if (max_loudness > self.data_max_loudness):
            self.data_max_loudness = max_loudness
    
    def get_sound_data(self):
        for file in self.wav_files:
            print(file)
            yield wavfile.read(file)
    
    def run_through_data(self):
        samplerate, data = self.sound_data_generator.__next__()
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
            self.sound_time_array.append(self.rec_datetime + datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS))
            
        if self.sound_time_array:
            self.sound_array = numpy.append(self.sound_array, array)
            silence_duration_in_seconds = (self.rec_datetime - self.sound_time_array[-1]).total_seconds()
            if silence_duration_in_seconds >= self.MAX_SILENCE_DURATION_IN_SECONDS:
                self.sound_array = self.sound_array[:-self.MAX_SILENCE_DURATION_IN_SECONDS * self.samplerate]
                self.append_data_to_data_point_list()
            
        if (self.rec_datetime.time() == self.MIDNIGHT and self.sound_time_array):
            self.append_data_to_data_point_list()
    
    def append_data_to_data_point_list(self):
        mp3_link = self.create_mp3_audio_files()
        self.data_point_list.append({
            'startTime': self.sound_time_array[0].isoformat(),
            'stopTime': self.sound_time_array[-1].isoformat(),
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
        
    def create_mp3_audio_files(self):
        wavfile.write('mp3_source.wav', self.samplerate, self.sound_array)
        mp3_name = datetime.datetime.strftime(self.sound_time_array[0], '%Y-%m-%d_%H-%M-%S') + '.mp3'
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        mp3_link = self.upload_file_to_bucket(mp3_name, "audioFiles")
        os.remove(mp3_name)
        return mp3_link
    
    def upload_file_to_bucket(self, file, folder=""):
        s3_client = boto3.client('s3')
        key = os.path.join('assets', self.prefix, folder, file)
        s3_client.upload_file(file, 'quietavenue.com', key)
        return key
    
    def append_data_to_sound_array(self, last_array):
        try:
            samplerate, data = self.sound_data_generator.__next__()
        except StopIteration:
            json_file = self.create_JSON()
            link_to_json_file = self.upload_file_to_bucket(json_file)
            self.upload_link_to_data_to_dynamodb(link_to_json_file)
            for file in self.wav_files:
                os.remove(file)
            os.remove(json_file)
            exit()
        
        data = numpy.append(last_array, data)
        return data
        
    def create_JSON(self):
        self.normalize_max_loudness()
        file = open('graphData.json', 'w')
        json.dump(self.data_point_list, file)
        file.close()
        return file.name
    
    def normalize_max_loudness(self):
        for data in self.data_point_list:
            data['maxLoudness'] = str(data['maxLoudness']/self.data_max_loudness)
       
    def upload_link_to_data_to_dynamodb(self, link):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table('quietavenue')
        
        response = table.update_item(
            Key={
                'PK': self.dynamodb_item_key,
            },
            UpdateExpression= 'set #ppty.graphDataLink=:d',
            ExpressionAttributeValues={
                ':d': link
            },
            ExpressionAttributeNames={
                "#ppty": "property"
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes'])