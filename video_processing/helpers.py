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
                f.write("file '%s'\n" % file)
        subprocess.run('ffmpeg -f concat -safe 0 -i concat_files.txt -c copy ' + concatenated_file_name + '.mp4' , shell=True)
    
    def upload_file_to_bucket(self, files_list, folder, bucket):
        s3_client = boto3.client('s3')
        for file in  files_list:
            s3_client.upload_file(file, bucket, folder + file)
            print(file)
            
    # def splitVideo(self):
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 0 -t 2211 -c copy part_1.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 2211 -t 2211 -c copy part_2.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 4422 -t 2211 -c copy part_3.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 6633 -t 2211 -c copy part_4.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 8844 -t 2211 -c copy part_5.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 11055 -t 2211 -c copy part_6.AVI' , shell=True)
    #     subprocess.run('ffmpeg -i complete_file.AVI -ss 13266 -t 2211 -c copy part_7.AVI' , shell=True)
        
    def clean_folder(self):
        for file in os.listdir():
            if file.endswith(('.AVI', '.avi', 'mp4')):
                os.remove(file)
