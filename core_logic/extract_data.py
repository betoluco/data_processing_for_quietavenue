import boto3
import datetime
import json
import numpy
import scipy.io.wavfile as wavfile
import os
import re
import subprocess


class ExtractData():
    
    def __init__(self, destination_bucket_folder, rec_datetime, dynamodb_item_key):
        """ Process audio data to obtain information
        
        Downloads ziped audio files from an S3 bucket and unzips them. Orders them 
        in cronologicaly order (a few seconds form the first file are trimend to get
        rid of undesire noise and to make it start at the minute exactly).
        Splits the audio data in to equal size chuncks (SAMPLE_SIZE_IN_SECONDS). 
        Extract max value data from the chunck array (one at the time) and stores it
        in a list.
        """
        
        pattern = re.compile("[A-Za-z0-9-_]+")
        if pattern.fullmatch(destination_bucket_folder) is not None:
            self.prefix = destination_bucket_folder 
        else:
            raise ValueError('The address must only contain "A-Z a-z 0-9 - _" character and no blank spaces')
        
        self.rec_datetime = rec_datetime
        self.dynamodb_item_key = dynamodb_item_key
        self.BUCKET = 'webfilesource'
        self.wav_files = []
        self.point_list = []
        self.sort_wave_files()
        self.X_AXIS_LENGTH_IN_MINUTES = 10 # When dividing by an hour the remanider has to be cero
        self.X_AXIS_LENGTH_IN_SECONDS = self.X_AXIS_LENGTH_IN_MINUTES * datetime.timedelta(minutes=1).seconds
        self.SAMPLE_SIZE_IN_SECONDS = .5
        
    def sort_wave_files(self):
        """Appends the wav files to a list and sorts them
        
        Loops through the local folder containing the wav files and appends it to
        a list. Once it is done orders the list
        """
        
        for file in os.listdir():
            if file.endswith('.wav'):
                self.wav_files.append(file)
        self.wav_files.sort()
        
    def process_data(self):
        """Calls the method in the correct order to process the data
        
        Gets the sound data from the first file and pass to a function to obtain
        the sample rate and a list (sample_list) containing the splited data from the first file.
        Loops through the list, extracting the data form the elements of the list and updates the time
        regiter. When there is only one elemente left in the list (sample_list), gets the data from
        the nex file split it and appends it to list (sample_list)
        
        """
        sound_data_generator = self.get_sound_data()
        sample_list, samplerate = self.process_first_file(sound_data_generator)
        while sample_list:
            for array in sample_list[:-1]:
                self.append_data_to_json(array, samplerate)
                self.update_rec_datetime(self.X_AXIS_LENGTH_IN_SECONDS)
            last_array = sample_list.pop()
            sample_list = self.append_data(last_array, sound_data_generator)
        
    def get_sound_data(self):
        """A generator that loops through the wav_files list and yeilds the sound data and samplerate

        Yeilds
        -----
        data : numpy array
            See PySoundFile library read method
        samplerate : integer
            See PySoundFile library read method
        
        """
        
        for file in self.wav_files:
            print(file)
            yield wavfile.read(file)

    def process_first_file(self, sound_data_generator):
        """Creates the first sample list
        
        Call a generator to obtain the data and samplerate of the 
        first files. Call a function to trims the data. Call another
        function to get a list that contains the splitted data 
        (although this can be executed in the process_data method,
        is separated in order to have data and trimed_data garbage
        collected to free space in memory)
        
        Parameters
        ----------
        sound_data_generator: Generator
            A generator that yeilds data and samplerate
        minutes_to_trim: Integer
            Minutes to trim form de start of the recording
            
        Returns
        -------
        : Calls the get_data_samples function
        """
        samplerate, data = sound_data_generator.__next__()
        data = self.trim_first_seconds(data, samplerate)
        data = self.trim_first_minutes(data, samplerate)
        data_samples = self.get_data_samples(data, samplerate, self.X_AXIS_LENGTH_IN_SECONDS)
        return data_samples, samplerate
    
    def trim_first_seconds(self, data, samplerate):
        """Trims a given time from the data array
        
        Trims from the data array the firts seconds recorded (seconds form the 
        first not complete minute) and the number of minutes passed as an argument. 
        Calls update_rec_datetime method to update the rec_datetime accordingly 
        to the trimed time.
        
        Parameters
        ----------
        data: numpy.array
            The data to be trimed
        samplerate: int
            Number of samples per second of the recodring
        minutes_to_trim: int
            Minutes to trim
            
        Return
        ------
        numpy.array
            The trimed array
        """
        seconds_to_trim = datetime.timedelta(minutes=1).seconds - self.rec_datetime.second
        self.update_rec_datetime(seconds_to_trim)
        data_points_to_trim = seconds_to_trim * samplerate
        trimed_data = numpy.delete(data, range(0, data_points_to_trim))
        return trimed_data
    
    def trim_first_minutes(self, data, samplerate):
        minutes_to_trim = self.rec_datetime.minute % self.X_AXIS_LENGTH_IN_MINUTES
        self.update_rec_datetime(minutes_to_trim * datetime.timedelta(minutes=1).seconds)
        data_points_to_trim = minutes_to_trim * samplerate * datetime.timedelta(minutes=1).seconds
        trimed_data = numpy.delete(data, range(0, data_points_to_trim))
        return trimed_data
          
    def get_data_samples(self, data, samplerate, sample_size_in_seconds):
        """ Splits the data array to get the samples
        
        Split a passed data array into self.SAMPLE_SIZE_IN_SECONDS size arrays
        and store them in a list. This function uses numpy split 
        
        Parameters
        ----------
        data: numpy.array
            The data to split
        samplerate:
            Number of samples per second of the recodring
            
        Returns
        -------
        : List
            A list containing array of size sample_size
        """
        
        stop = len(data)
        sample_size = int(sample_size_in_seconds *samplerate)
        samples = numpy.array_split(data, range(sample_size, stop, sample_size))
        return samples
    
    def append_data_to_json(self, data, samplerate):
        """Appends data points to a points_list
        
        Creates data points from the samples consisting of:
        The maximum value of the sample
        The hour, minute and the second of that samplerate
        A wav file with the sample
        A mp3 file with the sample
        A gaphic of the sample
        
        Parameters
        ----------
        data: numpy array
            Data to extract the amax
        """
        
        mp3_link = self.create_mp3_audio_files(data, samplerate)
        
        self.point_list.append({
            'time': datetime.datetime.strftime(self.rec_datetime, '%H:%M'),
            'strongest_sound': self.create_subsamples_list(data, samplerate),
            'mp3_link': mp3_link
        })
        
    def create_mp3_audio_files(self, data, samplerate):
        """Creates a .wav audio file
        
        Creates a wave (.wav) audio file using soundfile.write.
        The file is named by converting the rec_datetime variable 
        to a string with the format %H:%M %a %d %b %y where.
        %H: Hour (24-hour clock) as a zero-padded decimal number.
        %M: Minute as a zero-padded decimal number.
        %a: Weekday as locale’s abbreviated name.
        %d: Day of the month as a zero-padded decimal number.
        also calls a method to converte it to mp3 and to store it on s3
        
        Parameters
        ----------
        data: numpy array
            The data for the audio file
        samplerate: int
            The samplerate for the audio file
        """
        
        wavfile.write('mp3_source.wav',samplerate, data)
        mp3_name = datetime.datetime.strftime(self.rec_datetime, '%H-%M-%S_%a_%d') + '.mp3'
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        mp3_link = self.upload_file_to_bucket(mp3_name)
        os.remove('mp3_source.wav')
        return mp3_link
    
    def create_subsamples_list(self, data, samplerate):
        max_points = []
        samples = self.get_data_samples(data, samplerate, self.SAMPLE_SIZE_IN_SECONDS)
        for sample in samples:
            max_points.append(numpy.amax(sample).item())
        return max_points
        
    def upload_file_to_bucket(self, file):
        """Uploads the passed file to a s3 bucket
        
        Parameters
        ----------
        file: file
            The file to upload
        prefix: string
            The path to the file
        """
        s3_client = boto3.client('s3')
        key = os.path.join(self.prefix, datetime.datetime.strftime(self.rec_datetime, '%a_%b_%d_%Y'), file)
        s3_client.upload_file(file, self.BUCKET, key)
        os.remove(file)
        return key
    
    def update_rec_datetime(self, time_delta):
        """Updates rec_datetime adding SAMPLE_SIZE_IN_SECONDS to timedelta
        
        If rec_datetime is SAMPLE_SIZE_IN_SECONDS until midnigth (the end of the day)
        calls create_JSON(). Also updates rec_datetime by adding a time delta
        of the seconds passed as an argument
        
        Paramenters
        -----------
        seconds: Integer default value 60
            Seconds to add to rec_datetime        
        """
        MIDNIGHT = datetime.time(hour=0, minute=0, second=0)
        if (self.rec_datetime + datetime.timedelta(seconds=time_delta)).time() == MIDNIGHT:
            self.create_JSON()
        self.rec_datetime += datetime.timedelta(seconds=time_delta)

    def create_JSON(self):
        """Create the Json files with the point_list
        
        Creates a Json file using the date (Day of the month as a zero-padded decimal number,
        month as locale’s abbreviated name, Year without century as a zero-padded decimal number
        and Weekday as locale’s abbreviated name) as its name, and adds to the Json file the date
        with format(Weekday as locale’s abbreviated name, month as locale’s abbreviated name.
        day of the month as a zero-padded decimal number and year with century as a decimal number.)
        and the point_list
        
        """
        graph_data = {
            'date': datetime.datetime.strftime(self.rec_datetime, '%a %b %d %Y'),
            'data': self.point_list
        }
        file = open(datetime.datetime.strftime(self.rec_datetime, '%a_%d_%b_%y') + '.json', 'w')
        json.dump(graph_data, file)
        file.close()
        self.point_list = []
        txt_link = self.upload_file_to_bucket(file.name)
        self.upload_link_to_dynamodb(txt_link)
        
    def upload_link_to_dynamodb(self, value):
        """Uploads a link to dynamodb, pointing to a folder in S3 bucket wich contains the data of that day
        
        Parameters
        ----------
        Value: The link to upload 
        """
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
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
    
    def append_data(self, last_array, sound_data_generator):
        """Gets the data from the sound_data_generator and appends it to an array
        
        Call the sound_data_generator passed as an argument, to 
        obtain the data and append it to an array (the last array of the 
        list of array created with get_data_samples). Returns a call to
        get_data_samples
        
        Parameters
        ----------
        last_array: numpy_array
            The last array in the list
        sound_data_generator: Generator
            A generator that yeilds data and samplerate
        
        Returns
        -------
        : Calls the get_data_samples function
        """
        try:
            samplerate, data = sound_data_generator.__next__()
        except StopIteration:
            for file in self.wav_files:
                os.remove(file)
        data = numpy.append(last_array, data)
        data_samples = self.get_data_samples(data, samplerate, self.X_AXIS_LENGTH_IN_SECONDS)
        return data_samples