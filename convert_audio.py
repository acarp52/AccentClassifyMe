import subprocess
import os.path
import re
import numpy as np

"""
Must be run in an environment where ffmpeg is installed.
"""

def convert_audio(speakerid):
    
    if not os.path.isfile("audio_wav/%s.wav" % speakerid):
        print("File not found:", speakerid)
        shell_cmd = "ffmpeg -i audio/%s.mp3 -ac 1 -ar 16000 audio_wav/%s.wav" % (speakerid, speakerid)
        print("Running command:", shell_cmd)
        process = subprocess.Popen(shell_cmd.split(), stdout=subprocess.DEVNULL)


def parse_word_boundaries(speakerid, sphinx_out):

    pattern = r'\"(.+?)\"'

    speaker_word_boundaries = [speakerid]

    for line in sphinx_out.decode().split('\n'):
        # print(line)
        matches = re.findall(pattern, line)
        if len(matches) > 0:
            # word_times = [matches[0], int(matches[4]), int(matches[5])]
            # print(word_times)
            speaker_word_boundaries.append(matches[0])
            speaker_word_boundaries.append(int(matches[4]))
            speaker_word_boundaries.append(int(matches[5]))

    return speaker_word_boundaries


def main():

    try:
        from subprocess import DEVNULL # py3k
    except ImportError:
        import os
        DEVNULL = open(os.devnull, 'wb')


    s_file = open('speakerids.txt', 'r')

    word_boundaries = []

    for speakerid in s_file:
        
        s_id = speakerid.strip()
        convert_audio(s_id)

        shell_cmd = "cmusphinx-alignment-example/align.sh audio_wav/%s.wav transcript.txt" % s_id
        process = subprocess.Popen(shell_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()
    
        word_boundaries.append(parse_word_boundaries(s_id, output))
        print("Speaker %s aligned." % s_id)

    out_arr = np.asarray(word_boundaries)
    # print(out_arr)
    with open('word_boundaries.csv','wb') as f:
        np.savetxt("word_boundaries.csv", out_arr, delimiter=",", fmt='%s')
main()