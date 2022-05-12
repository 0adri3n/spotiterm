
from re import A
from urllib.error import ContentTooShortError
from flask import Flask
from flask import render_template, url_for, request, flash, redirect, session
import sqlite3
import string, random
import os

from pip import main
import startupflaskspotify
import requests
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = "spotitermKey"

def hash_gen(length):
    pool = string.ascii_letters + string.digits
    return ''.join(random.choice(pool) for i in range(length))

def utf8len(s):
    return len(s.encode('utf-8'))


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route('/index')
def index():

    return render_template('index.html')

@app.route('/login')
def login():

    return render_template('login.html')


@app.route('/login/login2Account', methods=["POST"])
def login2Account():

    uservar = request.form['user'] 
    passwdvar = request.form['passwd']
    
    conn = sqlite3.connect('spotitermData.db')
    cur = conn.cursor()

    data = (uservar, passwdvar)

    cur.execute("""SELECT username, password, pplink, hashaccount FROM users WHERE username=? AND password=?""", data)

    liste = cur.fetchone()

    if liste !=  None:

        userData = []
        for i in liste :
            userData.append(i)

        session["username"] = userData[0]
        session["password"] = userData[1]
        session["pfplink"] = userData[2]
        session['hashaccount'] = userData[3]

        cur.close()
        conn.close()

        flash("Logged in sucessfully.")
        return redirect(url_for('index'))

    else: 

        cur.close()
        conn.close()

        flash("Wrong username or password. Please retry.")
        return redirect(url_for('login'))



@app.route('/logout/logout2Account', methods=['POST'])
def logout2Account():

    session.pop('username', None)
    session.pop('password', None)
    session.pop('pfplink', None)
    session.pop('hashaccount', None)
    try:
        session.pop('spotifytoken', None)
        session.pop('spotifyuser', None)
    except:
        pass
    session.clear()
    flash('You were logged out')
    return redirect(url_for('index'))



@app.route('/register')
def register():

    return render_template('register.html')

@app.route('/register/addAccount', methods=["POST"])
def registerAccount():

    uservar = request.form['user'] 
    passwdvar = request.form['passwd']
    hashvar = hash_gen(10)
    pplinkvar = request.form['pfplink']
    
    conn = sqlite3.connect('spotitermData.db')
    cur = conn.cursor()

    data = (hashvar, uservar, passwdvar, pplinkvar)

    try:

        if utf8len(pplinkvar) > 4093 or utf8len(uservar) > 4093 or utf8len(passwdvar) > 4093:

            cur.close()
            conn.close()

            flash("Profile photo URL is too large.")
            return redirect(url_for('register'))

        else:
            cur.execute("INSERT INTO users(hashaccount, username, password, pplink) VALUES(?, ?, ?, ?)", data)
            conn.commit()

            cur.close()
            conn.close()

            flash("Account registered.")
            return redirect(url_for('index'))
        

    except sqlite3.IntegrityError:

        cur.close()
        conn.close()

        flash("Username already used.")
        return redirect(url_for('register'))


@app.route('/spotiterm')
def spotiterm():

    try:

        if session['username']:
            return render_template('spotiterm.html')

    except:

        flash("Please login to access to this page.")
        return redirect(url_for('index'))


@app.route('/spotiterm/loginSpotify', methods=['POST'])
def loginSpotify():

    response = startupflaskspotify.getUser()
    print(response)
    return redirect(response)

def create_image_with_text(wh, text, lasttext):

    img = Image.new('RGB', (1400, 450), "black")
    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    width, height = wh
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), lasttext[0], font = fnt, fill="white") 
    for r in range(1, len(lasttext)):
        if r == 1:
            draw.text((500, 0), lasttext[r], font = fnt, fill="white") 
        else:
            draw.text((0, 50+(40*(r-2))), lasttext[r], font = fnt, fill="white") 
    draw.text((width, height), text, font = fnt, fill="white")
    return img

