import datetime

from fetch_and_preprocess import FetchAndPreprocess 
from extract_data import ExtractData

#The following variables are needed 
recording_start_datetime = datetime.datetime(2020, 5, 17, 16, 14) #YYYY, MM, DD, HH, MM,
#The audiofilesource S3 bucket folder were the source files are in the
audio_files_source = '1020 Helm Ln Foster City, CA 94404, USA/'
#The quietavenue.com S3 bucket folder were the generated audio files are going to be stored
audio_files_storage = '1170_Foster_City_Blvd_206_Foster_City_California/'
#The key of the places DynamoDB element where the grpah data is going to be stored
dynamodb_key =	'1170_Foster_City_Blvd_206_Foster_City_California'

#FetchAndPreprocess(audio_files_source)

auxiliar = ExtractData(
    audio_files_storage,
    recording_start_datetime,
    dynamodb_key
)