import boto3
import os
import zipfile
import subprocess

class FetchAndPreprocess():
    def __init__(self, utilities):
        """Download audio files from s3 and preprocess them
        
        Download audio files from audiofilesource S3 bucket, unzip
        the files and tranform them with the help of FFMPEG
        """
        utilities.download_files_from_bucket()
        self.unzip_files()
        self.convert_adpcm_to_pcm()
        
    def unzip_files(self):
        for file in os.listdir(os.getcwd()):
            if file.endswith('.zip'):
                print(file)
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
            if (file.endswith(('.WAV', '.wav'))):
                new_file = 'pcm_' + file
                subprocess.run('ffmpeg -i ' + file + ' -acodec pcm_s16le -ac 1 ' + new_file, shell=True)
                # 'ac 1 converts the file from stereo to mono'
                os.remove(file)
                