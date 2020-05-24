import boto3
import datetime
import json
import numpy
import scipy.io.wavfile as wavfile
import os
import re
import subprocess

class SummaryGraph():
    
    def __init__(self, destination_bucket_folder, rec_datetime, dynamodb_item_key):
        """ Process audio data to obtain information

        """
        pattern = re.compile("[A-Za-z0-9-_/]+")
        if pattern.fullmatch(destination_bucket_folder) is not None:
            self.prefix = destination_bucket_folder 
        else:
            raise ValueError('The address must only contain "A-Z a-z 0-9 - _ /" character and no blank spaces')
        
        self.rec_datetime = rec_datetime
        self.dynamodb_item_key = dynamodb_item_key
        self.BUCKET = 'quietavenue.com'
        self.wav_files = []
        self.point_list = []
        self.sort_wave_files()
        self.sound_data_generator = self.get_sound_data()
        self.SAMPLE_SIZE_IN_SECONDS = 60
        
    def append_data_to_sound_array(self, last_array):
        """Appends to last_array the nex element in wav_files list
        
        Parameters
        ----------
        last_array: numpy_array
            The last array of the samples list
        
        Returns
        -------
        data_samples: list of arrays
            List of array each array of X_AXIS_LENGTH_IN_MINUTES size
        """
        try:
            samplerate, data = self.sound_data_generator.__next__()
        except StopIteration:
            self.create_JSON()
            exit()
            #for file in self.wav_files:
            #    os.remove(file)
        data = numpy.append(last_array, data)
        return data
        
    def append_data_to_list(self, data):
        """Appends extracted data points to points_list
        
        Parameters
        ----------
        data: numpy.array
            The data to split
        """
        self.point_list.append({
            'date': self.rec_datetime.date().isoformat(),
            'time_ms': (datetime.timedelta(hours=self.rec_datetime.hour).seconds
                + datetime.timedelta(minutes=self.rec_datetime.minute).seconds
                + datetime.timedelta(seconds=self.rec_datetime.second).seconds) * 1000,
            'max': int(numpy.amax(data))
        })
    
    def create_JSON(self):
        """Create the Json files with the point_list
        
        %a: Weekday as locale’s abbreviated name
        %b: Month as locale’s abbreviated name
        %d: Day of the month as a zero-padded decimal number
        %Y: Year with century as a decimal number
        %y: Year without century as a zero-padded decimal number
        """
        graph_data = {
            'data_points': self.point_list
        }
        file = open('summary.json', 'w')
        json.dump(graph_data, file)
        file.close()
        txt_link = self.upload_file_to_bucket(file.name)
        self.upload_link_to_dynamodb(txt_link)    
    
    def get_data_samples(self, data, samplerate, sample_size_in_seconds):
        """Splits the data array into sample_size_in_seconds size
        
        Parameters
        ----------
        data: numpy.array
            The data to split
        samplerate:
            The samplerate of the record
            
        Returns
        -------
        samples: List
            List containing array of size sample_size
        """
        stop = len(data)
        sample_size = int(sample_size_in_seconds *samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    def get_sound_data(self):
        """A generator that loops through the wav_files list and yeilds the sound data and samplerate

        Yeilds
        -----
        data : numpy array
            The record data points
        samplerate : integer
            The samplerate of the record
        
        """
        for file in self.wav_files:
            print(file)
            yield wavfile.read(file)
    
    def normalize_begining(self):
        samplerate, data = self.sound_data_generator.__next__()
        data, seconds_to_trim = self.trim_seconds_till_minute(data, samplerate)
        self.rec_datetime += datetime.timedelta(seconds=seconds_to_trim)
        return samplerate, data
        
    def process_data(self):
        """Loops through the samples list and call the method for extracting the data
        
        Loops through the samples list calling the method for extracting the data and 
        updating the time. making sure that the list is not empty by appending new samples
        extracted from the original files
        
        """
        samplerate, data = self.normalize_begining()
        sample_list = self.get_data_samples(data, samplerate, self.SAMPLE_SIZE_IN_SECONDS)
        while sample_list:
            for array in sample_list[:-1]:
                self.append_data_to_list(array)
                self.rec_datetime += datetime.timedelta(seconds=self.SAMPLE_SIZE_IN_SECONDS)
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data, samplerate, self.SAMPLE_SIZE_IN_SECONDS)
       
    def sort_wave_files(self):
        """Appends the files with .wav extension to a list and sorts them """
        for file in os.listdir():
            if file.endswith('.wav'):
                self.wav_files.append(file)
        self.wav_files.sort()
    
    def trim_seconds_till_minute(self, data, samplerate):
        """Trims the firts seconds recorded till the first complete minute
        
        Parameters
        ----------
        data: numpy.array
            The data to be trimed
        samplerate: int
            The samplerate of the record
            
        Return
        ------
        trimed_data: numpy.array
            The trimed array
        """
        seconds_to_trim = datetime.timedelta(minutes=1).seconds - self.rec_datetime.second
        data_points_to_trim = seconds_to_trim * samplerate
        trimed_data = numpy.delete(data, range(0, data_points_to_trim))
        return trimed_data, seconds_to_trim
    
    def upload_file_to_bucket(self, file, folder=''):
        """Uploads the passed file to an s3 bucket
        
        Parameters
        ----------
        file: file
            The file to upload
        """
        s3_client = boto3.client('s3')
        key = os.path.join(self.prefix, folder, file)
        s3_client.upload_file(file, self.BUCKET, key)
        os.remove(file)
        link = os.path.join(self.BUCKET, key)
        return link

    def upload_link_to_dynamodb(self, link):
        """Uploads a link to dynamodb, pointing to a folder in S3 bucket wich contains the data of that day
        
        Parameters
        ----------
        Value: The link to upload 
        """
        complete_link = os.path.join('https://s3-us-west-1.amazonaws.com', link)
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table('places')

        response = table.update_item(
            Key={
                'id': self.dynamodb_item_key,
            },
            UpdateExpression='set summary=:a',
            ExpressionAttributeValues={
                ':a': complete_link
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes']['summary'])

###################################################################################
#################
#################
#################
###################################################################################

class DailyGraph (SummaryGraph):
    def __init__(self, destination_bucket_folder, rec_datetime, dynamodb_item_key):
        super().__init__(destination_bucket_folder, rec_datetime, dynamodb_item_key)
        self.X_AXIS_LENGTH_IN_MINUTES = 10 # When dividing by an hour the remanider has to be cero
        self.SAMPLE_SIZE_IN_SECONDS = self.X_AXIS_LENGTH_IN_MINUTES * datetime.timedelta(minutes=1).seconds
        self.SUBSAMPLE_SIZE_IN_SECONDS = 1
    
    def append_data_to_list(self, data, samplerate):
        """Appends extracted data points to points_list
        
        Parameters
        ----------
        data: numpy.array
            The data to split
        samplerate:
            The samplerate of the record
        """
        
        mp3_name = self.create_mp3_audio_files(data, samplerate)
        folder = datetime.datetime.strftime(self.rec_datetime, '%a_%b_%d_%Y')
        mp3_link = self.upload_file_to_bucket(mp3_name, folder)
        
        self.point_list.append({
            'time': self.rec_datetime.isoformat(),
            'samples_list': self.create_subsamples_list(data, samplerate),
            'mp3_link': mp3_link
        })
        
    def create_JSON(self):
        """Create the Json files with the point_list
        
        %a: Weekday as locale’s abbreviated name
        %b: Month as locale’s abbreviated name
        %d: Day of the month as a zero-padded decimal number
        %Y: Year with century as a decimal number
        %y: Year without century as a zero-padded decimal number
        """
        graph_data = {
            'date': self.rec_datetime.isoformat(),
            'x_len_min': self.X_AXIS_LENGTH_IN_MINUTES,
            'subdamples': self.SUBSAMPLE_SIZE_IN_SECONDS,
            'data': self.point_list
        }
        file = open(datetime.datetime.strftime(self.rec_datetime, '%a_%d_%b_%y') + '.json', 'w')
        json.dump(graph_data, file)
        file.close()
        self.point_list = []
        txt_link = self.upload_file_to_bucket(file.name)
        self.upload_link_to_dynamodb(txt_link)   
        
    def create_mp3_audio_files(self, data, samplerate):
        """Creates a mp3 files from the data
        
        Creates a wave (.wav) audio file.
        The file is named by converting the rec_datetime variable 
        to a string with the format %H:%M %a %d %b %y where.
        %H: Hour (24-hour clock) as a zero-padded decimal number.
        %M: Minute as a zero-padded decimal number.
        %a: Weekday as locale’s abbreviated name.
        %d: Day of the month as a zero-padded decimal number.
        Converte the .wav file to mp3 using ffmpeg in a subprocess
        and to store it on s3
        
        Parameters
        ----------
        data: numpy array
            The data for the audio file
        samplerate: int
            The samplerate for the audio file
        """
        wavfile.write('mp3_source.wav', samplerate, data)
        mp3_name = datetime.datetime.strftime(self.rec_datetime, '%H-%M-%S_%a_%d') + '.mp3'
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        return mp3_name
        
    def create_subsamples_list(self, data, samplerate):
        """Splits the data in SAMPLE_SIZE_IN_SECONDS size and appends the max of every split to a list
        
        Parameters
        ----------
        data: numpy.array
            The data to split
        samplerate:
            The samplerate of the record
        """
        max_points = []
        samples = self.get_data_samples(data, samplerate, self.SUBSAMPLE_SIZE_IN_SECONDS)
        for sample in samples:
            max_points.append(numpy.amax(sample).item())
        return max_points

    def normalize_begining(self):
        samplerate, data = self.sound_data_generator.__next__()
        data, seconds_to_trim = self.trim_seconds_till_minute(data, samplerate)
        self.update_rec_datetime(seconds_to_trim)
        data, minutes_to_trim_in_sec = self.trim_to_normalize_to_X_AXIS_LENGTH(data, samplerate)
        self.update_rec_datetime(minutes_to_trim_in_sec)
        
        return samplerate, data
    
    def process_data(self):
        """Loops through the samples list and call the method for extracting the data
        
        Loops through the samples list calling the method for extracting the data and 
        updating the time. making sure that the list is not empty by appending new samples
        extracted from the original files
        
        """
        samplerate, data = self.normalize_begining()
        sample_list = self.get_data_samples(data, samplerate, self.SAMPLE_SIZE_IN_SECONDS)
        while sample_list:
            for array in sample_list[:-1]:
                self.append_data_to_list(array, samplerate)
                self.update_rec_datetime(self.SAMPLE_SIZE_IN_SECONDS)
            last_array = sample_list.pop()
            data = self.append_data_to_sound_array(last_array)
            sample_list = self.get_data_samples(data, samplerate, self.SAMPLE_SIZE_IN_SECONDS)
            
    def trim_to_normalize_to_X_AXIS_LENGTH(self, data, samplerate):
        """Trims the data so it starts in multiple of the X_AXIS_LENGTH
        
        Trims the firts seconds and the minutes necesary to make the recorded time
        a multiple of the X_AXIS_LENGTH also calls the method to update the 
        rec_datetime accordingly 
        to the trim.
        
        Parameters
        ----------
        data: numpy.array
            The data to be trimed
        samplerate: int
            The samplerate of the record
            
        Return
        ------
        data: numpy.array
            The trimed array
        """
        minutes_to_trim = self.rec_datetime.minute % self.X_AXIS_LENGTH_IN_MINUTES
        seconds_to_trim = (minutes_to_trim * datetime.timedelta(minutes=1).seconds) 
        data_points_to_trim = seconds_to_trim * samplerate
        data = numpy.delete(data, range(0, data_points_to_trim))
        return data, seconds_to_trim

    def update_rec_datetime(self, time_delta):
        """Updates rec_datetime by adding a time delta (in second) to rec_datetime
        
        Paramenters
        -----------
        seconds: Integer default value 60
            Seconds to add to rec_datetime        
        """
        MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        if (self.rec_datetime + datetime.timedelta(seconds=time_delta)).time() == MIDNIGHT:
            self.create_JSON()
        self.rec_datetime += datetime.timedelta(seconds=time_delta)
    
    def upload_link_to_dynamodb(self, value):
        """Uploads a link to dynamodb, pointing to a folder in S3 bucket wich contains the data of that day
        
        Parameters
        ----------
        Value: The link to upload 
        """
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table('places')

        response = table.update_item(
            Key={
                'id': self.dynamodb_item_key,
            },
            UpdateExpression='SET audio = list_append(audio, :a)',
            ExpressionAttributeValues={
                ':a': [value],
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes']['audio'])