from datetime import datetime
from helpers import helpers
from fetch_and_preprocess import fetchAndPreprocess
from extract_data import extractData


#The audiofilesource S3 bucket folder were the source files are in (1020-Helm-Ln-Foster-City-Ca-94404/audio/)
source_folder = '1020-Helm-Ln-Foster-City-Ca-94404/audio/'
#The quietavenue.com S3 bucket folder were the generated audio files are going to be stored (1020-Helm-Ln-Foster-City-CA-94404/)
destination_folder = '1020-Helm-Ln-Foster-City-CA-94404'
#The key of the element in quietavenue DynamoDB table where the link to S3 bucket is going to be stored (1020-Helm-Ln-Foster-City-Ca-94404)
dynamodb_item_key =	'1020-Helm-Ln-Foster-City-Ca-94404'
recording_start_datetime = datetime(2020, 2, 11, 10, 00) #YYYY, MM, DD, HH, MM,

new_helper = helpers(source_folder, destination_folder, dynamodb_item_key)
fetchAndPreprocess(new_helper)
extractData(recording_start_datetime, new_helper).extract_data()
new_helper.clean_folder()