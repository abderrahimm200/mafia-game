/*  login.html   */

$("#show-hide").click(function(){
  if($("#show-hide").attr("class")=="fa fa-eye"){console.log($("#show-hide").attr("class"));

      $("#show-hide").removeClass("fa fa-eye");
      $("#password").get(0).type="text";
    $("#show-hide").addClass("fa fa-eye-slash")
  }else{
      $("#password").get(0).type="password";
      $("#show-hide").removeClass("fa fa-eye-slash");
    $("#show-hide").addClass("fa fa-eye")
  }
  })
