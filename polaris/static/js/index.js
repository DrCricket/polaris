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

    $('<div id="overlay"/>').css({
        position: 'fixed',
        top: 0,
        left: 0,
        display: 'block',
        width: $(window).width() + 'px',
        height: $(window).height() + 'px',
        background: 'url(/static/images/loader.svg) no-repeat center'
    }).hide().appendTo('body');

    function getCities() {
        // $('#overlay').show();
        console.log('Getting cities...');
        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        $.ajax({
            type: "GET",
            url: "/polaris/",
            data: {
                'name': 'getCities'
            },
            success: function (data) {
                console.log('Ajax success: loaded cities');
                console.log(data);
                _.each(data, function(city_data) {
                    new_html += '<option value="' + city_data['id'] + '">' + city_data['name'] + '</option>';
                });
                $('#select-city').html(new_html);
                $('#select-city').selectpicker('refresh');
                // $('#overlay').hide();
            },
            error: function (err) {
                console.log("Ajax: Get error for cities:", err);
                // $('#overlay').hide();
            }
        });
    }

    // Get cities when document is ready
    getCities();

    function getLocalities(city_id) {
        // $('#overlay').show();
        console.log('Getting localities...');
        $('#select-locality').empty();
        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        if (city_id == 0) {
            $('#select-locality').html(new_html);
            $('#select-locality').selectpicker('refresh');
        } else {
            $.ajax({
                type: "GET",
                url: "/",
                data: {
                    'name': 'getLocalities'
                },
                success: function (data) {
                    console.log('Ajax success: loaded localities');
                    console.log(data);
                    _.each(data, function(locality_data) {
                        new_html += '<option value="' + locality_data['id'] + '">' + locality_data['name'] + '</option>';
                    });
                    $('#select-locality').html(new_html);
                    $('#select-locality').selectpicker('refresh');
                    // $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for localities:", err);
                    // $('#overlay').hide();
                }
            });
        }
    }

    function getSublocalities(locality_id) {
        // $('#overlay').show();
        console.log('Getting sublocalities...');
        $('#select-sublocality').empty();
        new_html = '<option value="0" data-content="<strong>All</strong>">All</option>';
        if (locality_id == 0) {
            $('#select-sublocality').html(new_html);
            $('#select-sublocality').selectpicker('refresh');
        } else if (locality_id != '') {
            $.ajax({
                type: "GET",
                url: "/",
                data: {
                    'name': 'getSublocalities'
                },
                success: function (data) {
                    console.log('Ajax success: loaded sublocalities');
                    console.log(data);
                    _.each(data, function(sublocality_data) {
                        new_html += '<option value="' + sublocality_data['id'] + '">' + sublocality_data['name'] + '</option>';
                    });
                    $('#select-sublocality').html(new_html);
                    $('#select-sublocality').selectpicker('refresh');
                    // $('#overlay').hide();
                },
                error: function (err) {
                    console.log("Ajax: Get error for sublocalities:", err);
                    // $('#overlay').hide();
                }
            });
        }
    }

    $('#select-city').on('change', function() {
        city_id = $(this).selectpicker('val');
        getLocalities(city_id);
    });

    $('#select-locality').on('change', function() {
        locality_id = $(this).selectpicker('val');
        getSublocalities(locality_id);
    });

    $('#clear-locality').on('click', function() {
        $('#select-locality').selectpicker('deselectAll');
        $('#select-sublocality').selectpicker('deselectAll');
    });

    $('#clear-sublocality').on('click', function() {
        $('#select-sublocality').selectpicker('deselectAll');
    });

    $('#submit').on('click', function() {
        service = $('#select-service').selectpicker('val');
        city = $('#select-city').selectpicker('val');
        $('label[for=select-service]').removeClass();
        $('label[for=select-city]').removeClass();
        // if (!(service || city)) {
        //     $('label[for=select-service]').addClass('animated shake');
        //     $('label[for=select-city]').addClass('animated shake');
        // } else if (!(service)) {
        //     $('label[for=select-service]').addClass('animated shake');
        // } else if (!(city)) {
        //     $('label[for=select-city]').addClass('animated shake');
        // } else {
            locality = $('#select-locality').selectpicker('val');
            sublocality = $('#select-sublocality').selectpicker('val');
            localities = _.find(city_to_locality, function (localities, city) {
                return city == city;
            })
            if (locality) {

            }
            if (sublocality) {

            }
            $('#table').bootstrapTable({
                load: data
            });
            $('#table-div').show();
        // }
    });

});