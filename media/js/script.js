
var createPostTextArea = function() {
    var counter = $('#create-post').find('div.post-char-count');
    $('#create-post').find('textarea').bind('keyup', function() {
        var max = 750;
        var count = max - $(this).val().length;
        counter.html(count);

        if (count < 0 || count >= max) {
            counter.addClass('danger');
            counter.removeClass('warning');
            $('#post-project-update').attr("disabled", "disabled");
            $('#post-update').attr("disabled", "disabled");
        } else if (count < 50) {
            counter.removeClass('danger');
            counter.addClass('warning');
            $('#post-project-update').removeAttr("disabled");
            $('#post-update').removeAttr("disabled");
        } else {
            counter.removeClass('danger');
            counter.removeClass('warning');
            $('#post-project-update').removeAttr("disabled");
            $('#post-update').removeAttr("disabled");
        }
    });

    $('#create-post').find('#fake-message-input').bind('focus', function() {
        $('#post-project-update').attr("disabled", "disabled");
        $('#post-update').attr("disabled", "disabled");
        counter.addClass('danger');
        counter.removeClass('warning');
        $('#create-post').addClass('expanded');
        $('#create-post').find('textarea').trigger('focus');
    });
};

var usernameHint = function() {
    var userurl = $('#username .hint b').html();
    $('#id_username').keyup(function() {
        $('#availability').removeClass('okay warning').html('');
        var val = (this.value) ? this.value : userurl;
        $(this).parent('.field').find('.hint b').html(val);
    }).keyup();
};

var usernameAvailability = function() {
    $('#id_username').bind('blur', function() {
        var $elem = $(this);
        if ($elem.val().length != 0) {
            $.ajax({
                url: '/ajax/check_username/',
                data: {
                    username: this.value
                },
                success: function() {
                    $('#availability').removeClass('okay')
                        .addClass('warning')
                        .html('not available');
                },
                error: function() {
                    $('#availability').removeClass('warning')
                        .addClass('okay')
                        .html('available');
                }
            });
        }
    });
};

var openidHandlers = function() {
    var oneClick = {
        'google': 'https://www.google.com/accounts/o8/id',
        'yahoo': 'https://yahoo.com',
        'myopenid': 'https://www.myopenid.com'
    };
    $.each(oneClick, function(key, value) {
        $('.openid_providers #' + key).bind('click', function(e) {
            e.preventDefault();
            $('#id_openid_identifier').val(value);
            $('#id_openid_identifier').parent().submit();
        });
    });
};

var loadMoreMessages = function() {
    $('a#inbox_more').bind('click', function(e) {
        e.preventDefault();
        var template = $('#message-template');
        var page = template.attr('page');
        var npages = template.attr('npages');
        var url = $(this).attr('href');
        $.getJSON(url, function(data) {
            $(data).each(function(i, value) {
                var msg = template.tmpl(value);
                msg.hide();
                $('#posts').append(msg);
                $('li.post-container:last').fadeIn(function() {
                    $('html').animate({
                        'scrollTop': $('a#inbox_more').offset().top
                    }, 200);
                });
            });
            nextPage = parseInt(page) + 1;
            template.attr('page', nextPage);
            if (nextPage > parseInt(npages)) {
                $('a#inbox_more').hide();
            }
            // update more link. very hacky :( 
            var href = $('a#inbox_more').attr('href');
            var newHref = href.substr(0, href.length - 2) + nextPage + '/';
            $('a#inbox_more').attr('href', newHref);
        });
    });
};

var attachFileUploadHandler = function($inputs) {
    var updatePicturePreview = function(path) {
        var $img = $('<img class="member-picture"></img>');
        $img.attr('src', path);
        $('p.picture-preview img').remove();
        $img.appendTo('p.picture-preview');
    };
    $(this).closest('form').removeAttr('enctype');
    $inputs.closest('fieldset').addClass('ajax-upload');
    $inputs.each(function() {
        $(this).ajaxSubmitInput({
            url: $(this).closest('form').attr('data-url'),
            beforeSubmit: function($input) {
                updatePicturePreview("/media/images/ajax-loader.gif");
                $options = {};
                $options.filename = $input.val().split(/[\/\\]/).pop();
                return $options;
            },
            onComplete: function($input, iframeContent, passJSON) {
                $input.closest('form')[0].reset();
                $input.trigger('clean');
                if (!iframeContent) {
                    return;
                }
                content = jQuery.parseJSON(iframeContent);
                updatePicturePreview("/media/" + content.filename);
            }
        });
    });
};

