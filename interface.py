import os
import datetime

from core_logic.fetch_decompress import FetchAndDecompress
from core_logic.extract_data import ExtractData

LOCAL_STORAGE_PATH = './source_files'
SOURCE_BUCKET_FOLDER = '1020 Helm Ln Foster City, CA 94404, USA'

if not os.listdir(LOCAL_STORAGE_PATH):
    fetch_data = FetchAndDecompress(SOURCE_BUCKET_FOLDER, LOCAL_STORAGE_PATH)


SAMPLE_SIZE_IN_SECONDS = 60
DESTINATION_BUCKET_FOLDER = '1020_Helm_Ln_Foster_City,CA_94404,USA'
DATETIME_REC_STARTS = '31 march 2019, 06:19:48 am'
DYNAMODB_ITEM_KEY = '37.546832,-122.255790'

datetime_rec = datetime.datetime.strptime(DATETIME_REC_STARTS, '%d %B %Y, %I:%M:%S %p')

extract_data = ExtractData(SAMPLE_SIZE_IN_SECONDS, DESTINATION_BUCKET_FOLDER, datetime_rec, DYNAMODB_ITEM_KEY, LOCAL_STORAGE_PATH)

extract_data.process_data()