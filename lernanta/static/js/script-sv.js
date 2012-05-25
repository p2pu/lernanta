$(document).ready(function() {
    if ($('#id_start_date').length) {
        $('#id_start_date').datepicker($.datepicker.regional['sv']);
        $('#id_end_date').datepicker($.datepicker.regional['sv']);
    }
});
