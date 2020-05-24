import boto3
import os
import zipfile
import subprocess

class FetchAndDecompress():
    def __init__(self, bucket_folder):
        """Fetchs the audio files from the s3 bucket and decompress them
        
        Fetchs the files from the s3 Bucket, decompress them, appends them 
        to a list and converts the format so python can use them
        """
        self.BUCKET = 'audiofilesource'
        self.prefix = bucket_folder + '/'
        self.download_files_from_bucket()
        self.unzip_files()
        self.convert_adpcm_to_pcm()
        
    def download_files_from_bucket(self):
        """"Downloads from a bucket all the files inside a folder.

        List all the objects of a folder, except the zero lenth object with the name
        of the folder (folder object) created by the S3 Management Console. Loops 
        through that list and downloads them to the current location.
        """
        client = boto3.client('s3')
        zip_files = client.list_objects_v2(
            Bucket=self.BUCKET, 
            Prefix=self.prefix, 
            StartAfter=self.prefix)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for zip_file in zip_files['Contents']:
            client.download_file(self.BUCKET,
                                 zip_file['Key'],
                                 os.path.basename(zip_file['Key'])) #basename eliminates the prefix
        
    def unzip_files(self):
        """Extract the zip files and deletes them afterwards"""
        for file in os.listdir(os.getcwd()):
            if file.endswith('.zip'):
                zip_ref = zipfile.ZipFile(file)
                zip_ref.extractall()
                zip_ref.close()
                os.remove(file)
        
    
    def convert_adpcm_to_pcm(self):
        """Converts the files with .wav extension from adpcm to pcm
        
        converts the .wav files from compresion format Adaptive Differential Pulse 
        Code Modulation (adpcm) to Pulse Code Modulation (pcm) using ffmpeg in a subprocess

        """
        for file in os.listdir():
            if file.endswith('.wav'):
                new_file = 'pcm_' + file
                subprocess.run('ffmpeg -i ' + file + ' -acodec pcm_s16le ' + new_file, shell=True)
                os.remove(file)
                