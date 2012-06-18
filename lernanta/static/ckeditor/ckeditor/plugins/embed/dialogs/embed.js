
CKEDITOR.dialog.add( 'embed', function( editor )
{
	return {
		title : 'Embed',
		minWidth : 350,
		minHeight : 140,
		onShow : function()
		{
            
		},
		onOk : function()
		{
            editor.insertText('[embed:');
            editor.insertText(this.getValueOf( 'info', 'url' ));
            editor.insertText(']');
		},
		contents : [
			{
				id : 'info',
				label : 'Embed',
				title : 'Embed',
				startupFocus : 'url',
				elements : [
					{
						id : 'url',
						type : 'text',
						label : 'URL (<u><a target="_blank" href="http://embed.ly/providers" style="color:#0000cd;">help</a></u>)',
						setup : function( element )
						{

						},
						commit : function( data )
						{

						}
					}
				]
			}
		]
	};
});
