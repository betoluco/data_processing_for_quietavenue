import boto3
import os
import json
import scipy.io.wavfile as wavfile
import subprocess
import datetime

from fetch_and_preprocess import FetchAndPreprocess 
from extract_data import ExtractData

class Utilities():
    def __init__(self):
        self.SOURCE_BUCKET = 'quietavenue-raw-data'
        #The audiofilesource S3 bucket folder were the source files are in (1020-Helm-Ln-Foster-City-Ca-94404/audio/)
        self.source_folder = '1020-Helm-Ln-Foster-City-Ca-94404/audio/'
        self.DESTINATION_BUCKET = 'quietavenue-dev-s3bucketassets-1k6f7f4u682l1'
        #The quietavenue.com S3 bucket folder were the generated audio files are going to be stored (1020-Helm-Ln-Foster-City-CA-94404/)
        self.destination_folder = '1020-Helm-Ln-Foster-City-CA-94404/'
        self.DYNAMO_DB = 'quietavenue-dev-SourceDynamoDBTable-4D1OHO9YOS2K'
        #The key of the element in quietavenue DynamoDB table where the link to S3 bucket is going to be stored (1020-Helm-Ln-Foster-City-Ca-94404)
        self.dynamodb_item_key =	'1020-Helm-Ln-Foster-City-Ca-94404'
        self.recording_start_datetime = datetime.datetime(2020, 2, 11, 10, 00) #YYYY, MM, DD, HH, MM,
        
        
        
    def sort_wave_files(self):
        wav_files = []
        for file in os.listdir():
            if file.endswith(('.WAV', '.wav')):
                wav_files.append(file)
        wav_files.sort()
        return wav_files
        
    def get_sound_data(self, wav_files):
        for file in wav_files:
            print(file)
            yield wavfile.read(file)
        
    def upload_file_to_bucket(self, file, folder=""):
        s3_client = boto3.client('s3')
        key = os.path.join('assets', self.destination_folder, folder, file)
        s3_client.upload_file(file, self.DESTINATION_BUCKET, key)
        return key
        
    def create_JSON(self, data_point_list):
        data_point_list
        file = open('graphData.json', 'w')
        json.dump(data_point_list, file)
        file.close()
        return file.name
            
    def create_mp3_audio_files(self, samplerate, sound_array, mp3_name):
        wavfile.write('mp3_source.wav', samplerate, sound_array)
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        mp3_link = self.upload_file_to_bucket(mp3_name, "audioFiles")
        os.remove(mp3_name)
        return mp3_link
        
    def upload_link_to_data_to_dynamodb(self, link):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table(self.DYNAMO_DB)
        
        response = table.update_item(
            Key={
                'PK': self.dynamodb_item_key,
            },
            UpdateExpression= 'set #ppty.graphDataLink=:d',
            ExpressionAttributeValues={
                ':d': link
            },
            ExpressionAttributeNames={
                "#ppty": "estate"
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes'])
    
    def remove_wav_files(self, json_file):
        for file in os.listdir():
            if file.endswith(('.WAV', '.wav')):
                os.remove(file)
        os.remove(json_file)
    
    def download_files_from_bucket(self):
        """"Downloads bucket all the files inside a folder.

        List all the objects inside a folder in the audiofilesource bucket, 
        except the zero lenth object with the same name of the folder (folder object) 
        created automatically by the S3 Management Console and downloads them to the current location.
        """
        client = boto3.client('s3')
        zip_files = client.list_objects_v2(
            Bucket=self.SOURCE_BUCKET, 
            Prefix=self.source_folder, 
            StartAfter=self.source_folder)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for zip_file in zip_files['Contents']:
            client.download_file(self.SOURCE_BUCKET,
                                 zip_file['Key'],
                                 os.path.basename(zip_file['Key'])) #basename eliminates the prefix
                                 

utilities = Utilities() 
#FetchAndPreprocess(utilities)
ExtractData(utilities.recording_start_datetime, utilities)