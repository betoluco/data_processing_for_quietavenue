import boto3
import os
import zipfile
import subprocess

class FetchAndDecompress():
    def __init__(self, bucket_folder):
        """Download audio files from s3 and preprocess them
        
        Download audio files from audiofilesource S3 bucket, unzip
        the files and tranform them with the help of FFMPEG
        """
        self.prefix = bucket_folder
        self.download_files_from_bucket()
        self.unzip_files()
        self.convert_adpcm_to_pcm()
        
    def download_files_from_bucket(self):
        """"Downloads bucket all the files inside a folder.

        List all the objects inside a folder in the audiofilesource bucket, 
        except the zero lenth object with the same name of the folder (folder object) 
        created automatically by the S3 Management Console and downloads them to the current location.
        """
        client = boto3.client('s3')
        zip_files = client.list_objects_v2(
            Bucket='audiofilesource', 
            Prefix=self.prefix, 
            StartAfter=self.prefix)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for zip_file in zip_files['Contents']:
            client.download_file('audiofilesource',
                                 zip_file['Key'],
                                 os.path.basename(zip_file['Key'])) #basename eliminates the prefix
        
    def unzip_files(self):
        for file in os.listdir(os.getcwd()):
            if file.endswith('.zip'):
                zip_ref = zipfile.ZipFile(file)
                zip_ref.extractall()
                zip_ref.close()
                os.remove(file)
        
    
    def convert_adpcm_to_pcm(self):
        """Converts the .wav files from adpcm to pcm
        
        The .wav files, with a compresion format of Adaptive Differential Pulse 
        Code Modulation (adpcm) are converted to Pulse Code Modulation (pcm) 
        using ffmpeg plataform ejecuted in a python subprocess

        """
        for file in os.listdir():
            if file.endswith('.wav'):
                new_file = 'pcm_' + file
                subprocess.run('ffmpeg -i ' + file + ' -acodec pcm_s16le ' + new_file, shell=True)
                os.remove(file)
                