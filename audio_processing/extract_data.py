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
        
        self.SAMPLE_SIZE_IN_SECONDS = 60
        self.prefix = destination_bucket_folder
        self.rec_datetime = rec_datetime
        self.dynamodb_item_key = dynamodb_item_key
        self.wav_files = []
        self.data_point_list = []
        self.days_list = []
        self.data_max_loudness = 0
        self.sort_wave_files()
        self.sound_data_generator = self.get_sound_data()
        self.process_data()
        
    def sort_wave_files(self):
        for file in os.listdir():
            if file.endswith('.wav'):
                self.wav_files.append(file)
        self.wav_files.sort()
        
    def get_sound_data(self):
        for file in self.wav_files:
            print(file)
            yield wavfile.read(file)
    
    def process_data(self):
        samplerate, data = self.sound_data_generator.__next__()
        sample_list = self.get_data_samples(data, samplerate)
        while sample_list:
            for array in sample_list[:-1]:
                mp3_link = self.create_mp3_audio_files(array, samplerate)
                max_loudness = numpy.amax(array)
                if (max_loudness > self.data_max_loudness):
                    self.data_max_loudness = max_loudness
                
                self.data_point_list.append({
                    'date': self.rec_datetime.isoformat(),
                    'maxLoudness': max_loudness,
                    'mp3Link': mp3_link
                })
                
                self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
                self.append_to_days_list()
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data, samplerate)
            
    def get_data_samples(self, data, samplerate):
        stop = len(data)
        sample_size = int(self.SAMPLE_SIZE_IN_SECONDS * samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
        
    def create_mp3_audio_files(self, data, samplerate):
        wavfile.write('mp3_source.wav', samplerate, data)
        mp3_name = datetime.datetime.strftime(self.rec_datetime, '%Y-%m-%d_%H-%M-%S') + '.mp3'
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        mp3_link = self.upload_file_to_bucket(mp3_name, 'audio_files')
        os.remove(mp3_name)
        return mp3_link
    
    def upload_file_to_bucket(self, file, folder=''):
        s3_client = boto3.client('s3')
        key = os.path.join('properties',self.prefix, folder, file)
        s3_client.upload_file(file, 'quietavenue.com', key)
        link = os.path.join('https://s3-us-west-1.amazonaws.com/quietavenue.com', key)
        return link
        
    def append_to_days_list(self):
        MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        if (self.rec_datetime.time() == MIDNIGHT):
            self.days_list.append(self.rec_datetime.isoformat())

    def append_data_to_sound_array(self, last_array):
        try:
            samplerate, data = self.sound_data_generator.__next__()
        except StopIteration:
            file_name = self.create_JSON()
            link_to_file_name = self.upload_file_to_bucket(file_name)
            self.upload_link_to_data_to_dynamodb(link_to_file_name)
            for file in self.wav_files:
                os.remove(file)
            os.remove(file_name)
            exit()
        
        data = numpy.append(last_array, data)
        return data
        
    def create_JSON(self):
        self.normalize_max_loudness()
        file = open('graph_data.json', 'w')
        json.dump(
        {
            'data': self.data_point_list,
            'days': self.days_list
        }
        , file)
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
            UpdateExpression= 'set #ppty.audioData=:d',
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