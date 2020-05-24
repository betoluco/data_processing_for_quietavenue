# Downloads the video files (.AVI) from the given folder inside a bucket
# the files are store in a list that is sorted by name (since the files name have
# a numeric order) the list is later converted in to a .txt file and passed as an 
# arguement to a ffmpeg command to concatenate all the videos in to a single one

import boto3
import os
import subprocess

BUCKET = 'videofilesource'
bucket_folder = '1020 Helm Ln Foster City, CA 94404, USA'
prefix = os.path.join(bucket_folder, '')
complete_file_name = 'complete_file.AVI'

def download_files_from_bucket():
    """"Downloads from a bucket all the files inside a folder.

    List all the objects of a folder, except the zero lenth object with the name
    of the folder (folder object) created by the S3 Management Console. Loops 
    through that list and downloads them to the current location.
    """
    client = boto3.client('s3')
    files = client.list_objects_v2(
        Bucket=BUCKET, 
        Prefix=prefix, 
        StartAfter=prefix)  # Eliminates from the list the zero length object named like the
                            # folder (folder object) created by the S3 Management Console.
                            # The folder object it is the first element in the list and its
                            # named equal to the folder (prefix)
    for file in files['Contents']:
        client.download_file(BUCKET,
                             file['Key'],
                             os.path.basename(file['Key'])) #basename eliminates the prefix
    order_files()

def order_files():
    """ Creates a list with the names of the file in the current folder and orders it
    
    Loops through the files in the current folder and appends to a list all the files with an
    .AVI extension. Once the loop is done the list is sorted (the files are named using
    consecutive numeration, beeing )
    """
    file_list = []
    for file in os.listdir(os.getcwd()):
        if file.endswith('.AVI'):
            file_list.append(file)
    file_list.sort()
    write_concat_file(file_list)

def write_concat_file(files_list):
    with open('concat_files.txt', 'w') as f:
        for file in files_list:
            f.write("file '%s'\n" % file)
            
def contatenate_video():
    subprocess.run('ffmpeg -f concat -safe 0 -i concat_files.txt -c copy ' + complete_file_name , shell=True)

def upload_file_to_bucket():
    """Uploads the passed file to a s3 bucket
    
    Parameters
    ----------
    file: file
        The file to upload
    prefix: string
        The path to the file
    """
    
    s3_client = boto3.client('s3')
    s3_client.upload_file(complete_file_name, BUCKET, prefix + complete_file_name)


#download_files_from_bucket()
#order_files()
#contatenate_video()
#upload_file_to_bucket()


subprocess.run('ffmpeg -i complete_file.AVI -ss 0 -t 2211 -c copy part_1.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 2211 -t 2211 -c copy part_2.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 4422 -t 2211 -c copy part_3.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 6633 -t 2211 -c copy part_4.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 8844 -t 2211 -c copy part_5.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 11055 -t 2211 -c copy part_6.AVI' , shell=True)
subprocess.run('ffmpeg -i complete_file.AVI -ss 13266 -t 2211 -c copy part_7.AVI' , shell=True)