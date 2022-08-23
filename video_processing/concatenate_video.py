import boto3
import os
import subprocess


class VideoProcessing():
    SOURCE_BUCKET = 'videofilesource'
    DESTINATION_BUCKET = 	'quietavenue-raw-data'
    source_folder = '1020 Helm Ln Foster City, CA 94404, USA/'
    destination_folder = '1020-Helm-Ln-Foster-City-Ca-94404/video/'
    complete_file_name = 'complete_file.AVI'
    
    def download_files_from_bucket(self):
        """"Downloads from a bucket all the files inside a folder.
    
        List all the objects of a folder, except the zero lenth object with the name
        of the folder (folder object) created by the S3 Management Console. Loops 
        through that list and downloads them to the current location.
        """
        client = boto3.client('s3')
        files = client.list_objects_v2(
            Bucket=self.SOURCE_BUCKET, 
            Prefix=self.source_folder, 
            StartAfter=self.source_folder)  # Eliminates from the list the zero length object named like the
                                # folder (folder object) created by the S3 Management Console.
                                # The folder object it is the first element in the list and its
                                # named equal to the folder (prefix)
        for file in files['Contents']:
            client.download_file(self.SOURCE_BUCKET,
                                 file['Key'],
                                 os.path.basename(file['Key'])) #basename eliminates the prefix
    
    def sort_files(self):
        files_list = []
        for file in os.listdir(os.getcwd()):
            if file.endswith('.AVI'):
                files_list.append(file)
        files_list.sort()
        return files_list
    
    def write_concat_file(self, files_list):
        with open('concat_files.txt', 'w') as f:
            for file in files_list:
                f.write("file '%s'\n" % file)
        self.contatenate_video()
                
    def contatenate_video(self):
        subprocess.run('ffmpeg -f concat -safe 0 -i concat_files.txt -c copy ' + self.complete_file_name , shell=True)
    
    def upload_file_to_bucket(self, files_list):
        s3_client = boto3.client('s3')
        for file in files_list:
            s3_client.upload_file(file, self.DESTINATION_BUCKET, self.destination_folder + file)
            
    def splitVideo(self):
        subprocess.run('ffmpeg -i complete_file.AVI -ss 0 -t 2211 -c copy part_1.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 2211 -t 2211 -c copy part_2.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 4422 -t 2211 -c copy part_3.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 6633 -t 2211 -c copy part_4.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 8844 -t 2211 -c copy part_5.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 11055 -t 2211 -c copy part_6.AVI' , shell=True)
        subprocess.run('ffmpeg -i complete_file.AVI -ss 13266 -t 2211 -c copy part_7.AVI' , shell=True)
        
    def remove_AVI_files(self):
        for file in os.listdir():
            if file.endswith(('.AVI', '.avi')):
                os.remove(file)


video_processing = VideoProcessing()
#video_processing.download_files_from_bucket()
#files_list = video_processing.sort_files()
#contatenate_video()
#video_processing.upload_file_to_bucket(files_list)
video_processing.remove_AVI_files()