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
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });
    $(".form-register").submit(function(e){
        e.preventDefault();
        let email = $("#email").val();
        let passwd = $("#password").val();
        let passwd2 = $("#password2").val();
        if (!email) {
            $("#email-err span").html("Invalid email");
            $("#email-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("Password must contain lowercase letter, uppercase letter, number and special character");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("Passwords do not match");
            $("#password2-err").show();
            return;
        }

        let user_data = {
            name: email,
            email: email,
            password: passwd,
            password2: passwd2,
        }
        user_data = JSON.stringify(user_data)
        $.ajax({
            url: "/api/v1.0/users",
            type: "post",
            data: user_data,
            contentType: "application/json",
            dataType: "json",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function(response){
                if(response.errno == "0"){
                    alert("Success!")
                    location.href = "/login.html"
                }else{
                    alert(response.errmsg)
                }
            }
        })
    });
})