CKEDITOR.plugins.add('prettify',
{
    init: function(editor)
    {
        var pluginName = 'prettify';
        var lang = editor.lang.common;
        var style = new CKEDITOR.style( editor.config.prettify );
        editor.addCommand( pluginName, new CKEDITOR.styleCommand( style ) );
        editor.ui.addButton('SyntaxHighlighting',
            {
                label: lang.prettify,
                command: pluginName,
                icon: CKEDITOR.getUrl(this.path + 'images/prettify.ico'),
            });
    }
});
