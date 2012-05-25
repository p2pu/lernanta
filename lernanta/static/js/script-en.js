$(document).ready(function() {
    if ($('#id_start_date').length) {
        $('#id_start_date').datepicker($.datepicker.regional['en']);
        $('#id_end_date').datepicker($.datepicker.regional['en']);
    }
});
