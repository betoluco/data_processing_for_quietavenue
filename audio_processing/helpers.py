import boto3
import os
import json
import scipy.io.wavfile as wavfile
import subprocess


class helpers():
    def __init__(self, source_folder, destination_folder, dynamodb_item_key, environment):
        self.SOURCE_BUCKET = 'quietavenue-raw-data'
        self.DESTINATION_BUCKET = 'quietavenue-dev-s3bucketassets-1k6f7f4u682l1'
        self.DYNAMO_DB = 'quietavenue-dev-SourceDynamoDBTable-4D1OHO9YOS2K'
        self.JSON_FILE_NAME = 'audioData.json'
        self.DYNAMO_DB_ATTRIBUTE_NAME = 'audioDataLink'
        self.DESTINATION_BUCKET_FOLDER_FOR_AUDIOS = 'audioFiles'
        self.ROUTE_TO_DESTINATION_FOLDER = 'assets'
        self.CLEAN_DATA = ('.WAV', '.wav', self.JSON_FILE_NAME)
        
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.dynamodb_item_key = dynamodb_item_key
        
        if environment == 'prod':
            self.DESTINATION_BUCKET = 'quietavenue-prod-s3bucketassets-d2nifjn1egsk'
            self.DYNAMO_DB = 'quietavenue-prod-SourceDynamoDBTable-55RWHSP2EBVF'
            
        
    def upload_file_to_bucket(self, file, folder=""):
        s3_client = boto3.client('s3')
        key = os.path.join(self.ROUTE_TO_DESTINATION_FOLDER, self.destination_folder, folder, file)
        s3_client.upload_file(file, self.DESTINATION_BUCKET, key)
        return key
        
    def create_JSON(self, data_point_list):
        data_point_list
        file = open(self.JSON_FILE_NAME, 'w')
        json.dump(data_point_list, file)
        file.close()
        self.upload_file_to_bucket(file.name)
        self.upload_link_to_data_to_dynamodb(file.name)
            
    def create_mp3_audio_files(self, samplerate, sound_array, mp3_name):
        wavfile.write('mp3_source.wav', samplerate, sound_array)
        subprocess.run('ffmpeg -i mp3_source.wav -acodec libmp3lame ' + mp3_name, shell=True)
        os.remove('mp3_source.wav')
        mp3_link = self.upload_file_to_bucket(mp3_name, self.DESTINATION_BUCKET_FOLDER_FOR_AUDIOS)
        os.remove(mp3_name)
        return mp3_link
        
    def upload_link_to_data_to_dynamodb(self, file):
        dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
        table = dynamodb.Table(self.DYNAMO_DB)
        
        response = table.update_item(
            Key={
                'PK': self.dynamodb_item_key,
            },
            UpdateExpression= 'set #ppty.' + self.DYNAMO_DB_ATTRIBUTE_NAME + '=:d',
            ExpressionAttributeValues={
                ':d': os.path.join(self.ROUTE_TO_DESTINATION_FOLDER, self.destination_folder, file)
            },
            ExpressionAttributeNames={
                "#ppty": "estate"
            },
            ReturnValues="UPDATED_NEW"
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 and 'Attributes' in response:
            print (response['Attributes'])
    
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

    def clean_folder(self):
        for file in os.listdir():
            if file.endswith(self.CLEAN_DATA):
                os.remove(file)
        os.remove(self.JSON_FILE_NAME)