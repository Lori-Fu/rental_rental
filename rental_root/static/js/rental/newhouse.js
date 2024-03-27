function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    $.get("/api/v1.0/session", function (response){
        if (response.errno != "0"){
            location.href = "/login.html"
        }
    }, "json");

    $.get("/api/v1.0/areas", function(response){
        if (response.errno == "0"){
            const areas = response.data.areas
            // for (let i=0; i<areas.length; i++){
            //     const area = areas[i]
            //     // console.log(`<option value="${area.aid}">${area.aname}</option>`)
            //     $("#area-id").append(`<option value="${area.aid}">${area.aname}</option>`)
            // }
            let html = template("areas-template", {areas: areas})
            $("#area-id").html(html)
        }
    },"json")

    $.get("/api/v1.0/facilities", function(response){
        if (response.errno == "0"){
            const facilities = response.data.facilities
            let html = template("facilities-template", {facilities: facilities})
            $("#house-facility-list").html(html)
        }
    },"json")


    $("#form-house-info").submit(function (e) {
        e.preventDefault();

        var data = {};
        $("#form-house-info").serializeArray().map(function (x) {
            data[x.name] = x.value
        });

        var facility = [];
        $(":checked[name=facility]").each(function (index, x) {
            facility[index] = $(x).val()
        });

        data.facility = facility;

        $.ajax({
            url: "/api/v1.0/houses",
            type: "post",
            contentType: "application/json",
            data: JSON.stringify(data),
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "4101") {
                    location.href = "/login.html";
                } else if (resp.errno == "0") {
                    $("#form-house-info").hide();
                    $("#form-house-image").show();
                    $("#house-id").val(resp.data.house_id);
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    })

    $("#form-house-image").submit(function (e) {
        e.preventDefault();
        $(this).ajaxSubmit({
            url: "/api/v1.0/houses/image",
            type: "post",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token"),
            },
            success: function (resp) {
                if (resp.errno == "4101") {
                    location.href = "/login.html";
                } else if (resp.errno == "0") {
                    alert("success")
                    location.href = "/detail.html?hid=" + resp.data.hid;
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    })

})