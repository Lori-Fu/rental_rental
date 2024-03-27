function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#email").focus(function(){
        $("#email-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        e.preventDefault();
        email = $("#email").val();
        passwd = $("#password").val();
        if (!email) {
            $("#email-err span").html("Invalid email");
            $("#email-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("Invalid password");
            $("#password-err").show();
            return;
        }

        let user_data = {
            email: email,
            password: passwd,
        }
        user_data = JSON.stringify(user_data)
        $.ajax({
            url: "/api/v1.0/sessions",
            type: "post",
            data: user_data,
            contentType: "application/json",
            dataType: "json",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function(response){
                if(response.errno == "0"){
                    location.href = "/index.html"
                }else{
                    alert(response.errmsg)
                }
            }
        })
    });
})