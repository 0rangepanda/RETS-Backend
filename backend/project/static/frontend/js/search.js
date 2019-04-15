    /*
     * Global vars
     */
    // should read from config file
    //console.log(ifpixel);

    apiurl = "http://127.0.0.1:5000/api";
    place = {}

    var curr_jsfile, scripts = document.getElementsByTagName("script");
    curr_jsfile = scripts[scripts.length - 1].getAttribute("src");
    var parent_url = curr_jsfile.split("/").slice(0, -2).join("/");
    //console.log("!!!url: " + parent_url + "/css/image/no-photo.jpg");
    nophoto_url = parent_url + "/css/image/no-photo.jpg";

    /* ------------------------------------------ Utils ----------------------------------------------- */
    /*
     * And comma to a number (like 1,000,000)
     * num: Int
     */
    function formatNumber(num) {
        return (num || 0).toString().replace(/(\d)(?=(?:\d{3})+$)/g, '$1,');
    }

    /*
     * Parse the hash path and return a dict
     * e.g.: !/city/DB/page/2 --> {"city": "DB", "page":"2"}
     */
    function parsehashpath(hashpath) {
        var path = hashpath.split("/");
        var args = {};
        for (let index = 1; index < path.length; index += 2) {
            args[path[index]] = path[index + 1];
        }
        return args;
    }

    /*
     * Parse the dict and return a hash path
     * e.g.: {"city": "DB", "page":"2"} --> !/city/DB/page/2 
     */
    function tohashpath(args) {
        var hashpath = "#!";
        for (var key in args) {
            hashpath += "/" + key + "/" + args[key];
        }
        return hashpath;
    }

    /*
     * Parse the dict and return a searcb (For api)
     * e.g.: {"city": "DB", "page":"2"} --> ?city=DB&page=2 
     * NOTE: need to modify here to match the api name
     */
    function tosearch(args, active) {
        if ($.isEmptyObject(args)) {
            return "";
        }
        // args dictionary
        var args_dict = {
            "city": "city",
            "minp": "minlistprice",
            "maxp": "maxlistprice",
            "beds": "bedmin",
            "baths": "bathmin",
            "stby": "orderby",
            "desc": "descend",
            "p": "p",
        };
        // orderby dictionary
        var ordby_dict = {
            "1": "reduce_price",
            "2": "reduce_percent",
            "3": "list_price",
            "4": "yearbuilt",
            "5": "area",
            "6": "pricepersquare",
        };
        var search = "?";
        // search += "status=A&"; //Active
        for (var key in args) {
            if (key in args_dict) {
                if (key == "stby") {
                    search += args_dict[key] + "=" + ordby_dict[args[key]] + "&";
                } else {
                    search += args_dict[key] + "=" + args[key] + "&";
                }
            }
        }
        // Handle text search
        if ("srchtxt" in args) {
            var searchtxt = args["srchtxt"];
            if ("type" in args) {
                var searchtype = args["type"];
                switch (searchtype) {
                    case "premise":
                        search += "streetname=" + searchtxt + "&";
                        break;
                    case "street_address":
                        search += "streetname=" + searchtxt + "&";
                        break;
                    case "postal_code":
                        search += "postalcode=" + searchtxt + "&";
                        break;
                    case "locality":
                        search += "city=" + searchtxt + "&";
                        break;
                    default:
                        break;
                }
            } else {
                // No type, do a WHERE OR query
                search += "streetname=" + searchtxt + "&";
                search += "postalcode=" + searchtxt + "&";
                search += "city=" + searchtxt + "&";
                search += "or=true" + "&";
            }
        }
        // only show active
        if (active) {
            search += "status=A" + "&";
        }
        return search;
    }

    /* ------------------------------------ Google Map --------------------------------------- */
    /*
     * Google Map API autocomplete
     */
    var defaultBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(-33.8902, 151.1759),
        new google.maps.LatLng(-33.8474, 151.2631)
    );

    var stateBounds = {
        ca: ["32.812736", "-119.216815", "34.608128", "-117.039301"]
        // lat/long boundaries list for states/provinces.
    };

    function getStateBounds(state) {
        return new google.maps.LatLngBounds(
            new google.maps.LatLng(stateBounds[state][0],
                stateBounds[state][1]),
            new google.maps.LatLng(stateBounds[state][2],
                stateBounds[state][3])
        );
    }

    var input = document.getElementById('text-input-2134486574');
    var options = {
        bounds: defaultBounds,
        componentRestrictions: {
            'country': 'us'
        },
        bounds: getStateBounds('ca'),
    };

    var autocomplete = new google.maps.places.Autocomplete(input, options);
    autocomplete.setFields(
        ['address_components', 'geometry', 'type', 'name']);
    autocomplete.addListener('place_changed', onPlaceChanged);
    /*
     * place_changed function
     */
    function onPlaceChanged() {
        place = autocomplete.getPlace();
        console.log(place);
        //console.log(place.name);
        //console.log(place.types);
        //console.log(place.address_components);
    }

    /* ------------------------------------- Jquery functions ----------------------------------------- */
    jQuery(document).ready(function ($) {
        /* ---------------------------------- DOM Logic -------------------------------------- */
        // ajax pool for clear all pending ajax     
        $.xhrPool = [];
        $.xhrPool.abortAll = function() {
            $(this).each(function(idx, jqXHR) {
                jqXHR.abort();
            });
            $.xhrPool = [];
            console.log('xhrPool clear');        
        };
        
        $.ajaxSetup({
            beforeSend: function(jqXHR) {
                $.xhrPool.push(jqXHR);
            },
            complete: function(jqXHR) {
                var index = $.xhrPool.indexOf(jqXHR);
                if (index > -1) {
                    $.xhrPool.splice(index, 1);
                }
            }
        });   

        // read logo img 
        $(".logo-wrapper-2134486574 > a > img").attr("src", parent_url+'/css/image/logo.png');

        // dropdown-menu max and min price input
        $(".text-input-dropdown-2134486574 > input").change(function () {
            //check input
            if (!/^\d+$/.test($(this).val())) {
                //not pure number
            } else {
                var changeval = parseInt($(this).val());
                var changetext = '$' + formatNumber(changeval);
                var replace = $(this).parent().parent().parent().find("button");
                replace.val(changeval);
                replace.text(changetext);
                replace.css("background-color", "#428BCA");
                replace.css("color", "#fff");
            }
        });

        //dropdown-menu a element click
        $("div.dropdown-menu > li > a").click(function () {
            if ($(this).attr('id') == "sortby-dec-2134486574" || $(this).attr('id') == "sortby-asc-2134486574") {
                return;
            }
            //console.log("div.dropdown-menu > li > a");
            var changetext = $(this).attr("data-display-text");
            var changeval = $(this).attr("data-value");
            var replace = $(this).parent().parent().parent().find("button");
            replace.css("background-color", "#428BCA");
            replace.css("color", "#fff");
            if (replace.attr('id') == "sortby-btn-2134486574") {
                if ($("button#sortby-btn-2134486574").attr("sort-value") == "desc") {
                    changetext += " ↓";
                } else {
                    changetext += " ↑";
                }
                $("button#sortby-btn-2134486574").attr("text-value", changetext);
                replace.css("background-color", "#ff8347");
                replace.css("color", "#fff");
            }
            replace.val(changeval);
            replace.text(changetext);
        });

        //sort by ascend toggle
        $("a#sortby-asc-2134486574").click(function () {
            $("button#sortby-btn-2134486574").attr("sort-value", "asc");
            if ($("button#sortby-btn-2134486574").attr("text-value") != "Sort by") {
                var buttontext = $("button#sortby-btn-2134486574").text().slice(0, -1);
                $("button#sortby-btn-2134486574").text(buttontext + "↑");
                $("button#sortby-btn-2134486574").attr("text-value", buttontext + "↑")
            }
        });

        //sort by descend toggle
        $("a#sortby-dec-2134486574").click(function () {
            $("button#sortby-btn-2134486574").attr("sort-value", "desc");
            if ($("button#sortby-btn-2134486574").attr("text-value") != "Sort by") {
                var buttontext = $("button#sortby-btn-2134486574").text().slice(0, -1);
                $("button#sortby-btn-2134486574").text(buttontext + "↓");
                $("button#sortby-btn-2134486574").attr("text-value", buttontext + "↓")
            }
        });

        /* --------------------------------- Hash Handler ---------------------------------------- */
        /*
         * According to url hash change html text
         */
        function argstohtml(args) {
            // sortby value-datatext
            var ordby_datatext = {
                "1": "Price Reduce (percentage)",
                "2": "Price Reduce (price)",
                "3": "List Price",
                "4": "Year Built",
                "5": "Square Footage",
                "6": "Price per Square",
            };

            var args_to_DOM = {
                "minp": "#min-price-btn-2134486574",
                "maxp": "#max-price-btn-2134486574",
                "beds": "#beds-btn-2134486574",
                "baths": "#baths-btn-2134486574",
                "stby": "#sortby-btn-2134486574",
                "srchtxt": "#text-input-2134486574",
            };

            for (var key in args_to_DOM) {
                if (args[key]) {
                    var DOM = $(args_to_DOM[key]);
                    if (key == "srchtxt") {
                        DOM.val(decodeURI(args[key]));
                        console.log(args[key]);
                        continue;
                    }
                    DOM.val(args[key]);
                    DOM.css("background-color", "#428BCA");
                    DOM.css("color", "#fff");
                    switch (key) {
                        case "minp":
                            DOM.text('$' + formatNumber(args[key]));
                            break;
                        case "maxp":
                            DOM.text('$' + formatNumber(args[key]));
                            break;
                        case "beds":
                            DOM.text(args[key] + "+ Beds");
                            break;
                        case "baths":
                            DOM.text(args[key] + "+ Baths");
                            break;
                        case "stby":
                            var DOMtext = ordby_datatext[args[key]];
                            if (args["desc"] == "true") {
                                DOM.attr("sort-value", "desc");
                                DOMtext += " ↓";
                            } else {
                                DOM.attr("sort-value", "asc");
                                DOMtext += " ↑";
                            }
                            DOM.text(DOMtext);
                            DOM.attr("text-value", DOMtext);
                            DOM.css("background-color", "#ff8347");
                            DOM.css("color", "#fff");
                            break;
                        default:
                            break;
                    }
                }
            }
        };

        /*
         * Parse all input, send request to api and present data
         */
        function loadresults() {
            //clear all previous ajax and previous data
            $("#gallery-properties").empty();
            $.xhrPool.abortAll = function () {
                $(this).each(function (idx, jqXHR) {
                    // console.log(jqXHR);
                    jqXHR.abort();
                });
                $.xhrPool = [];
            };
            $.xhrPool.abortAll();

            // According to url hash 
            // 1. generate apiurl 
            // 2. change html text TODO
            var args = parsehashpath(location.hash);
            var queryurl = apiurl + "/query" + tosearch(args, true);
            console.log(queryurl);
            argstohtml(args);
            // get data
            $.get(queryurl, function (data, status) {
                var args = parsehashpath(location.hash);
                var curpage = 0;
                if (args["p"]) {
                    curpage = parseInt(args["p"]);
                    delete args["p"];
                }
                // pagination
                $('#pagination').pagination({
                    items: data["count"],
                    itemsOnPage: data["query_para"]["page_size"],
                    cssStyle: 'light-theme',
                    hrefTextPrefix: tohashpath(args) + '/p/',
                    hrefTextSuffix: '',
                    selectOnClick: true,
                    currentPage: curpage
                });

                var url = document.location.toString();
                var arrUrl = url.split("/");

                var galleryproperties = "";
                for (var i = 0; i < data["results"].length; i++) {
                    //to get the right parent url
                    var url_index = 0;
                    while (url_index<arrUrl.length && arrUrl[url_index] != '#!') {
                        url_index += 1;
                    }
                    if (url_index == arrUrl.length) {
                        url_index -= 1;
                    } 
                    console.log(arrUrl);
                    
                    var link = "http://" + arrUrl.slice(2, url_index-1).join('/') + "/property?mlsname=CRMLS&listingid=" + data["results"][i]["listing_id"];
                    var imglink = apiurl + "/propertyphoto/CRMLS/" + data["results"][i]["listingkey_numeric"];

                    // print total count
                    $("#count-2134486574").text(data["count"] + " Results");

                    var template_data = {
                        "link": link,
                        "listingkey": data["results"][i]["listingkey_numeric"],
                        "address": data["results"][i]["streetname"],
                        "beds": data["results"][i]["beds"],
                        "baths": data["results"][i]["baths"],
                        "area": formatNumber(parseInt(data["results"][i]["area"])),
                        "yearbuilt": data["results"][i]["yearbuilt"],
                        "list_price": formatNumber(parseInt(data["results"][i]["list_price"])),
                        "pricepersquare": data["results"][i]["pricepersquare"],
                        "city": data["results"][i]["city"],
                        "coverimage": data["results"][i]["coverimage"],
                        "loadingimage": "",
                        "img_id": data["results"][i]["listingkey_numeric"],
                        "status": data["results"][i]["status"],
                        "listagent_firstname": data["results"][i]["listagent_firstname"],
                        "listagent_lastname": data["results"][i]["listagent_lastname"],
                        "listoffice_name": data["results"][i]["listoffice_name"],
                        "count": data["count"],
                    };
                    var html = template("test", template_data);
                    $("#gallery-properties").append(html);

                    if (template_data["coverimage"] != "") {
                        // already have img url
                        data_src = template_data["coverimage"];
                        //to https
                        
                        imghtml = "<img class=\"lazy photo gallery-photo\" src=\"\" data-src=\"" + data_src + "\" style=\"display: block;\"> ";
                        $('#' + template_data["listingkey"]).append(imghtml);
                        $('.lazy').lazy({
                            onError: function (element) {
                                //console.log('error loading ' + element.data('src'));
                                element.attr('src', nophoto_url);
                            },
                        });
                    } else {
                        // call img api on demand
                        $.get(imglink, function (coverimage, status) {
                            var i = 0;
                            // No img
                            if (coverimage["imgs"].length == 0) {
                                data_src = nophoto_url;
                            } else {
                                // the first one could be .pdf
                                while (coverimage["imgs"][i]["type"] != 'IMAGE' & i < coverimage["imgs"].length) {
                                    i++;
                                }
                                if (i == coverimage["imgs"].length) {
                                    data_src = nophoto_url; // No cover image
                                } else {
                                    data_src = coverimage["imgs"][i]["url"];
                                }
                            }
                            imghtml = "<img class=\"lazy photo gallery-photo\" src=\"\" data-src=\"" + data_src + "\"  style=\"display: block;\"> ";
                            $('#' + coverimage["listingkey"]).append(imghtml);
                            $('.lazy').lazy({
                                onError: function (element) {
                                    //console.log('error loading ' + element.data('src'));
                                    element.attr('src', nophoto_url);
                                }
                            });
                        });
                    }
                }

            });
        }

        $("img").error(function () {
            console.log("Image Error!");
        });

        // change hash when search-button click 
        $("#search-button-2134486574").click(function () {
            var urlhash = "!";
            // TODO: this should include zipcode, city and ... use autocomplete
            if ($("#text-input-2134486574").val()) {
                if (place.types) {
                    urlhash += "/srchtxt/" + place.name;
                    urlhash += "/type/" + place.types[0];
                } else {
                    urlhash += "/srchtxt/" + $("#text-input-2134486574").val();
                }
            }
            // button group
            if ($("#min-price-btn-2134486574").val()) {
                urlhash += "/minp/" + $("#min-price-btn-2134486574").val();
            }
            if ($("#max-price-btn-2134486574").val()) {
                urlhash += "/maxp/" + $("#max-price-btn-2134486574").val();
            }
            if ($("#beds-btn-2134486574").val()) {
                urlhash += "/beds/" + $("#beds-btn-2134486574").val();
            }
            if ($("#baths-btn-2134486574").val()) {
                urlhash += "/baths/" + $("#baths-btn-2134486574").val();
            }
            if ($("#sortby-btn-2134486574").val()) {
                urlhash += "/stby/" + $("#sortby-btn-2134486574").val();
            }
            if ($("#sortby-btn-2134486574").attr("sort-value") == "desc") {
                urlhash += "/desc/true";
            }
            console.log(urlhash);
            location.hash = urlhash;
        });
        // load result driver
        $(window).on('hashchange', function () {
            loadresults();
        });
        $(document).ready(function () {
            loadresults();
        });
    });