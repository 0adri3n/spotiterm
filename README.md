# spotiterm
<p align="center">spotiterm is a website interface when u can create account, then login in Spotify and generate GIF with ur top tracks/artists !</p>

# Setup


1. Download the repository.
2. Download required python module:
```diff
pip install flask
pip install Pillow
```
3. Create a Spotify App at https://developer.spotify.com/dashboard/. Copy Client ID and Secret Token. Then, modify ```CLIENT_ID``` and ```CLIENT_TOKEN``` in ```startupflaskspotify.py```.
4. Start server.py
5. Open your browser and go to http://localhost:5000/index
6. Ready to use !

#

<p align="center">Open an issue if you have an error !</p>

<img src="https://user-images.githubusercontent.com/62818208/168120244-e7b16834-f5f1-49a2-ac3b-0f6cb0effafd.png">

# Notes
Huge thanks to https://github.com/vanortg/Flask-Spotify-Auth ! With his program, I don't spend time to create my own to login in spotify api.

<ins>Fact :</ins> 

When I deploy spotiterm on https://musicsaved.me 's server, everything was fine except the most important thing : the GIF generation. My server was'nt good enough to generate gif...

<img src="https://user-images.githubusercontent.com/62818208/168119046-b23c9a3f-0efd-4b3c-adbc-58dcef56a6bc.PNG">
