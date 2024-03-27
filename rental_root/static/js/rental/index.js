
function centerModals(){
    $('.modal').each(function(i){
        var $clone = $(this).clone().css('display', 'block').appendTo('body');    
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top-30);
    });
}

function setStartDate() {
    var startDate = $("#start-date-input").val();
    if (startDate) {
        var nextDay = moment(startDate, "YYYY-MM-DD").add(1, 'days');
        nextDay = moment(nextDay).format("YYYY-MM-DD")

        $(".search-btn").attr("start-date", startDate);
        $("#start-date-btn").html(startDate);
        $("#end-date").datepicker("destroy");
        $("#end-date-btn").html("Check Out Date");
        $("#end-date-input").val("");
        $(".search-btn").attr("end-date", "");
        $("#end-date").datepicker({
            keyboardNavigation: false,
            startDate: nextDay,
            format: "yyyy-mm-dd"
        });
        $("#end-date").on("changeDate", function() {
            $("#end-date-input").val(
                $(this).datepicker("getFormattedDate")
            );
        });
        $(".end-date").show();
    }
    $("#start-date-modal").modal("hide");
}

function setEndDate() {
    var endDate = $("#end-date-input").val();
    if (endDate) {
        $(".search-btn").attr("end-date", endDate);
        $("#end-date-btn").html(endDate);
    }
    $("#end-date-modal").modal("hide");
}

function goToSearchPage(th) {
    var url = "/search.html";
    if ($(th).attr("area-id") || $(th).attr("start-date") || $(th).attr("end-date")) {
        url += "?"
    }
    if ($(th).attr("area-id")){
        url += ("aid=" + $(th).attr("area-id"));
    }
    if ($(th).attr("start-date")){
        if (url[url.length - 1] != "?"){
            url += "&";
        }
        url += ("sd=" + $(th).attr("start-date"));
    }
    if ($(th).attr("end-date")){
        if (url[url.length - 1] != "?"){
            url += "&";
        }
        url += ("ed=" + $(th).attr("end-date"));
    }
    location.href = url;
}

$(document).ready(function(){
    $.get("/api/v1.0/session", function (response){
        if (response.errno == "0"){
            $(".top-bar>.user-info>.user-name").html(response.data.name);
            $(".top-bar>.user-info").show();
        }else{
            $(".top-bar>.register-login").show();
        }
    }, "json");

    $.get("/api/v1.0/houses/index", function(resp){
        if ("0" == resp.errno) {
            $(".swiper-wrapper").html(template("swiper-houses-template", {houses:resp.data.houses}));
            var mySwiper = new Swiper ('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationClickable: true
            });
        }
    });

    $.get("/api/v1.0/areas", function(resp){
        if ("0" == resp.errno) {
            $(".area-list").html(template("areas-template", {areas:resp.data.areas}));
            $(".area-list a").click(function(e){
                $("#area-btn").html($(this).html());
                $(".search-btn").attr("area-id", $(this).attr("area-id"));
                $(".search-btn").attr("area-name", $(this).html());
                $("#area-modal").modal("hide");
            });
        }
    });

    $('.modal').on('show.bs.modal', centerModals);
    $(window).on('resize', centerModals);
    $("#start-date").datepicker({
        keyboardNavigation: false,
        startDate: "today",
        format: "yyyy-mm-dd"
    });
    $("#start-date").on("changeDate", function() {
        var date = $(this).datepicker("getFormattedDate");
        $("#start-date-input").val(date);
    });
})