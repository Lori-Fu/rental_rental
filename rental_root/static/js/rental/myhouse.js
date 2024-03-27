$(document).ready(function(){
    $.get("/api/v1.0/session", function (response){
        if (response.errno != "0"){
            location.href = "/login.html"
        }
    }, "json");

    $.get("/api/v1.0/user/houses", function (response){
        const houses = response.data.houses
        let html = template("house-template", {houses: houses})
            $("#houses-list").html(html)
    },"json")
})