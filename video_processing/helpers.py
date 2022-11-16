import boto3
import os
import subprocess

class helpers():
    def download_files_from_bucket(self, folder, bucket):
        """"Downloads from a bucket all the files inside a folder.
    
        List all the objects of a folder, except the zero lenth object with the name
        of the folder (folder object) created by the S3 Management Console. Loops 
        through that list and downloads them to the current location.
        """
        client = boto3.client('s3')
        files = client.list_objects_v2(
            Bucket=bucket, 
            Prefix=folder, 
            StartAfter=folder)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for file in files['Contents']:
            client.download_file(bucket,
                                 file['Key'],
                                 os.path.basename(file['Key'])) #basename eliminates the prefix

    def sort_files(self, extension):
        files_list = []
        for file in os.listdir(os.getcwd()):
            if file.endswith(extension):
                files_list.append(file)
        files_list.sort()
        return files_list

    def convert_to_mp4(self, files_list):
        for file in files_list:
            name = os.path.splitext(file)[0]
            subprocess.run('ffmpeg -i '+file+' -c:v h264 '+name+'.mp4' , shell=True)
  
    def contatenate_video(self, files_list, concatenated_file_name):
        with open('concat_files.txt', 'w') as f:
            for file in files_list:
                name = os.path.splitext(file)[0]
                subprocess.run('ffmpeg -i ' + file + ' -c copy ' + name + '.ts' , shell=True)
                f.write('file ' + name + '.ts\n')
        
        subprocess.run('ffmpeg -f concat -i concat_files.txt ' + concatenated_file_name , shell=True)
        os.remove('concat_files.txt')

    def upload_file_to_bucket(self, files_list, folder, bucket):
        s3_client = boto3.client('s3')
        for file in  files_list:
            s3_client.upload_file(file, bucket, folder + file)
            print(file)

    def clean_folder(self, extension):
        for file in os.listdir():
            if file.endswith(extension):
                os.remove(file)
