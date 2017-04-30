# AccentClassifyMe
General classificatier for English language accents

Running CMU Sphinx:

cd cmusphinx-alignment-example
javac -cp sphinx4/sphinx4-core/target/sphinx4-core-5prealpha-SNAPSHOT.jar:opencsv-3.3.jar Aligner.java

cd ..
cmusphinx-alignment-example/align.sh sample.wav transcript.txt
