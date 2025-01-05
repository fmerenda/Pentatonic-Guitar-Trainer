This is an interactive python app to learn the pentatonic scales on guitar. 
It's just started, and only does a minor pentatonic right now.
There's a command line version and a handy GUI version as well.
It can play the scale, and listen to you play it back. It will grade you on accuracy, and show you the results.

It's gamified, and you start at 120bpm, and once you hit 100%, it increases 10 bpm. You can set your target bpm. 
Once you hit the target, the next position opens up.

I didn't write a single line of code for this. I used Claude 3.5 to generate it, and iterated through it about 30 times.

It's very basic, and just scratching an itch I had. Feel free to steal it, improve it, etc. I may update it again when I have time.


==============
To run this program on your machine do the following:

 git clone https://github.com/fmerenda/Pentatonic-Guitar-Trainer.git
 cd Pentatonic-Guitar-Trainer/
 python3 -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt 
 
 Then you can run either file with:
     python3 $FILENAME
     
     
If you have problems building the audio module, you may have to do the following on your linux machine (debian based dists):    

sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
=============

License GPL 3.

#WNCSTRONG

** Hurricane Helene devistated my part of the world. If you like this program, please consider donating to the little
town near where I live. Thank you. https://helpmarshall.org/
