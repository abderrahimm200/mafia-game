from  threading import Thread
from flask import Flask,render_template,url_for,redirect,request,session,flash
from flask_login import login_required,LoginManager,login_user,logout_user,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import  SocketIO,send,emit
import datetime,random,time,json,os,re
from  copy import deepcopy
name='name'
app=Flask(__name__)
app.config['SECRET_KEY']='mafiamafiagame'
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI']=uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key=os.environ.get("SECRET")
socketio = SocketIO(app)
db=SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'
login_manager.login_message = u"<h1 class='faild'>Please log in to access this page.</h1>"

#save useres
class User(UserMixin,db.Model):
    __tablename__ = 'use'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(120),unique=True,nullable=False)
    password=db.Column(db.String(60),nullable=False)
    def __init__(self,username,password):
        self.username=username
        self.password=password
db.create_all()

#login users
@login_manager.user_loader
def load_user(user_id):
    return  User.query.get(user_id)

#create rooms
rooms={"all":{"players":set({}),"player_role":[],"roles":[],"villageois":[],"mafia":[],"doctor":[],"vote":[],"detective":[],"kill":set({}),"hill":[],"dic_players":{},"messages":[],"start":False,"vote_cache":False,'active':set(),'day':1,'night':False}}
list_room=[]

"""     **********         functions for the game          ***********     """

#check if players join the room
def check_rooms(room_name):
    room=rooms[room_name]
    room_id=room["room_id"]
    time.sleep(600)
    if not room["start"]:
        rooms.pop(room_name)
        list_room.remove(room_name)
        socketio.emit(room_name+room_id+"reload")

#create roles for given number of players
def roles(godfather,angel,players_num):
    roles=[]
    if angel=="Yes":
        roles.append("angel")
    if godfather=="Yes":
        roles.append("godfather")
        if players_num in "45":
            pass
        elif players_num in "786":
            roles.append("mafia")
        else:
            roles+=["mafia"]*2
    else:
        if players_num in "45":
            roles.append("mafia")
        elif players_num in "786":
            roles+=["mafia"]*2
        else:
            roles+=["mafia"]*3
    roles+=['doctor']+['detective']
    return  roles+["villager"]*(int(players_num)-len(roles))

#create roles for each player
def create_roles(part):
    room=rooms[part]
    room_id=room["room_id"]
    copy_players=list(room["players"]).copy()
    copy_roles=room["roles"].copy()
    villageois=room["villageois"]
    mafia=room["mafia"]
    doctor=room['doctor']
    detective=room['detective']
    for i in range(len(copy_players)):
        ra,rb=random.choice(copy_players),random.choice(copy_roles)
        if rb=="mafia" or rb=="godfather":
            mafia.append(ra)
        else:
            villageois.append(ra)
        if rb=="doctor":
            doctor.append(ra)
        elif rb=="detective":
            detective.append(ra)
        elif rb=="angel":
            room["angel"]=ra
        room["player_role"].append((ra,rb))
        socketio.emit(part+room_id+"role"+ra,rb)
        copy_players.remove(ra)
        copy_roles.remove(rb)

#get player's role
def role(room,x):
    c=room['player_role']
    for i in c:
        if i[0]==x:
            return i[1]

#calcul vote
def voter(part,x):
    room=rooms[part]
    room_id=room["room_id"]
    dic_players=room['dic_players']
    players=room["players"]
    villageois=room["villageois"]
    mafia=room["mafia"]
    calc={}
    for i in set(x):
        calc[i]=x.count(i)
    calc_val=list(calc.values())
    if not calc_val or calc_val.count(max(calc_val))>1:
        return "Vote: no one died"
    else:
        for i in calc:
            if calc[i]==max(calc_val):
                players.remove(i)
                if i==room["admin"]:
                    room["admin"]=list(players)[0]
                if i in mafia:
                    mafia.remove(i)
                else:
                    villageois.remove(i)
                if "angel" in room and i==room["angel"] and room["day"]<3:
                    room.pop("angel")
                dic_players.pop(i)
                socketio.emit(part+room_id+"players",dic_players)
                return f"{i} is dead he was {role(room,i)}"

