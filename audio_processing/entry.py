import datetime

from fetch_and_preprocess import FetchAndPreprocess 
from extract_data import ExtractData
#Ejecute to create a new estate for quietavenue

recording_start_datetime = datetime.datetime(2020, 2, 11, 12, 25) #YYYY, MM, DD, HH, MM,
#The audiofilesource S3 bucket folder were the source files are in (1020-Helm-Ln-Foster-City-Ca-94404/audio/)
audio_files_source = '1020-Helm-Ln-Foster-City-Ca-94404/audio/'
#The quietavenue.com S3 bucket folder were the generated audio files are going to be stored (1020-Helm-Ln-Foster-City-CA-94404/)
audio_files_storage = '1020-Helm-Ln-Foster-City-CA-94404/'
#The key of the element in quietavenue DynamoDB table where the link to S3 bucket is going to be stored (1020-Helm-Ln-Foster-City-Ca-94404)
dynamodb_key =	'1020-Helm-Ln-Foster-City-Ca-94404'

FetchAndPreprocess(audio_files_source)
auxiliar = ExtractData(audio_files_storage, recording_start_datetime, dynamodb_key)