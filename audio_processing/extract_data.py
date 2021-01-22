import boto3
import datetime
import json
import numpy
import scipy.io.wavfile as wavfile
import os
import subprocess

class ExtractData():
    def __init__(self, destination_bucket_folder, rec_datetime, dynamodb_item_key):
        """Extract information from the audio files to make a sound graphic
        
        The information is stored in json arrays, one for every day recorded. Each
        element in the array represents SAMPLE_SIZE_IN_SECONDS (one minute) of the recording and is 
        an object that contains the time with the ISO 8601 format, a link to the audio 
        file (mp3),and a number representing the maximum intensity of the noise in 
        that minute.
        
        The audio files are uploaded to quietavenue.com S3 bucket and the extracted
        data to DynamoDB places table
        """
        
        self.SAMPLE_SIZE_IN_SECONDS = 60
        self.prefix = destination_bucket_folder
        self.rec_datetime = rec_datetime
        self.dynamodb_item_key = dynamodb_item_key
        self.wav_files = []
        self.data_point_list = []
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
                
                self.data_point_list.append({
                    'date': self.rec_datetime.isoformat(),
                    'max': int(numpy.amax(array)),
                    'mp3_link': mp3_link
                })
                
                self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
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
            os.remove('mp3_source.wav')
            exit()
        
        data = numpy.append(last_array, data)
        return data
        
    def create_JSON(self):
        file = open('graph_data.json', 'w')
        json.dump(self.data_point_list, file)
        file.close()
        return file.name
        
    def upload_link_to_data_to_dynamodb(self, link):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table('properties')
        
        response = table.update_item(
            Key={
                'id': self.dynamodb_item_key,
            },
            UpdateExpression='set  audio_data=:d',
            ExpressionAttributeValues={
                ':d': link
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes'])