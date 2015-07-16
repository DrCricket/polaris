city_to_locality = {
    'Mumbai': ['Powai', 'Bandra'],
    'Delhi': ['Hauz Khas', 'Connaught Place']
};

locality_to_sublocality = {
    'Powai': ['Chandivali', 'Hiranandani'],
    'Bandra': ['Bandstand', 'Bandra Kurla Complex'],
    'Hauz Khas': ['Hauz Khas Village', 'Saket'],
    'Connaught Place': ['Rajiv Chowk', 'Palika Bazaar']
};

data = []

$(document).ready(function() {

    $('.selectpicker').selectpicker();

    // $('<div id="overlay"/>').css({
    //     position: 'fixed',
    //     top: 0,
    //     left: 0,
    //     display: 'block',
    //     width: $(window).width() + 'px',
    //     height: $(window).height() + 'px',
    //     background: 'url(/static/images/loader.svg) no-repeat center'
    // }).hide().appendTo('body');

    $('<div id="overlay"/>').css({
        position: 'fixed',
        top: 0,
        left: 0,
        display: 'block',
        width: $(window).width() + 'px',
        height: $(window).height() + 'px',
        background: 'url(/static/gif/ajax-loader-circle.gif) no-repeat center'
    }).hide().appendTo('body');

    function getCities(service) {
        $('#overlay').show();
        console.log('Getting cities... for service '+service.toLowerCase());
        $('#select-city').selectpicker('deselectAll');
        $('#select-city').empty();
        $('#select-locality').selectpicker('deselectAll');
        $('#select-locality').empty();
        $('#select-sublocality').selectpicker('deselectAll');
        $('#select-sublocality').empty();

        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        $.ajax({
            type: "GET",
            url: "/polaris/",
            data: {
                'name': 'getCities',
                'service': service.toLowerCase()
            },
            success: function (data) {
                console.log('Ajax success: loaded cities');
                console.log(data);
                _.each(data, function(city_data) {
                    new_html += '<option value="' + city_data['id'] + '">' + city_data['name'] + '</option>';
                });
                $('#select-city').html(new_html);
                $('#select-city').selectpicker('refresh');
                $('#overlay').hide();
            },
            error: function (err) {
                console.log("Ajax: Get error for cities:", err);
                $('#overlay').hide();
            }
        });
    }

    function getLocalities(service,city_id) {
        $('#overlay').show();
        console.log('Getting localities...for service and city '+service.toLowerCase()+'  '+city_id);
        $('#select-locality').selectpicker('deselectAll');
        $('#select-locality').empty();
        $('#select-sublocality').selectpicker('deselectAll');
        $('#select-sublocality').empty();

        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        if (city_id == 0) {
            $('#select-locality').html(new_html);
            $('#select-locality').selectpicker('refresh');
            $('#overlay').hide();
        } else {
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'getLocalities',
                    'service': service.toLowerCase(),
                    'city_id': city_id
                },
                success: function (data) {
                    console.log('Ajax success: loaded localities');
                    console.log(data);
                    _.each(data, function(locality_data) {
                        new_html += '<option value="' + locality_data['id'] + '">' + locality_data['name'] + '</option>';
                    });
                    $('#select-locality').html(new_html);
                    $('#select-locality').selectpicker('refresh');
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for localities:", err);
                    $('#overlay').hide();
                }
            });
        }
    }

    function getSublocalities(service, locality_id) {
        $('#overlay').show();
        console.log('Getting sublocalities...for service and locality '+service.toLowerCase()+'  '+locality_id);
        $('#select-sublocality').selectpicker('deselectAll');
        $('#select-sublocality').empty();
        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        if (locality_id == 0) {
            $('#select-sublocality').html(new_html);
            $('#select-sublocality').selectpicker('refresh');
            $('#overlay').hide();
        } else if (locality_id != '') {
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'getSublocalities',
                    'service': service.toLowerCase(),
                    'locality_id': locality_id
                },
                success: function (data) {
                    console.log('Ajax success: loaded sublocalities');
                    console.log(data);
                    _.each(data, function(sublocality_data) {
                        new_html += '<option value="' + sublocality_data['id'] + '">' + sublocality_data['name'] + '</option>';
                    });
                    $('#select-sublocality').html(new_html);
                    $('#select-sublocality').selectpicker('refresh');
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for sublocalities:", err);
                    $('#overlay').hide();
                }
            });
        }
    }

    function full_export(granularity_level){
        console.log('exporting data for granularity_level ', granularity_level)
        var for_export = true;
        service = $('#select-service').selectpicker('val').toLowerCase();
        city = $('#select-city').selectpicker('val');
        locality = $('#select-locality').selectpicker('val');
        sublocality = $('#select-sublocality').selectpicker('val');
        if ( (service != null && service != '') && (city != null && city != '') ) {
            
            if ( (locality != null && locality != '' ) && (sublocality != null && sublocality != '') ) {
                fill_data_granular_to_sublocality(service, city, locality, sublocality, for_export)
            }
            else if ( ( locality != null && locality != '' )  && (sublocality === null || sublocality === '') ) {
                fill_data_granular_to_locality(service, city, locality, for_export)
            }
            else if ( ( locality === null || locality === '' ) && ( sublocality === null || sublocality === '' ) ) {
                fill_data_granular_to_city(service, city, for_export)
            }
            else {
                alert('Fill the fields properly and then re-submit')    
            }
            
            // }      
        }
        else {
            alert('You have to select something for service and city and then re-submit')
        }
    }

    function JSONToCSVConvertor(JSONData, ReportTitle, ShowLabel) {
        //If JSONData is not an object then JSON.parse will parse the JSON string in an Object
        var arrData = typeof JSONData != 'object' ? JSON.parse(JSONData) : JSONData;
        
        var CSV = '';    
        //Set Report title in first row or line
        
        CSV += ReportTitle + '\r\n\n';

        //This condition will generate the Label/Header
        if (ShowLabel) {
            var row = "";
            
            //This loop will extract the label from 1st index of on array
            // for (var index in arrData[0]) {
                
            //     //Now convert each value to string and comma-seprated
            //     row += index + ',';
            // }

            // row = row.slice(0, -1);
            row = "city,locality,sublocality,demand,supply,ds_gap,conversions,leads_per_user"
            //append Label row with line break
            CSV += row + '\r\n';
        }
        indices = "city,locality,sublocality,demand,supply,ds_gap,conversions,leads_per_user".split(',')
        //1st loop is to extract each row
        for (var i = 0; i < arrData.length; i++) {
            var row = "";
            
            //2nd loop will extract each column and convert it in string comma-seprated
            for (var index in indices) {
                row += '"';
                if(typeof(arrData[i][indices[index]])!='undefined')
                    row+= arrData[i][indices[index]];
                else
                    row += '-';
                row += '",';
            }

            row.slice(0, row.length - 1);
            
            //add a line break after each row
            CSV += row + '\r\n';
        }

        if (CSV == '') {        
            alert("Invalid data");
            return;
        }   
        
        //Generate a file name
        var fileName = "MyReport_";
        //this will remove the blank-spaces from the title and replace it with an underscore
        fileName += ReportTitle.replace(/ /g,"_");   
        
        //Initialize file format you want csv or xls
        var uri = 'data:text/csv;charset=utf-8,' + escape(CSV);
        
        // Now the little tricky part.
        // you can use either>> window.open(uri);
        // but this will not work in some browsers
        // or you will not get the correct file extension    
        
        //this trick will generate a temp <a /> tag
        var link = document.createElement("a");    
        link.href = uri;
        
        //set the visibility hidden so it will not effect on your web-layout
        link.style = "visibility:hidden";
        link.download = fileName + ".csv";
        
        //this part will append the anchor tag and remove it after automatic click
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function fill_data_granular_to_sublocality(service, city, locality, sublocality, for_export){
        if(for_export){
            $('#overlay').show();
            console.log('exporting data granular to sublocality...for service and city and locality and sublocality '+service.toLowerCase()+'  '+city+'  '+locality+'  '+sublocality);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'export_ds_data_granular_to_sublocality',
                    'service': service,
                    'city': city,
                    'locality': locality,
                    'sublocality': sublocality
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to sublocalities');
                    if(data)
                        JSONToCSVConvertor(data, "Demand Supply Data", true);
                    else
                        return;
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to sublocalities:", err);
                    $('#overlay').hide();
                }
            });
        }
        else{
            $('#overlay').show();
            console.log('filling data granular to sublocality...for service and city and locality and sublocality '+service.toLowerCase()+'  '+city+'  '+locality+'  '+sublocality);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'ds_data_granular_to_sublocality',
                    'service': service,
                    'city': city,
                    'locality': locality,
                    'sublocality': sublocality
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to sublocalities');
                    $('#table').bootstrapTable('load', data);
                    $('#table-div').show();
                    $('.fixed-table-toolbar').find('#full_export').remove();
                    $('.fixed-table-toolbar').append('<div class="pull-right search"><button type="button" class="btn btn-primary center-block" id="full_export" style="margin-right: 10px;">Full csv  export</button></div>');
                    $('#full_export').on('click', function(){full_export('sublocality')});
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to sublocalities:", err);
                    $('#overlay').hide();
                }
            });
        }
    }
    
    function fill_data_granular_to_locality(service, city, locality, for_export){
        if(for_export){
            $('#overlay').show();
            console.log('exporting data granular to locality...for service and city and locality '+service.toLowerCase()+'  '+city+'  '+locality);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'export_ds_data_granular_to_locality',
                    'service': service,
                    'city': city,
                    'locality': locality
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to localities');
                    if(data)
                        JSONToCSVConvertor(data, "Demand Supply Data", true);
                    else
                        return;
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to localities:", err);
                    $('#overlay').hide();
                }
            });
        }
        else{
            $('#overlay').show();
            console.log('filling data granular to locality...for service and city and locality '+service.toLowerCase()+'  '+city+'  '+locality);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'ds_data_granular_to_locality',
                    'service': service,
                    'city': city,
                    'locality': locality
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to localities');
                    $('#table').bootstrapTable('load', data);
                    $('#table-div').show();
                    $('.fixed-table-toolbar').find('#full_export').remove();
                    $('.fixed-table-toolbar').append('<div class="pull-right search"><button type="button" class="btn btn-primary center-block" id="full_export" style="margin-right: 10px;">Full csv  export</button></div>');
                    $('#full_export').on('click', function(){full_export('locality')});
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to localities:", err);
                    $('#overlay').hide();
                }
            });
        }
    }

    function fill_data_granular_to_city(service, city, for_export){
        if(for_export){
            $('#overlay').show();
            console.log('exporting data granular to city...for service and city and '+service.toLowerCase()+'  '+city);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'export_ds_data_granular_to_city',
                    'service': service,
                    'city': city
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to sublocalities');
                    if(data)
                        JSONToCSVConvertor(data, "Demand Supply Data", true);
                    else
                        return;
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to sublocalities:", err);
                    $('#overlay').hide();
                }
            });
        }
        else{
            $('#overlay').show();
            console.log('filling data granular to city...for service and city and '+service.toLowerCase()+'  '+city);
            $.ajax({
                type: "GET",
                url: "/polaris/",
                data: {
                    'name': 'ds_data_granular_to_city',
                    'service': service,
                    'city': city
                },
                success: function (data) {
                    console.log('Ajax success: got ds data granular to sublocalities');
                    $('#table').bootstrapTable('load', data);
                    $('#table-div').show();
                    $('.fixed-table-toolbar').find('#full_export').remove();
                    $('.fixed-table-toolbar').append('<div class="pull-right search"><button type="button" class="btn btn-primary center-block" id="full_export" style="margin-right: 10px;">Full csv  export</button></div>');
                    $('#full_export').on('click', function(){full_export('city')});
                    $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for ds data granular to sublocalities:", err);
                    $('#overlay').hide();
                }
            });
        }
    }


    $('#select-service').on('change', function() {
        var service = $(this).selectpicker('val');
        getCities(service);
    });

    $('#select-city').on('change', function() {
        city_id = $(this).selectpicker('val');
        service = $("#select-service").selectpicker('val');
        getLocalities(service,city_id);
    });

    $('#select-locality').on('change', function() {
        locality_id = $(this).selectpicker('val');
        service = $("#select-service").selectpicker('val');
        getSublocalities(service, locality_id);
    });

    $('#clear-locality').on('click', function() {
        $('#select-locality').selectpicker('deselectAll');
        $('#select-sublocality').selectpicker('deselectAll');
    });

    $('#clear-sublocality').on('click', function() {
        $('#select-sublocality').selectpicker('deselectAll');
    });

    $('#submit').on('click', function() {
        var for_export = false;
        service = $('#select-service').selectpicker('val').toLowerCase();
        city = $('#select-city').selectpicker('val');
        locality = $('#select-locality').selectpicker('val');
        sublocality = $('#select-sublocality').selectpicker('val');
        if ( (service != null && service != '') && (city != null && city != '') ) {
            
            if ( (locality != null && locality != '' ) && (sublocality != null && sublocality != '') ) {
                fill_data_granular_to_sublocality(service, city, locality, sublocality, for_export)
            }
            else if ( ( locality != null && locality != '' )  && (sublocality === null || sublocality === '') ) {
                fill_data_granular_to_locality(service, city, locality, for_export)
            }
            else if ( ( locality === null || locality === '' ) && ( sublocality === null || sublocality === '' ) ) {
                fill_data_granular_to_city(service, city, for_export)
            }
            else {
                alert('Fill the fields properly and then re-submit')    
            }
            
            // }      
        }
        else {
            alert('You have to select something for service and city and then re-submit')
        }
        
    });
        
});