@app.route('/spotiterm/get4weeksTracks', methods=['POST'])
def get4weeksTrack():
    
    getData = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=last_month -type=tracks -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        artists = []
        for j in i['artists']:
            artists.append(j['name'])
        #print(i['name'], end=" - ")
        string = ""
        for a in range(len(artists)-1):
            string += artists[a]+", "
        string+=artists[-1]
        fstring = str(indexitems) + "/ " + i['name'] + " - " + string
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/get6monthsTracks', methods=['POST'])
def get6monthsTracks():

    getData = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=medium_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=last_6months -type=tracks -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        artists = []
        for j in i['artists']:
            artists.append(j['name'])
        string = ""
        for a in range(len(artists)-1):
            string += artists[a]+", "
        string+=artists[-1]
        fstring = str(indexitems) + "/ " + i['name'] + " - " + string
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/getAllTimeTracks', methods=['POST'])
def getAllTimeTracks():

    getData = requests.get("https://api.spotify.com/v1/me/top/tracks?time_range=long_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=all_time -type=tracks -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        artists = []
        for j in i['artists']:
            artists.append(j['name'])
        string = ""
        for a in range(len(artists)-1):
            string += artists[a]+", "
        string+=artists[-1]
        fstring = str(indexitems) + "/ " + i['name'] + " - " + string
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/get4weeksArtists', methods=['POST'])
def get4weeksArtists():

    getData = requests.get("https://api.spotify.com/v1/me/top/artists?time_range=short_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=last_month -type=artists -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        artists = i['name']
        fstring = str(indexitems) + "/ " + i['name']
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/get6monthsArtists', methods=['POST'])
def get6monthsArtists():

    getData = requests.get("https://api.spotify.com/v1/me/top/artists?time_range=medium_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=last_6months -type=artists -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        artists = i['name']
        fstring = str(indexitems) + "/ " + i['name']
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/getAllTimeArtists', methods=['POST'])
def getAllTimeArtists():

    getData = requests.get("https://api.spotify.com/v1/me/top/artists?time_range=long_term&limit=10&offset=0", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    datajson = getData.json()


    console = ["root@musicsavedme:~/spotiterm#", " show -time=all_time -type=artists -user=" + session['spotifyuser']]

    indexitems = 1
    for i in datajson['items']:
        fstring = str(indexitems) + "/ " + i['name']
        console.append(fstring)
        indexitems+=1

    frames = []
    x, y = 0, 0

    fnt = ImageFont.truetype("C:\Windows\Fonts\Consola.ttf", 30)
    img = Image.new('RGB', (1400, 450), "black")
    draw = ImageDraw.Draw(img)
    draw.text((x, y), console[0], font = fnt, fill="white")
    frames.append(img)
    x += 500
    lasttext = []
    lasttext.append(console[0])
    for i in range(len(console[1])+1):
        new_frame = create_image_with_text((x, y), console[1][:i], lasttext)
        frames.append(new_frame)
    lasttext.append(console[1])
    x = 0
    y+=50
    for elem in range(2, len(console)):
        
        for lettre in range(len(console[elem])+1):
            new_frame = create_image_with_text((x, y), console[elem][:lettre], lasttext)
            frames.append(new_frame)
        y+=40
        lasttext.append(console[elem])


    frames[0].save('static/gifgen/' + session['hashaccount'] + '.gif', format='GIF',append_images=frames[1:], save_all=True, duration=10)

    flash("Gif generation done !")
    return redirect(url_for('spotiterm'))

@app.route('/spotiterm/clearGif', methods=['POST'])
def clearGif():

    os.remove('static/gifgen/' + session["hashaccount"] + '.gif')

    flash("Last gif cleared.")
    return redirect(url_for('spotiterm'))

@app.route('/callback/')
def callback():

    startupflaskspotify.getUserToken(request.args['code'])

    session['spotifytoken'] = startupflaskspotify.getAccessToken()[0]
    r = requests.get("https://api.spotify.com/v1/me", headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(session["spotifytoken"])})
    r = r.json()
    session['spotifyuser'] = r['display_name']
    return redirect(url_for('spotiterm'))

@app.route('/edit')
def edit():

    try:
        if session['username']:
            return render_template('edit.html')

    except:

        flash("Please login to access to this page.")
        return redirect(url_for('index'))

@app.route('/edit/editUsername', methods=['POST'])
def editUsername():

    newuservar = request.form['newuser'] 

    conn = sqlite3.connect('spotitermData.db')
    cur = conn.cursor()

    data = (newuservar, session['username'])

    if utf8len(newuservar) > 4093:

        flash("New username is too large.")
        return redirect(url_for('edit'))

    else:
        try:
            cur.execute("""UPDATE users SET username=? WHERE username=?""", data)
            conn.commit()

            session['username'] = newuservar
    
            cur.close()
            conn.close()

            flash("Username modified.")
            return redirect(url_for('edit'))
        
        except sqlite3.IntegrityError:

            flash("Username already used.")

            cur.close()
            conn.close()

            return redirect(url_for('edit'))

@app.route('/edit/editPassword', methods=['POST'])
def editPassword():
    
    newpasswdvar = request.form['newpasswd'] 
    currentpasswdvar = request.form['currentpasswd'] 

    if utf8len(newpasswdvar) > 4093:

            flash("New password is too large.")
            return redirect(url_for('edit'))

    else:

        if currentpasswdvar == session['password']:

            conn = sqlite3.connect('spotitermData.db')
            cur = conn.cursor()

            data = (newpasswdvar, session['username'], session['password'] )

            cur.execute("""UPDATE users SET password=? WHERE username=? AND password=?""", data)
            conn.commit()

            session['password'] = newpasswdvar
        
            cur.close()
            conn.close()

            flash("Password modified.")
            return redirect(url_for('edit'))

        else:

            flash("Wrong current password.")
            return redirect(url_for('edit'))


@app.route('/edit/editPfp', methods=['POST'])
def editPfp():

    newpfpvar = request.form['newpfplink'] 

    if utf8len(newpfpvar) > 4093:
        
        flash("Profile photo URL is too large.")
        return redirect(url_for('edit'))

    else:

        conn = sqlite3.connect('spotitermData.db')
        cur = conn.cursor()

        data = (newpfpvar, session['username'])

        cur.execute("""UPDATE users SET pplink=? WHERE username=?""", data)
        conn.commit()

        session['pfplink'] = newpfpvar
    
        cur.close()
        conn.close()

        flash("Profile photo modified.")
        return redirect(url_for('edit'))
        


@app.route('/profileInfo', methods=['POST'])
def profileInfo():

    if request.form['action'] == "edit":

        return redirect(url_for('edit'))

    elif request.form['action'] == "logout":

        logout2Account()
        return redirect(url_for('index'))


@app.route('/wtfisthis')
def wtfisthis():

    return render_template('wtfisthis.html')


if __name__ == '__main__':

    #import logging
    #logging.basicConfig(filename='server.log',level=logging.DEBUG)
    app.run(debug=True)

