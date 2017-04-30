# AccentClassifyMe
General classificatier for English language accents

converting mp3 to wav:
ffmpeg -i audio/00003.mp3 -ac 1 -ar 16000 00003.wav


Running CMU Sphinx:

cd cmusphinx-alignment-example
javac -cp sphinx4/sphinx4-core/target/sphinx4-core-5prealpha-SNAPSHOT.jar:opencsv-3.3.jar Aligner.java

cd ..
cmusphinx-alignment-example/align.sh sample.wav transcript.txt
