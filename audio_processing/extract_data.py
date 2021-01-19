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
        element in the array represents one minute of the recording and is 
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
                self.append_data_to_list(array, samplerate)
                self.update_rec_datetime()
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data, samplerate)
            
    def get_data_samples(self, data, samplerate):
        stop = len(data)
        sample_size = int(self.SAMPLE_SIZE_IN_SECONDS * samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    def append_data_to_list(self, data, samplerate):
        mp3_link = self.create_mp3_audio_files(data, samplerate)
        
        self.data_point_list.append({
            'date': self.rec_datetime.date().isoformat(),
            'max': int(numpy.amax(data)),
            'mp3_link': mp3_link
        })
        
    def create_mp3_audio_files(self, data, samplerate):
        wavfile.write('mp3_source.wav', samplerate, data)
        mp3_name = datetime.datetime.strftime(self.rec_datetime, '%H-%M-%S_%a_%d') + '.mp3'
        # %H: Hour (24-hour clock) as a zero-padded decimal number.
        # %M: Minute as a zero-padded decimal number.
        # %a: Weekday as locale’s abbreviated name.
        # %d: Day of the month as a zero-padded decimal number.
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        mp3_link = self.upload_file_to_bucket(mp3_name)
        os.remove(mp3_name)
        return mp3_link
        
    def upload_file_to_bucket(self, file):
        folder = datetime.datetime.strftime(self.rec_datetime, '%a_%b_%d_%Y')
        # %b Month as locale’s abbreviated name.
        # %d Day of the month as a zero-padded decimal number.
        # %Y Year with century as a decimal number.
        s3_client = boto3.client('s3')
        key = os.path.join('places',self.prefix, folder, file)
        s3_client.upload_file(file, 'quietavenue.com', key)
        link = os.path.join('quietavenue.com', key)
        return link

    def update_rec_datetime(self):
        MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        if (self.rec_datetime + datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)).time() == MIDNIGHT:
            self.upload_data_to_dynamodb()
        self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
    
    def upload_data_to_dynamodb(self):
        date = datetime.datetime.strftime(self.rec_datetime, '%a_%b_%d_%Y')
        json_data = json.dumps(self.data_point_list)
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table('properties')
        
        response = table.update_item(
            Key={
                'id': self.dynamodb_item_key,
            },
            UpdateExpression='set ' + date + '=:d',
            ExpressionAttributeValues={
                ':d': json_data
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes'])

    def append_data_to_sound_array(self, last_array):
        try:
            samplerate, data = self.sound_data_generator.__next__()
        except StopIteration:
            self.upload_data_to_dynamodb()
            exit()
            #for file in self.wav_files:
            #    os.remove(file)
        data = numpy.append(last_array, data)
        return data