from helpers import helpers

RAW_DATA_BUCKET = 'quietavenue-raw-data'
RAW_DATA_FOLDER = '1020-Helm-Ln-Foster-City-Ca-94404/video/'

CONCATENATED_FILE_NAME = '1020-Helm-Ln-Foster-City-Ca-94404Video.mp4'
UPLOAD_BUCKET = 'quietavenue-dev-s3bucketassets-1k6f7f4u682l1'
UPLOAD_FOLDER = 'assets/2141-Mills-Ave-Menlo-Park-CA-94025/'

MP4 = '.mp4'
AVI = '.AVI'
TS = '.ts'

helpers = helpers()
helpers.download_files_from_bucket(RAW_DATA_FOLDER, RAW_DATA_BUCKET)
#helpers.convert_to_mp4(avi_files_list)
#helpers.clean_folder(AVI)
#mp4_files_lits = helpers.sort_files(MP4)
#helpers.contatenate_video(mp4_files_lits, CONCATENATED_FILE_NAME)
helpers.upload_file_to_bucket([CONCATENATED_FILE_NAME], UPLOAD_FOLDER, UPLOAD_BUCKET)
#helpers.clean_folder((MP4, TS))