#chrono
def chrono(part,x,y):
    s=round(time.time())+x
    rooms[part]["skip"]=False
    room_id=rooms[part]["room_id"]
    while s-round(time.time())>=0  and not rooms[part]["skip"]:
        t=s-round(time.time())
        d=t//60
        r=t%60
        if d<10:
            d="0"+str(d)
        if r<10:
            r="0"+str(r)
        socketio.emit(part+room_id+"chrono",{"event":y,"timer":str(d)+":"+str(r),"admin":rooms[part]["admin"]})
        time.sleep(1)

#start part
def start(part):
    #creating  roles
    room=rooms[part]
    players=room["players"]
    active=room["active"]
    while len(active)<len(players):
        time.sleep(1)
    time.sleep(10)
    create_roles(part)
    villageois=room["villageois"]
    mafia=room["mafia"]
    doctor=room['doctor']
    detective=room['detective']
    dic_players=room['dic_players']
    room_id=rooms[part]['room_id']
    socketio.emit(part+room_id+"players",dic_players)
    room['num_det']=1
    angel=True if "angel" in room else False
    num_mafia=len(deepcopy(mafia))
    lvote=room['vote']
    #starting  part
    time.sleep(5)
    day=1
    while len(mafia) and len(villageois)>len(mafia):
        time.sleep(2)
        room['night']=True
        socketio.emit(part+room_id+"day",day)
        kill_check=room['kill']
        hill_check=room['hill']
        socketio.emit(part+room_id+"night","")
        #mafia
        for player in mafia:
            socketio.emit(part+room_id+"night"+player,"")
            socketio.emit(part+room_id+"mafia"+player,"<h1 style='padding:0;margin:0'>Kill a player </h1><h3 style='color:red;font-size:17px;margin:0'>*Note that if you're note agree to kill a player no one will die</h3>")
            socketio.emit(part+room_id+"godfather"+player,"<h1 style='padding:0;margin:0'>Kill a player </h1><h3 style='color:red;font-size:17px;margin:0'>*Note that if you're note agree to kill a player no one will die</h3>")
        chrono(part,45,"mafia")
        socketio.emit(part+room_id+"delplayers",{player:player for player in players})
        #doctor
        if "".join(doctor) in villageois: 
            socketio.emit(part+room_id+"doctor"+"".join(doctor),"Save a player")
            chrono(part,15,"doctor")
            socketio.emit(part+room_id+"delplayers",{player:player for player in players})
        #detective
        if "".join(detective) in villageois and room['num_det']<=num_mafia:
            socketio.emit(part+room_id+"detective"+"".join(detective),"Check mafia ,you have "+str(num_mafia-room['num_det']+1)+" checks")
            chrono(part,15,"detective")
            socketio.emit(part+room_id+"delplayers",{player:player for player in players})
        socketio.emit(part+room_id+"morning","")
        time.sleep(2)
        room['night']=False
        #result
        kill,hill="".join(list(kill_check)),"".join(hill_check)
        if kill==hill or (not kill):
            socketio.emit(part+room_id+"general"+str(day),"No one died this night")
        else:
            players.remove(kill)
            if kill==room["admin"]:
                room["admin"]=list(players)[0]
            if kill in mafia:
                mafia.remove(kill)
            else:
                villageois.remove(kill)
            socketio.emit(part+room_id+"general"+str(day),f"Mafia killed {kill}, he was {role(room,kill)}")
            dic_players.pop(kill)
        socketio.emit(part+room_id+"players",dic_players)
        if  not (len(mafia) and len(villageois)>len(mafia)):
            break
        #discussion
        chrono(part,150,"discussion")
        socketio.emit(part+room_id+"delplayers",{player:player for player in players})
        #vote
        for player in players:
            socketio.emit(f"{part}{room_id}vote{player}","")
        chrono(part,30,"vote")
        socketio.emit(part+room_id+"delplayers",{player:player for player in players})
        #calcul vote
        socketio.emit(part+room_id+"general"+str(day),voter(part,lvote))
        if angel and "angel" not in room:
            break
        lvote.clear()
        rooms[part]['kill'].clear()
        room['hill'].clear()
        day+=1
        room['day']=day
    #end of part
    if angel and "angel" not in room:
        socketio.emit(part+room_id+"generalend","Game over angel won")
    elif len(mafia):
        socketio.emit(part+room_id+"generalend","Game over mafia won")
    else:
        socketio.emit(part+room_id+"generalend","Game over villagers won")
    
    socketio.emit(part+room_id+"sala","")
    time.sleep(30)
    for player in  players:
        socketio.emit(part+room_id+"reload"+player,"")
    rooms.pop(part)

