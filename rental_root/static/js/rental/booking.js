function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg(msg) {
    $(".popup-msg").html("Error: " + msg)
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function(){
    $.get("/api/v1.0/session", function(resp) {
        if ("0" != resp.errno) {
            alert("Please log in")
            location.href = "/login.html";
        }
    }, "json");

    $("#start-date").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        autoclose: true
    });
    $("#end-date").datepicker({
        format: "yyyy-mm-dd",
        startDate: "tomorrow",
        autoclose: true
    });

    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();
        if (startDate){
            var nextDay = moment(startDate, "YYYY-MM-DD").add(1, 'days');
            nextDay = moment(nextDay).format("YYYY-MM-DD")
            $("#end-date").datepicker("setStartDate", nextDay);
            if (endDate && endDate <= startDate ){
                endDate = nextDay
                $("#end-date").val(endDate)
            }
        }

        if (startDate && endDate && startDate < endDate) {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) ;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            if (days == 1){
                $(".order-amount>span").html(amount.toFixed(2) + " ("+ days +" night)");
            }else{
                $(".order-amount>span").html(amount.toFixed(2) + " ("+ days +" nights)");
            }
        }
    });

    var queryData = decodeQuery();
    var house_id = queryData["hid"];

    $.get("/api/v1.0/house/" + house_id, function(resp){
        if (0 == resp.errno) {
            $(".house-info>img").attr("src", resp.data.house.img_urls[0]);
            $(".house-text>h3").html(resp.data.house.title);
            $(".house-text>p>span").html((resp.data.house.price/100.0).toFixed(0));
        }
    });

    $(".submit-btn").on("click", function(e) {
        console.log($(".order-amount>span").html())
        if ($(".order-amount>span").html()) {
            $(this).prop("disabled", true);
            var startDate = $("#start-date").val();
            var endDate = $("#end-date").val();
            var data = {
                "house_id":house_id,
                "start_date":startDate,
                "end_date":endDate
            };
            $.ajax({
                url:"/api/v1.0/orders",
                type:"POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                headers:{
                    "X-CSRFTOKEN":getCookie("csrf_token"),
                },
                success: function (resp) {
                    console.log(resp)
                    if ("4101" == resp.errno) {
                        location.href = "/login.html";
                    } else if ("0" == resp.errno) {
                        alert("Success!")
                        location.href = "/orders.html";
                    } else {
                        showErrorMsg(resp.errmsg);
                    }
                }
            });
        }
    });
})
