// After DOM fully loaded
// 1. delete header
// 2. load data from /api/property/

// remove wp header
$("header.entry-header").remove();

/*
$(document).ready(function(){
    //$("header.entry-header").remove();

    $("button").click(function(){
        $.get("http://127.0.0.1:5000/api/property/CRMLS/OC18252847",function(data,status){
            alert("Data: " + data["property_info"]["list_price"] + "\nStatus: " + status);
        });
    });
});
*/

function toThousands(num) {
    return (num || 0).toString().replace(/(\d)(?=(?:\d{3})+$)/g, '$1,');
}

