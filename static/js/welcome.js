//welcome.html

var username=$("#room-username").html();
var room=$("#room-name").html();
console.log(room,username);

var socket = io.connect(location.protocol+'//'+document.domain+':'+location.port);
// var players=;
//functions
//create players button
window.addEventListener('load',function(){
function create(){
for (var key in players){
    $("#players-button").append(`<button class="players-choice" id=${players[key]}>${players[key]}</button>`)
}}
function voter(){
    create();
    $("#choose1").html("Vote for player")
    for (let i = 0; i < $(".players-choice").length; i++) {
    const e =  $(".players-choice")[i];
    $(e).click(function(){
            socket.emit("vote",{"username":username,"vote":$(e).html(),"room":room})
            $("#players-button").html("<h2  style='color:black'>You voted for "+$(e).html()+"</h2>");
            $("#choose1").html("Nothing to do now")
        });   
    }
}
function play(role){
    create();
    for (let i = 0; i < $(".players-choice").length; i++) {
    const e =  $(".players-choice")[i];
    $(e).click(function(){
        if(role=="godfather"){
            role="mafia";
        }
        socket.emit(role,{"username":username,"target":$(e).html(),"room":room})
        $("#players-button").html("");
        $("#choose1").html("Nothing to do now")
    });
    }
}
//connect
    socket.emit("connexion",{'room':room,"username":username})

//message  
//send
$("#send").click(function(){
    msg={"room":room,"username":username,"msg":$("#msg-box").val()}
    console.log(msg)
    $("#msg-box").val("")
        socket.emit("message",msg)}) 
$("#msg-box").keypress(function(event){
    if(event.which==13){
        $("#send").click();
    }
})
//receive
socket.on(room+"msg",function(msg){
if (msg['username']==username){
        $("#update-msg").prepend(`<div class="msg-div sended-msg"><span class="message">${msg['msg']}</span><br><span  class="time">${msg['time']}</span></div>`)
    }else{        
        $("#update-msg").prepend(` <div class="msg-div"><span class="username">@${msg['username']}</span><br><span class="message">${msg['msg']}</span><br><span  class="time">${msg['time']}</span></div>`)
    }
})
socket.on(room+"msg"+username,function(msg){
            if (msg['username']==username){
            $("#mafia-msg").prepend(`<div class="msg-div sended-msg"><span class="message">${msg['msg']}</span><br><span  class="time">${msg['time']}</span></div>`)
            }else{        
                $("#mafia-msg").prepend(` <div class="msg-div"><span class="username">@${msg['username']}</span><br><span class="message">${msg['msg']}</span><br><span  class="time">${msg['time']}</span></div>`)
            }
    })


socket.on(room+'night'+username,function(){
$('#mafia-msg').css("display","flex")
$('#update-msg').hide()
})
socket.on(room+"night",function(){
$("#game-side").css("background-image",'url("/static/css/game-night.jpg")')
})

socket.on(room+"morning",function(){
$("#game-side").css("background-image",'url("/static/css/game-morning.jpg")')
$('#mafia-msg').hide()
$('#update-msg').css("display","flex")
})
socket.on(room+"reload"+username,function(){
    location.reload();
})


socket.on(room+"delplayers",function(){
$("#players-button").html("");
$("#choose1").html("Nothing to do now")
})
socket.on(room+"chrono",function(msg){
    document.getElementById("chrono").innerHTML= `<h1 id="event">${msg['event']}</h1><h2 id='timer'>${msg['timer']}</h2>`;
})

socket.on(room+"vote"+username,function(){
    voter();
})
socket.on(room+"generalend",function(msg){
    $("#parts").prepend(`<div  class="part" id="partsala"><div class="up" id="upsala"><h2>${msg}</h2></div></div>`)
})

socket.on(room+"role"+username,function(role){
    document.getElementById("role").innerHTML=role;
    socket.emit("receive",{'username':username,'room':room})
    $("#wait").html("")
    socket.on(room+role,function(doc){
        $("#players-button").html(`<h2  style='color:black'>${doc}</h2>`);
    })
    socket.on(room+'day',function(dayy){
        var day=dayy;
        $("#parts").prepend(`<div  class="part" id="part${day}"><h1>Day${day}</h1><div class="up" id="up${day}"></div></div>`)
        
        socket.on(room+"general"+day,function(msg){
            $(`#up${day}`).append(`<h2>${msg}</h2>`)
        })
        socket.on(room+username+day,function(vote){
            $(`#up${day}`).append(`<h2>${vote}</h2>`)
            })
            
    })
    socket.on(room+role+username,function(msg){
        $("#choose1").html(msg)
        play(role);
    })
    socket.on(room+"players",function(msg){
        players=msg;
    })
    
    })
})