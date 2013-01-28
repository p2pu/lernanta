( function ( $ ) {
    $.fn.daveDown = function (){
        var inputId = this.attr('id');
        $("<div id='" + inputId + "-wmd-button-bar'></div>").insertBefore("#" + inputId);
        $("<div id='" + inputId + "-wmd-preview'></div>").insertAfter("#" + inputId);
        var converter1 = Markdown.getSanitizingConverter();
        var editor1 = new Markdown.Editor(converter1, inputId);
        editor1.run();
    };
})( jQuery );
