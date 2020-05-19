            //   join.html

let arr=['vote','gfather','players_num']
        $("#godfather").change(function(){
            $("#players_number").show()
        })
        $("#players_number").change(function(){
            $("#vote_cache").show()
        })
    $("#create").click(function(){
        $("#create").addClass("checked")
        $("#join").removeClass("checked")
        $("#create-rooms").show()
        $("#avaible-rooms").hide()
    })
    $("#join").click(function(){
        $("#join").addClass("checked")
        $("#create").removeClass("checked")
        $("#avaible-rooms").show()
        $("#create-rooms").hide()
    })

