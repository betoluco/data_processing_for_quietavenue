from helpers import helpers

UPLOAD_FOLDER = '1020 Helm Ln Foster City, CA 94404, USA/'
UPLOAD_BUCKET = 'videofilesource'

RAW_DATA_BUCKET = 'quietavenue-raw-data'
RAW_DATA_FOLDER = '1020-Helm-Ln-Foster-City-Ca-94404/video/'

CONCATENATED_FILE_NAME = 'concatVideo.mp4'
UPLOAD_BUCKET = 'videofilesource'

MP4 = '.mp4'
AVI = '.AVI'
TS = '.ts'

helpers = helpers()
helpers.download_files_from_bucket(UPLOAD_FOLDER, UPLOAD_BUCKET)
avi_files_list = helpers.sort_files(AVI)
helpers.convert_to_mp4(avi_files_list)
helpers.clean_folder(AVI)
mp4_files_lits = helpers.sort_files(MP4)
helpers.contatenate_video(mp4_files_lits, CONCATENATED_FILE_NAME)
helpers.upload_file_to_bucket(['concatF.mp4'], RAW_DATA_FOLDER, RAW_DATA_BUCKET)
mp4_files_lits = helpers.sort_files(MP4)
helpers.upload_file_to_bucket(mp4_files_lits, RAW_DATA_FOLDER, RAW_DATA_BUCKET)
helpers.clean_folder((MP4, TS))



