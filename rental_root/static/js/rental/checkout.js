var order_id;

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

$(document).ready(function(){
    $.get("/api/v1.0/session", function (response){
        if (response.errno != "0"){
            location.href = "/login.html"
        }
    }, "json");

    var queryData = decodeQuery();
    order_id = queryData["oid"];
})

window.paypal
  .Buttons({
    async createOrder() {
      try {
        const response = await fetch("/api/v1.0/order/" + order_id + "/payment", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrf_token"),
          },
          // use the "body" param to optionally pass additional order information
          // like product ids and quantities
          // body: JSON.stringify({
          //   cart: [
          //     {
          //       id: "YOUR_PRODUCT_ID",
          //       quantity: "YOUR_PRODUCT_QUANTITY",
          //     },
          //   ],
          // }),
        });
        const resp = await response.json()
        if ("4101" == resp.errno) {
            location.href = "/login.html";
        }else if("0" != resp.errno){
            alert(resp.errmsg);
            return;
        }
        const orderData = resp.data
        if (orderData.id) {
          return orderData.id;
        } else {
          const errorDetail = orderData?.details?.[0];
          const errorMessage = errorDetail
            ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
            : JSON.stringify(orderData);

          throw new Error(errorMessage);
        }
      } catch (error) {
        console.error(error);
        alert(`Could not initiate PayPal Checkout...<br><br>${error}`);
      }
    },
    async onApprove(data, actions) {
      try {
        const response = await fetch(`/api/v1.0/order/${order_id}/${data.orderID}/capture`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrf_token"),
          },
        });

        const resp = await response.json()
        const orderData = resp.data
        // Three cases to handle:
        //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
        //   (2) Other non-recoverable errors -> Show a failure message
        //   (3) Successful transaction -> Show confirmation or thank you message

        const errorDetail = orderData?.details?.[0];

        if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
          // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
          // recoverable state, per https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/
          return actions.restart();
        } else if (errorDetail) {
          // (2) Other non-recoverable errors -> Show a failure message
          throw new Error(`${errorDetail.description} (${orderData.debug_id})`);
        } else if (!orderData.purchase_units) {
          throw new Error(JSON.stringify(orderData));
        } else {
          // (3) Successful transaction -> Show confirmation or thank you message
          // Or go to another URL:  actions.redirect('thank_you.html');
          const transaction =
            orderData?.purchase_units?.[0]?.payments?.captures?.[0] ||
            orderData?.purchase_units?.[0]?.payments?.authorizations?.[0];

          var notification = `Transaction ${transaction.status}: ${transaction.id}`
          if (transaction.status == "COMPLETED") {
            notification += "\nYou will receive a confirmation email shortly!"
          }
          alert(notification);
          location.href = "/orders.html";
        }
      } catch (error) {
          alert(
              `Sorry, your transaction could not be processed...<br><br>${error}`,
          );
      }
    },
  })
  .render("#paypal-button-container");

// Example function to show a result to the user. Your site's UI library can be used instead.
function resultMessage(message) {
  const container = document.querySelector("#result-message");
  container.innerHTML = message;
}