#delete part
def delete_room(room):
    time.sleep(7200)
    if room in rooms:
        rooms.pop(room)
        if room in list_room:
            list_room.remove(room)

"""         *********  socket getting messages from clients *********      """

#discussion message
@socketio.on('message')
def message(player):
    room=player['room']
    room_id=rooms[room]["room_id"]
    night=rooms[room]['night']
    mafia=rooms[room]['mafia']
    username=player['username']
    if username in rooms[room]['players']:
        player['time']=datetime.datetime.now().strftime("%H:%M") 
        if night:
            if username in mafia:
                for user in mafia:
                    emit(room+room_id+'msg'+user,player,broadcast=True)
        else:
            rooms[room]['messages'].append(player)
            emit(room+room_id+'msg',player,broadcast=True)

@socketio.on("connexion")
def connexion(msg):
    rooms[msg['room']]["active"].add(msg['username'])
    room_id=rooms[msg['room']]["room_id"]
    emit(msg['room']+room_id+"connect",msg['username'],broadcast=True)

#receiving from mafia
@socketio.on("mafia")
def kil(player):
    room=rooms[player['room']]
    room_id=room["room_id"]
    kill=room["kill"]
    target=player["target"]
    if not len(kill):
        kill.add(target)
    elif  target not in kill:
        kill.clear()
    emit(player['room']+room_id+role(room,player["username"]),"You killed "+target)
    for mafia in room['mafia']:
        if mafia!=player["username"]:
            emit(player['room']+room_id+mafia+str(room["day"]),player['username']+" killed "+target,broadcast=True)

#receiving from doctor
@socketio.on("doctor")
def doc(player):
    room=rooms[player['room']]
    room_id=room["room_id"]
    hill=room["hill"]
    hill.append(player['target'])
    emit(player['room']+room_id+"doctor","You saved "+player['target'])

#receiving from detective
@socketio.on("detective")
def es(player):
    room=rooms[player['room']]
    room_id=room["room_id"]
    room["num_det"]+=1
    esp=player['target']
    if role(room,esp)=="mafia":
        emit(player['room']+room_id+"detective",f"{esp} mafia")
    else:
        emit(player['room']+room_id+"detective",f"{esp} is not mafia")

#receiving votes
@socketio.on("vote")
def vote(player):    
    room=rooms[player['room']]
    room_id=room["room_id"]
    day=str(room['day'])
    vote_cache=room['vote_cache']
    player_role=room["player_role"]
    lvote=room["vote"]
    player_v=player['vote']
    lvote.append(player_v)
    if not vote_cache:
        for i in player_role:
            if i[0]!=player["username"]:
                emit(player['room']+room_id+i[0]+day,player["username"]+" voted for "+player_v,broadcast=True)
            else:
                emit(player['room']+room_id+player["username"]+day,"You voted for "+player_v)
    else:
        emit(player['room']+room_id+player["username"]+day,"You voted for "+player_v)

