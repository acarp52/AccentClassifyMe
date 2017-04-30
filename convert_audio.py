import subprocess
import os.path
import re

"""
Must be run in an environment where ffmpeg is installed.
"""

def convert_audio(speakerid):
    
    if not os.path.isfile("audio_wav/%s.wav" % speakerid):
        print("File not found:", speakerid)
        shell_cmd = "ffmpeg -i audio/%s.mp3 -ac 1 -ar 16000 audio_wav/%s.wav" % (speakerid, speakerid)
        print("Running command:", shell_cmd)
        process = subprocess.Popen(shell_cmd.split(), stdout=subprocess.DEVNULL)

def main():

    s_file = open('speakerids.txt', 'r')
    for speakerid in s_file:
        
        convert_audio(speakerid.strip())


    try:
        from subprocess import DEVNULL # py3k
    except ImportError:
        import os
        DEVNULL = open(os.devnull, 'wb')

    shell_cmd = "cmusphinx-alignment-example/align.sh audio_wav/00061.wav transcript.txt"
    process = subprocess.Popen(shell_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    # sphinx_out = open('sphinx_out.txt', 'w')
    # sphinx_out.write(output.decode())
    # sphinx_out.close()
    pattern = r'\"(.+?)\"'

    for line in output.decode().split('\n'):
        # print(line)
        matches = re.findall(pattern, line)
        if len(matches) > 0:
            print(matches)
    # print(output.decode())

main()