var batucada = {
    splash: {
        onload: function() {
        }
    },
    compose_message: {
        onload: function() {
            $('#id_recipient').autocomplete({
                source: '/ajax/following/',
                minLength: 2
            });
        }
    },
    create_profile: {
        onload: function() {
            usernameHint();
            usernameAvailability();
        }
    },
    signup: {
        onload: function(){
            usernameHint();
            usernameAvailability();
        }
    },
    signup_openid: {
        onload: function() {
            openidHandlers();
        }
    },
    signin_openid: {
        onload: function() {
            openidHandlers();
        }
    },
    dashboard: {
        onload: function() {
            createPostTextArea();
            $('#post-update').bind('click', function() {
                $('#post-status-update').submit();
            });
            $('a.activity-delete').bind('click', function(e) {
                $(e.target).parent().submit();
                return false;
            });
            $('.close_button').bind('click', function(e) {
                e.preventDefault();
                $('.welcome').animate({
                    opacity: 'hide',
                    height: 'hide',
                    paddingTop: 0,
                    paddingBottom: 0,
                    marginTop: 0,
                    marginBottom: 0
                }, 600, 'jswing', function() {
                    $.post('/broadcasts/hide_welcome/');
                });
            });
        }
    },
    project_landing: {
        onload: function() {
            createPostTextArea();
            $('#post-project-update').bind('click', function() {
                $('#post-project-status-update').submit();
            });
        }
    },
    challenge_landing: {
        onload: function() {
            createPostTextArea();
            $('#post-challenge').bind('click', function() {
                $('#post-challenge-summary').submit();
            });
        }
    },
    user_profile: {
        onload: function() {
            createPostTextArea();
            $('#post-user-update').bind('click', function() {
                $('#post-user-status-update').submit();
            });
        }
    },
    profile_edit: {
        onload: function() {
            var $inputs = $('input[type=file]');
            if ($inputs) {
                attachFileUploadHandler($inputs);
            }
            openidHandlers();
        }
    },
    project_edit: {
        onload: function() {
            var $inputs = $('input[type=file]');
            if ($inputs) {
                attachFileUploadHandler($inputs);
            }
        }
    },
    school_edit: {
        onload: function() {
            var $inputs = $('input[type=file]');
            if ($inputs) {
                attachFileUploadHandler($inputs);
            }
        }
    },
    signup: {
        onload: function() {
            var $inputs = $('input[type=file]');
            if ($inputs) {
                attachFileUploadHandler($inputs);
            }
        }
    },
    inbox: {
        onload: function() {
            loadMoreMessages();
        }
    },
};


$(document).ready(function() {
    // dispatch per-page onload handlers 
    var ns = window.batucada;
    var bodyId = document.body.id;
    if (ns && ns[bodyId] && (typeof ns[bodyId].onload == 'function')) {
        ns[bodyId].onload();
    }
    // attach handlers for elements that appear on most pages
     $('#main-nav').find('li.menu').bind('mouseover mouseout', function(event) {
        $(this).toggleClass('open');
    });

    $('#user-nav').find('li.menu').bind('mouseover mouseout', function(event) {
        $(this).toggleClass('open');
    });

    // modals using jQueryUI dialog
    $('.button.openmodal').live('click', function(){
        var url = this.href;
        var selector = '.modal';
        var urlFragment =  url + ' ' + selector;
        var dialog = $('<div></div>').appendTo('body');
        // load remote content
        dialog.load(
            urlFragment,
            function (responseText, textStatus, XMLHttpRequest) {
                dialog.dialog({
                    draggable: true
                });
            }
        );
        // prevent the browser to follow the link
        return false;
    });
    
    $('#id_start_date').datepicker();
    $('#id_end_date').datepicker();

    $.farbtastic('#headers_colorpicker', { callback: '#id_headers_color', width: 100, heigth: 100 });
    $.farbtastic('#headers_light_colorpicker', { callback: '#id_headers_color_light', width: 100, heigth: 100 });
    $.farbtastic('#background_colorpicker', { callback: '#id_background_color', width: 100, heigth: 100 });
    $.farbtastic('#menu_colorpicker', { callback: '#id_menu_color', width: 100, heigth: 100 });
    $.farbtastic('#menu_light_colorpicker', { callback: '#id_menu_color_light', width: 100, heigth: 100 });
    $.farbtastic('#about_us_footnote_colorpicker', { callback: '#id_about_us_footnote_color', width: 100, heigth: 100 });
    $.farbtastic('#contact_us_footnote_colorpicker', { callback: '#id_contact_us_footnote_color', width: 100, heigth: 100 });
    $.farbtastic('#license_info_footnote_colorpicker', { callback: '#id_license_info_footnote_color', width: 100, heigth: 100 });

    prettyPrint();

    // disable submit button on form submit
    $('form').submit(function(){
        $(this).find('input[type=submit]').attr('disabled', 'disabled');
        $(this).find('button[type=submit]').attr('disabled', 'disabled');
        $(this).find('#previewButton').removeAttr('disabled');
    });
});

// Recaptcha
var RecaptchaOptions = { theme : 'custom' };

$('#recaptcha_different').click(function(e) {
    e.preventDefault();
    Recaptcha.reload();
});

$('#recaptcha_audio').click(function(e) {
    e.preventDefault();
    Recaptcha.switch_type('audio');
});

$('#recaptcha_help').click(function(e) {
    e.preventDefault();
    Recaptcha.showhelp();
});


$('#send-badges').bind('submit', function(e) {
  var $this = $(this),
      csrfname = 'csrfmiddlewaretoken',
      csrfvalue = $this.find('input[name="'+csrfname+'"]').val(),
      button = $this.find('input[type="submit"]'),
      msgfield = $this.find('span.message'),
      email = $this.find('input[name="email"]').val(),
      postdata = {};
  e.preventDefault();

  if ($this.data('submitted')) { return false; }
  $this.data('submitted', true);
  
  button.hide();
  msgfield.html('Sending...');
  
  postdata[csrfname] = csrfvalue
  $.ajax({
    type: 'POST',
    url: '/badges/send', //don't hardcode this in the future.
    data: postdata,
    success: function(response){
      var msg = msgfield.html();
      if (response['status'] == 'accepted') {
        msg += ' Success! <br/>You can now go to <a href="http://alpha.badgehub.org">' +
          'http://alpha.badgehub.org</a> and view your badges.<br/>' +
          'Be sure to log in using the email <strong>' + email + '</strong>';
      } else {
        msg += "Error :(<br/> Something has gone wrong. " +
          "Hopefully it's temporary – please try again in a few minutes.";
      }
      msgfield.html(msg);
    },
    error: function(response){
      var msg = msgfield.html();
      msg += " Error :(<br/> Something has gone wrong. <br/>" +
        "Hopefully it's temporary – please try again in a few minutes.";
      msgfield.html(msg);
    }
  })
  return false;
})