#skip
@socketio.on("skip")
def skip(room):
    rooms[room]["skip"]=True
"""     *************   routes  ***************     """

#login
@app.route("/",methods=['POST','GET'])
@app.route('/login',methods=['POST','GET'])
def login():
    if  request.method=="POST":
        username=request.form.get("username").lower()
        password=request.form.get("password")
        f_u=User.query.filter_by(username=username).first()
        f_p=User.query.filter_by(username=username,password=password).first()
        if not f_u:
            flash("Couldn't find your username <a href='/signup'>sign up</a>","login")
            return redirect(url_for('login'))
        elif f_p:
            session[name]=username
            login_user(f_u)
            return redirect(url_for('create_room'))
        flash("incorrect password try again",'login')
        return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/signup',methods=['POST','GET'])
def signup():
    if  request.method=="POST":
        username=request.form.get("username").lower()
        password=request.form.get('password')
        repassword=request.form.get('repassword')
        f_u=User.query.filter_by(username=username).first()
        if f_u:
            flash("username already taken try another one",'signup')
            return redirect(url_for('signup'))
        elif  not 4<len(username)<14:
            flash("username must be between 5 and 14 characters",'signup')
        elif  len(password)<8:
            flash("unvalid password, your password must include at least 9 characters",'signup')
            return redirect(url_for('signup'))
        elif password==repassword:
                user=User(username,password)
                db.session.add(user)
                db.session.commit()
                flash("Registred successfully. please login",'login-succes')
                return redirect(url_for('login'))
        flash("passwords didn't match",'signup')
        redirect(url_for("signup"))
    return render_template("signup.html")

#get the room
@app.route("/join",methods=['POST','GET'])
@login_required
def create_room():
    if request.method=="POST":
        room=request.form.get("room_name")#get name of room
        vote_cache=request.form.get("vote cache")#check if the user want the vote be hidden
        godfather=request.form.get("godfather")#check if the user want godfather role
        players_num=request.form.get("players_num")#get number of players
        angel=request.form.get("angel")
        if (vote_cache and room and godfather and players_num):
            if room not in rooms:
                list_room.append(room)
                rooms[room]=deepcopy(rooms['all'])
                rooms[room]['roles']=roles(godfather,angel,players_num)#return the list of roles depending of the number of players
                if vote_cache=="Yes":
                    rooms[room]["vote_cache"]=True
                    create_roles(room)
                rooms[room]["admin"]=session[name]
                rooms[room]["room_id"]=str(random.randint(1000000,2000000))
                Thread(target=check_rooms,args=(room,)).start()
                return redirect(url_for("join",room=room))
            else:
                flash("already exist","join")
        else:
            flash("Please complete all the fields","join")
    return render_template("join.html",rooms=list_room,numpl=[(len(rooms[i]['players']),len(rooms[i]['roles'])) for i in list_room],lenn=len(list_room))

#on join room
@app.route("/mafia/<room>",methods=['POST','GET'])
@login_required
def join(room):
    if room not in list_room:
        return redirect(url_for("create_room"))
    username=session[name]
    req_room=rooms[room]
    if len(req_room["players"])<len(req_room["roles"]) and (not req_room["start"]):
            req_room["players"].add(username)
            if len(req_room["players"])==len(req_room["roles"]):
                req_room["start"]=True
                for player in req_room['players']:
                    req_room['dic_players'][player]=player
                Thread(target=start,args=(room,)).start()
                Thread(target=delete_room,args=(room,)).start()
                list_room.remove(room)
            return render_template("welcome.html",room=room,username=session[name],room_id=req_room["room_id"],messages=req_room['messages'])    
    elif username in req_room["players"]:
            return render_template("welcome.html",room=room,role=role(rooms[room],session[name]),start=rooms[room]['start'],username=session[name],messages=req_room['messages'])
    return redirect(url_for("create_room"))

#lougout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('login')) 

if __name__=="__main___":
    app.run()
