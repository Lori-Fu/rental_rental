function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
        url: "/api/v1.0/session",
        type: "delete",
        dataType: "json",
        headers:{
            "X-CSRFToken": getCookie("csrf_token")
        },
        success: function(response){
            if (response.errno == "0") {
                location.href = "/index.html";
            }
        }
    })
}

$(document).ready(function(){
    $.get("/api/v1.0/session", function (response){
        if (response.errno != "0"){
            location.href = "/login.html"
        }
    }, "json");
})