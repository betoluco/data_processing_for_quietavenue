import boto3
import os
import json
import scipy.io.wavfile as wavfile
import subprocess
import datetime

class Utilities():
    def __init__(self, bucket_source_folder, bucket_destination_folder , dynamodb_item_key):
        self.SOURCE_BUCKET = 'quietavenue-raw-data'
        self.DESTINATION_BUCKET = 'quietavenue.com'
        self.DYNAMO_DB = 'quietavenue.com'
        
        self.bucket_source_folder = bucket_source_folder
        self.bucket_destination_folder = bucket_destination_folder
        self.dynamodb_item_key = dynamodb_item_key
        
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
        key = os.path.join('assets', self.bucket_destination_folder, folder, file)
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
            Prefix=self.bucket_source_folder, 
            StartAfter=self.bucket_source_folder)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for zip_file in zip_files['Contents']:
            client.download_file(self.SOURCE_BUCKET,
                                 zip_file['Key'],
                                 os.path.basename(zip_file['Key'])) #basename eliminates the prefix