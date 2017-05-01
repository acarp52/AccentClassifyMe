from python_speech_features import mfcc
import numpy as np
import os
import csv
import query
import scipy.io.wavfile as wav
from pydub import AudioSegment
import time


def main():

    labels = ["speakerid", "sex", "area_code", "area_str", "lng", "lat", "word", "ms_time", "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"]
    
    # Initialize output file
    # open('mfcc_short.csv', 'w').close()
    f = open('mfcc.csv','w')
    base_writer = csv.writer(f,lineterminator='\n')
    base_writer.writerow(labels)
    f.close()

    # Prepare to add rows
    mfcc_file = open('mfcc.csv','a')
    writer = csv.writer(mfcc_file,lineterminator='\n')

    speaker_results = np.asarray(query.potgres_query())
    speaker_dict = dict(zip(speaker_results[:,0], speaker_results[:,1:]))

    with open('word_boundaries.csv', newline='') as csvfile:
        speaker_reader = csv.reader(csvfile, delimiter=',')
        for row in speaker_reader:
            clean_row = [item.strip(" '[]") for item in row]
            sound = AudioSegment.from_wav("audio_wav/%s.wav" % clean_row[0])
            row_class_num =  int(speaker_dict[clean_row[0]][4])
            row_class_str = speaker_dict[clean_row[0]][3]
            row_lat = float(speaker_dict[clean_row[0]][2])
            row_lng = float(speaker_dict[clean_row[0]][1])
            if speaker_dict[clean_row[0]][0] == 'male':
                row_sex = 0
            else:
                row_sex = 1
            feature_info = [clean_row[0], row_sex, row_class_num, row_class_str, row_lat, row_lng]
            for word in range(1, len(clean_row)-2, 3):
                current_word = clean_row[word]
                start_ms = int(clean_row[word+1])
                end_ms = int(clean_row[word+2])

                current_ms = start_ms
                while current_ms < end_ms:
                    newSlice = sound[current_ms:current_ms+10]
                    newSlice.export("audio_wav/%s_temp.wav" % clean_row[0], format="wav")
                    (rate,sig) = wav.read("audio_wav/%s_temp.wav" % clean_row[0])
                    # print(rate, sig)
                    mfcc_feat = mfcc(sig,rate,winlen=0.01,winstep=0.01)

                    os.remove("audio_wav/%s_temp.wav" % clean_row[0])
                    current_feature = feature_info + [current_word, current_ms] + list(mfcc_feat[0])
                    current_ms += 10
                    writer.writerow(current_feature)

            print("Extracted MFCCs for speaker: %s" % clean_row[0])

    # print(my_data)
    # print(speaker_dict)
    # print(out_arr)
    mfcc_file.close()
    

main()