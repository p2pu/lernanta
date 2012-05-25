CKEDITOR.plugins.add('embed',
{
    init: function(editor)
    {
        var pluginName = 'embed';
        CKEDITOR.dialog.add(pluginName, this.path + 'dialogs/embed.js');
        editor.addCommand(pluginName, new CKEDITOR.dialogCommand(pluginName));
        editor.ui.addButton('Embed',
            {
                label: 'Embed',
                command: pluginName,
                icon: CKEDITOR.getUrl(this.path + 'images/embed.png'),
            });
    }
});
