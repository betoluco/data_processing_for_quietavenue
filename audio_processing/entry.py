import datetime

from fetch_and_preprocess import FetchAndPreprocess 
from extract_data import ExtractData

#The following variables are needed 
recording_start_datetime = datetime.datetime(2020, 5, 17, 16, 14) #YYYY, MM, DD, HH, MM,
#The audiofilesource S3 bucket folder were the source files are in
audio_files_source = '1020 Helm Ln Foster City, CA 94404, USA/'
#The quietavenue.com S3 bucket folder were the generated audio files are going to be stored
audio_files_storage = '742_Aries_Ln_Foster_City_California_94404/'
#The key of the element in quietavenue DynamoDB table where the link to S3 bucket is going to be stored
dynamodb_key =	'457-Oak-St-APT-2-San-Francisco-CA-94102'

FetchAndPreprocess(audio_files_source)

auxiliar = ExtractData(audio_files_storage, recording_start_datetime, dynamodb_key)