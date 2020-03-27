import os
import datetime

from core_logic.fetch_decompress import FetchAndDecompress
from core_logic.extract_data import ExtractData

SOURCE_BUCKET_FOLDER = '1020 Helm Ln Foster City, CA 94404, USA'


fetch_data = FetchAndDecompress(SOURCE_BUCKET_FOLDER)


DESTINATION_BUCKET_FOLDER = '1020_Helm_Ln_Foster_City_CA_94404_USA'
DATETIME_REC_STARTS = '31 march 2019, 06:19:48 am'
DYNAMODB_ITEM_KEY = '37.546832,-122.255790'

datetime_rec = datetime.datetime.strptime(DATETIME_REC_STARTS, '%d %B %Y, %I:%M:%S %p')

extract_data = ExtractData(DESTINATION_BUCKET_FOLDER, datetime_rec, DYNAMODB_ITEM_KEY)

extract_data.process_data()