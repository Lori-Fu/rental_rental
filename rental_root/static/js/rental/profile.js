function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $.get("/api/v1.0/profile/session", function (response){
        // console.log(response)
        if (response.errno == "0") {
            $('#user-email').attr('value', response.data.email);
            $('#user-name').attr('value', response.data.name);
        }else{
            location.href = "/login.html"
        }
    }, "json");


    $("#form-name").submit(function (e) {
        e.preventDefault();
        var name = $("#user-name").val();
        if (!name) {
            alert("Please provide username！");
            return;
        }
        $.ajax({
            url: "/api/v1.0/users/name",
            type: "post",
            data: JSON.stringify({name: name}),
            contentType: "application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".error-msg").hide();
                    showSuccessMsg();
                    var name = resp.data.name;
                    $("#user-name").value = name;
                } else {
                    $(".error-msg").show();
                }
            }
        })
    })
})