function hrefBack() {
    history.go(-1);
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    var queryData = decodeQuery();
    var house_id = queryData["hid"];
    $.get("/api/v1.0/house/" + house_id, function(resp){
        if (resp.errno == 0){
            let house = resp.data.house
            $(".detail-con").html(template("house-template", {house: house}));
            $(".swiper-container").html(template("images-template", {images: house.img_urls, price: house.price}));

            if (resp.data.user_id != resp.data.house.user_id) {
                $(".book-house").attr("href", "/booking.html?hid="+resp.data.house.hid);
                $(".book-house").show();
            }else{
                $(".book-house").hide();
            }

            var mySwiper = new Swiper ('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            })
        }
    })


})