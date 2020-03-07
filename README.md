# banderplay - Bandersnatch movie player

This app uses VLC to play Bandersnatch movie.
To play:
1. Get the full movie itself, e.g. Bandersnatch.mkv
2. Install all python modules mentioned as imports in the app, e.g. using pip
3. Enable http interface in VLC player. 
Like mentioned here: https://wiki.videolan.org/Documentation:Modules/http_intf/#VLC_2.0.0_and_later
As credentials for http Authorization use empty login and the password "12345".
4. ! Restart VLC 
5. Open the movie in VLC
6. start banderplay.py

The app will download necessary metadata files from the Internet and then will start playing. 
Periodically playing will stop and then you will need to switch to application console to choose code of the next video 
fragment to play.
