var createPostTextArea = function() {
    var counter = $('#create-post').find('div.post-char-count');
    $('#create-post').find('textarea').bind('keyup', function() {
        var max = 750;
        var count = max - $(this).val().length;
        counter.html(count);

        if (count < 0) {
            counter.addClass('danger');
            counter.removeClass('warning');
            disableFields();
        } else if (count < 50) {
            counter.removeClass('danger');
            counter.addClass('warning');
            removeDisabledAttr();
        } else if (count == max) {
            counter.removeClass('danger');
            counter.removeClass('warning');
            disableFields();
        } else {
            counter.removeClass('danger');
            counter.removeClass('warning');
            removeDisabledAttr();
        }
    });

    $('#create-post').find('#fake-message-input').bind('focus', function() {
        disableFields();
        counter.removeClass('warning');
        $('#create-post').addClass('expanded');
        $('#create-post').find('textarea').trigger('focus');
    });

    function disableFields(){
        $('#post-project-update').attr("disabled", "disabled");
        $('#post-update').attr("disabled", "disabled");
    }

    function removeDisabledAttr(){
        $('#post-project-update').removeAttr("disabled");
        $('#post-update').removeAttr("disabled");
    }
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
                updatePicturePreview("/static/images/ajax-loader.gif");
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

function carousel_itemLoadCallback(url, carousel, state) {

    if (carousel.has(carousel.first, carousel.last)) {
        return;
    }

    $.get(url, {first: carousel.first, last: carousel.last}, function(data) {
        carousel_itemAddCallback(carousel, carousel.first, carousel.last, data);
    });
};

function carousel_itemAddCallback(carousel, first, last, data) {
    carousel.size(data['total']);

    $.each(data['items'], function(index, item) {
        carousel.add(first + index, item);
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

	// initialize and set trunk8 plugin
	$('.truncate-to-1-line').trunk8({
	   lines: 1
	});

	$('.truncate-to-2-lines').trunk8({
	   lines: 2
	});

	$('.truncate-to-3-lines').trunk8({
	   lines: 3
	});

	$('.truncate-to-4-lines').trunk8({
	   lines: 4
	});

	$('.truncate-to-5-lines').trunk8({
	   lines: 5
	});

	$('.truncate-to-6-lines').trunk8({
	   lines: 6
	});

	$('.truncate-to-7-lines').trunk8({
	   lines: 7
	});

	$('.truncate-to-8-lines').trunk8({
	   lines: 8
	});

	$('.truncate-to-9-lines').trunk8({
	   lines: 9
	});

	$('.truncate-to-10-lines').trunk8({
	   lines: 10
	});

    $('li.contribute-nav').click(function(){
    	var number = $(this).index();
    	$('li.contribute-item').hide().eq(number).fadeIn('slow');
    	$(this).toggleClass('active inactive');
    	$('li.contribute-nav').not(this).removeClass('active').addClass('inactive');
    });
    if ($('li.contribute-item').length) {
    	$('li.contribute-item').not(':first').hide();
    }

    if ($('#id_start_date').length) {
        $('#id_start_date').datepicker();
        $('#id_end_date').datepicker();
    }

    if ($('#id_duration').length) {
        $('#id_duration').spinner({min:0, max:9000, step:1, places:0});
    }

    // Now using twitter bootstrap progressbar
    if ($('.project-kind-challenge #task_list_wall #progressbar').length) {
        var $tasks_progressbar = $(".project-kind-challenge #task_list_wall #progressbar");
        var percentage_done = (completed_count / total_count) * 100;
        $tasks_progressbar.find('.bar').css('width', percentage_done + '%');
        // var progressbar_value = $(".project-kind-challenge #task_list_wall #progressbar").attr('value');
        // $(".project-kind-challenge #task_list_wall #progressbar").progressbar({'value': parseInt(progressbar_value)});
    }

    if ( $('#other-badges').length ) {
        var $carousel_list = $(this).find('.carousel');
        var carousel_callback_url = $(this).find('.carousel-callback').attr('href');
        function other_badges_carousel_itemLoadCallback (carousel, state) {
            carousel_itemLoadCallback(carousel_callback_url, carousel, state);
        };
        $carousel_list.jcarousel({
            // Uncomment the following option if you want items
            // which are outside the visible range to be removed
            // from the DOM.
            // Useful for carousels with MANY items.

            // itemVisibleOutCallback: {onAfterAnimation: function(carousel, item, i, state, evt) { carousel.remove(i); }},
            itemLoadCallback: other_badges_carousel_itemLoadCallback
        });
    }

    if ( $('#task-body a.external-task').length ) {
        var $external_task = $('#task-body a.external-task');
        $external_task.find('span.external-task-text').text($external_task.attr('title'));
        $external_task.show();
    }

    if ( $('#task-body-preview a.external-task').length ) {
        var $external_task = $('#task-body-preview a.external-task');
        $external_task.find('span.external-task-text').text($external_task.attr('title'));
        $external_task.show();
    }

    if ($('#headers_colorpicker').length) {
        $.farbtastic('#headers_colorpicker', { callback: '#id_headers_color', width: 100, heigth: 100 });
        $.farbtastic('#headers_light_colorpicker', { callback: '#id_headers_color_light', width: 100, heigth: 100 });
        $.farbtastic('#background_colorpicker', { callback: '#id_background_color', width: 100, heigth: 100 });
        $.farbtastic('#menu_colorpicker', { callback: '#id_menu_color', width: 100, heigth: 100 });
        $.farbtastic('#menu_light_colorpicker', { callback: '#id_menu_color_light', width: 100, heigth: 100 });
    }

    prettyPrint();
    $('.richtext_section').each(function(index, value) {
       AMprocessNode(value);
    });

    // disable submit button on form submit
    $('form').submit(function(){
        $(this).find('input[type=submit]').attr('disabled', 'disabled');
        $(this).find('button[type=submit]').attr('disabled', 'disabled');
        $(this).find('#previewButton').removeAttr('disabled');
        $(this).find('#editModeButton').removeAttr('disabled');
        $(this).find('#addPageButton').removeAttr('disabled');
        $(this).find('#finalSaveButton').removeAttr('disabled');
    });

    if ($('#task_list_wall_toogle').length) {
        $( "#task_list_wall_toogle" ).buttonset();
    }

    if ($('#submissions-list-toogle').length) {
        $( "#submissions-list-toogle" ).buttonset();
    }

        if ($('#projects-reviews-list-toggle').length) {
        $( "#projects-reviews-list-toggle" ).buttonset();
    }

    if ($(".challenge-set-modal-action").length) {
        $(".challenge-set-modal-action").fancybox({
          'titlePosition'       : 'inside',
          'transitionIn'        : 'none',
          'transitionOut'       : 'none'
        });
    }
    if ( $('#learn').length ) {
        enableLearn();
    }

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

$('.messages li.error .closeNotification, .messages li.success .closeNotification, .messages li.info .closeNotification').click(function () {
    $(this).parent().fadeOut("fast");
});

$(".project-kind-challenge #task_list_wall #task_list_wall_toogle #radio1").click(function(){
    $('.project-kind-challenge #task_list_wall #project_wall_section').hide();
    $('.project-kind-challenge #task_list_wall #task_list_section').show();
    $('.project-kind-challenge #task_list_wall #progress').show();
});

$(".project-kind-challenge #task_list_wall #task_list_wall_toogle #radio2").click(function(){
    $('.project-kind-challenge #task_list_wall #task_list_section').hide();
    $('.project-kind-challenge #task_list_wall #progress').hide();
    $('.project-kind-challenge #task_list_wall #project_wall_section').show();
});

$("#submissions-list-toogle #radio1").click(function(){
    $('#submissions-list #awarded-submission-list').hide();
    $('#submissions-list #my-submissions-list').hide();
    $('#submissions-list #pending-submission-list').show();
});

$("#submissions-list-toogle #radio2").click(function(){
    $('#submissions-list #pending-submission-list').hide();
    $('#submissions-list #my-submissions-list').hide();
    $('#submissions-list #awarded-submission-list').show();
});

$("#submissions-list-toogle #radio3").click(function(){
    $('#submissions-list #pending-submission-list').hide();
    $('#submissions-list #awarded-submission-list').hide();
    $('#submissions-list #my-submissions-list').show();
});

$("#projects-reviews-list-toggle #radio1").click(function(){
    $('#projects-reviews-list #reviewed-projects-reviews-list').hide();
    $('#projects-reviews-list #new-projects-reviews-list').show();
});

$("#projects-reviews-list-toggle #radio2").click(function(){
    $('#projects-reviews-list #new-projects-reviews-list').hide();
    $('#projects-reviews-list #reviewed-projects-reviews-list').show();
});

$(".project-kind-challenge #task_list_section .taskCheckbox").click(function(){
    var $task_completion_checkbox = $(this);
    var $task_completion_form = $task_completion_checkbox.parent();
    $task_completion_form.parent().toggleClass("taskSelected");
    var url = $task_completion_form.attr('action');
    $task_completion_checkbox.attr('disabled', 'disabled');
    $.post(url, $task_completion_form.serialize(), function(data) {
        var total_count = data['total_count'];
        var completed_count = data['completed_count'];
        var progressbar_value = data['progressbar_value'];
        $(".project-kind-challenge #task_list_wall #total_count").html(total_count);
        $(".project-kind-challenge #task_list_wall #completed_count").html(completed_count);
        var $tasks_progressbar = $(".project-kind-challenge #task_list_wall #progressbar");
        var percentage_done = (completed_count / total_count) * 100;
        $tasks_progressbar.find('.bar').css('width', percentage_done + '%');
        // $tasks_progressbar.progressbar("option", "value", progressbar_value);
        $task_completion_checkbox.removeAttr('disabled');
        var $tasks_completed_msg = $('.project-kind-challenge .tasks-completed-msg');
        if( progressbar_value == "100" ) {
            $tasks_completed_msg.fadeIn('fast');
            $(window).scrollTop();
        } else {
            $tasks_completed_msg.fadeOut('fast');
        }
    });
});

var submitTaskFooterToggleTaskCompletion = function() {
    var $task_completion_form = $(this);
    var $task_footer = $task_completion_form.parent();
    var url = $task_completion_form.attr('action');
    $.post(url, $task_completion_form.serialize(), function(data) {
        var progressbar_value = data['progressbar_value'];
        var upon_completion_redirect = data['upon_completion_redirect'];
        var stay_on_page = data['stay_on_page'];
        var toggle_task_completion_form_html = data['toggle_task_completion_form_html'];
        $task_footer.html(toggle_task_completion_form_html);
        if( !stay_on_page && progressbar_value == "100" ) {
            window.location.href = upon_completion_redirect;
        }
        $task_footer.find('button').removeAttr('disabled');
        $new_task_completion_form = $task_footer.find('form#task-footer-toggle-task-completion-form');
        $new_task_completion_form.submit(submitTaskFooterToggleTaskCompletion);
        $new_link_submit_form = $task_footer.find('#task-footer-after-completed form');
        $new_link_submit_form.submit(submitTaskFooterAfterCompletionForm);
    });
    return false;
};

var submitTaskFooterAfterCompletionForm = function() {
    var $link_submit_form = $(this);
    var url = $link_submit_form.attr('action');
    var $task_footer = $link_submit_form.parent().parent();
    var $content_textarea = $link_submit_form.find('textarea')
    if ($content_textarea.length && CKEDITOR.instances['id_content']) {
        $content_textarea.text(CKEDITOR.instances['id_content'].getData());
    }
    var post_data = $link_submit_form.serialize();
    $.post(url, post_data, function(data) {
        if ( 'posted_link_comment_html' in data ) {
            var $comment_placeholder = $('.project-kind-challenge #task-link-submit-jquery-comment-placeholder');
            $comment_placeholder.html(data['posted_link_comment_html']);
        }
        var progressbar_value = data['progressbar_value'];
        var upon_completion_redirect = data['upon_completion_redirect'];
        var stay_on_page = data['stay_on_page'];
        var toggle_task_completion_form_html = data['toggle_task_completion_form_html'];
        $task_footer.html(toggle_task_completion_form_html);
        if( !stay_on_page && progressbar_value == "100" ) {
            window.location.href = upon_completion_redirect;
        }
        $task_footer.find('button').removeAttr('disabled');
        $new_task_completion_form = $task_footer.find('form#task-footer-toggle-task-completion-form');
        $new_task_completion_form.submit(submitTaskFooterToggleTaskCompletion);
        $new_link_submit_form = $task_footer.find('#task-footer-after-completed form');
        $new_link_submit_form.submit(submitTaskFooterAfterCompletionForm);
    });
    return false;
};

$('.project-kind-challenge form#task-footer-toggle-task-completion-form').submit(submitTaskFooterToggleTaskCompletion);
$('.project-kind-challenge #task-footer-after-completed form').submit(submitTaskFooterAfterCompletionForm);


$('.project-kind-challenge a#leave_direct_signup_button').bind('click', function() {
    $(this).parent().submit();
});

$('#user_profile .profile-wrapper a.show-all-badges').click(function(){
    $('#user_profile .profile-wrapper div.profile-badges').animate({height: '100%'}, 'slow');
    $('#user_profile .profile-wrapper div.profile-badges li').fadeIn('slow');
    $('#user_profile .profile-wrapper a.show-all-badges').toggle();
});

$('#user_profile .profile-wrapper a.show-all-courses').click(function(){
    $('#user_profile .profile-wrapper div.profile-courses').animate({height: '100%'}, 'slow');
    $('#user_profile .profile-wrapper div.profile-courses li').fadeIn('slow');
    $('#user_profile .profile-wrapper a.show-all-courses').toggle();
});

var getSourceFromUrl = function(url) {
    var a = document.createElement('a');
    a.href = url;
    var source = a.hostname;
    if ( a.protocol) {
        source = a.protocol + '//' + source;
    }
    if ( a.port ) {
        source = source + ':' + a.port;
    }
    return source;
};

$('.project-kind-challenge #task-body a.external-task').click(function() {
    var url = $(this).attr('href');
    var origin = getSourceFromUrl(url);
    var opened = window.open(url);
    function onMessage(event) {
        event = event.originalEvent;
        if (event.source == opened && event.origin == origin && event.data == 'task-complete') {
            $(window).unbind('message', onMessage);
            $(window).focus();
            opened.close();
            var $task_completion_form = $('.project-kind-challenge form#task-footer-toggle-task-completion-form');
            var $task_completion_cancel = $task_completion_form.find('#task-footer-toggle-task-completion-cancel-button');
            if ( $task_completion_form.length && $task_completion_cancel.length == 0 ) {
                $task_completion_form.submit();
            }
        }
    }
    $(window).bind('message', onMessage);
    return false;
});

$('.project-kind-challenge a.give_badge_action').each(function() {

    var $dialog_div = $(this).parent().find('div.give_badge_dialog');
    var $dialog = $dialog_div.dialog({
        modal: true,
        autoOpen: false
    });

    $(this).click(function() {
        $dialog.dialog('open');
        return false;
    });

});

$('.project-kind-challenge #task_list_section li').hover(function() {
      $(this).find('.taskView').show();
}, function() {
      $(this).find('.taskView').hide();
});

$('.project-kind-challenge span.first-post').hover(function() {
      $(this).find('.report').show();
}, function() {
      $(this).find('.report').hide();
});

$('.project-kind-challenge span.post-replies').hover(function() {
      $(this).find('.report').show();
}, function() {
      $(this).find('.report').hide();
});

$(".right-aligned-rating").hover(
    function () {
        $("div.rating-key").hide();
        $(this).find("div.rating-key").show();
});

function disableLearn() {
    $("#learn #main #show-more-results").addClass('disabled');
    $("#learn #sidebar a.filter").addClass('disabled');
    $('#learn #sidebar form#learn-projects-filter input').attr('disabled', 'disabled');
    $('#learn #sidebar form#learn-projects-filter select').attr('disabled', 'disabled');
}

function enableLearn() {
    $("#learn #sidebar form#learn-projects-filter button[type=submit]").hide();
    $("#learn #main #learn-pagination").hide();
    if ( $("#learn #main #learn-pagination a.next").length ) {
        var $next = $("#learn #main #learn-pagination a.next");
        $("#learn #main #show-more-results").attr('href', $next.attr('href'));
        $("#learn #main #show-more-results").removeClass('disabled');
        $("#learn #main #show-more-results").show();
    } else {
        $("#learn #main #show-more-results").hide();
    }
    $("#learn #sidebar a.filter").removeClass('disabled');
    $('#learn #sidebar form#learn-projects-filter input').removeAttr('disabled');
    $('#learn #sidebar form#learn-projects-filter select').removeAttr('disabled');
}

function updateLearnHeader(data) {
    var learn_header = data['learn_header'];
    $('#learn #main #learn-header').html(learn_header);
}

function bindLearnFilters() {
    $('#learn #sidebar a.filter').click(submitLearnFilterLinks);
    $('#learn #sidebar form#learn-projects-filter select').change(submitLearnFilterFormField);
    $('#learn #sidebar form#learn-projects-filter input').click(submitLearnFilterFormField);
    $('#learn #sidebar form#learn-projects-filter').submit(submitLearnFilterForm);
}

function updateLearnFilters(data) {
    var learn_filters = data['learn_filters'];
    $('#learn #sidebar').html(learn_filters);
    bindLearnFilters();
}

function updateLearnProjectList(data) {
    var projects_html = data['projects_html'];
    var projects_pagination = data['projects_pagination'];
    $('#learn #main #project-list').append(projects_html);
    $('#learn #main #learn-pagination').html(projects_pagination);
}

function reloadLearnProjectList(data) {
    $('#learn #main #project-list').empty();
    updateLearnProjectList(data);
}

var doingPush = false;

if ( window.History.enabled ) {
    window.History.Adapter.bind(window,'statechange',function(){
        var state = window.History.getState();
        if ( !doingPush && state.data.path ) {
            window.location = state.data.path;
        }
        doingPush = false;
    });
}

function updateBrowserUrl(url) {
    if ( window.History.enabled ) {
        doingPush = true;
        window.History.pushState({path: url}, $("title").text(), url);
    }
}

function submitLearnShowMore(e) {
    $link = $(this);
    if ( !$link.hasClass('disabled') ) {
        var url = $link.attr('href');
        disableLearn();
        $.get(url, function(data) {
            updateLearnProjectList(data);
            enableLearn();
        });
        updateBrowserUrl(url);
    }
    return false;
}

function submitLearnFilterLinks(e) {
    $link = $(this);
    if ( !$link.hasClass('disabled')) {
        var url = $link.attr('href');
        disableLearn();
        $.get(url, function(data) {
            updateLearnHeader(data);
            updateLearnFilters(data);
            reloadLearnProjectList(data);
            enableLearn();
        });
        updateBrowserUrl(url);
    }
    return false;
}

function submitLearnFilterForm (e) {
    var $form = $(this).closest('form');
    var url = $form.attr('action');
    var form_data = $form.serialize();
    disableLearn();
    $.get(url, form_data, function(data) {
        console.log(data);
        updateLearnHeader(data);
        updateLearnFilters(data);
        reloadLearnProjectList(data);
        enableLearn();
    });
    updateBrowserUrl(url + '?' + form_data);
   return false;
};

function submitLearnFilterFormField(e) {
    $(this).closest('form').submit();
}

$('#learn #main #show-more-results').click(submitLearnShowMore);
bindLearnFilters();

(function(){
	var oldIndex;
	var oldOrder;
	$("#content-pages ul").sortable({
	    start: function (event, ui) {
	         oldIndex = $(ui.item).parent().children().index(ui.item);
	         oldOrder = $(this);
	    },
		update: function(event, ui) {
			var newIndex = $(ui.item).parent().children().index(ui.item);
			if (newIndex  == oldIndex) {
				return false;
			}
			var url = $("#reorder_tasks").attr("action");
            var tasks = [];
            tasks = $.makeArray($(this).children().find("a.taskLink"))
                .map(function(t, i)
                {
                    return $(t).attr("id");
                });
	        $.ajax({
	            type: 'POST',
	            url: url,
	            data: {
                    csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
                    tasks: tasks,
	            },
	            dataType: "json",
	            success: function(data) {
	            	renderTasks($(ui.item).parent(), data);
            	},
	            error: function() {
	            	oldOrder.sortable('cancel');
            	},
	        });
		},

	});

	if ($("input[name=canChangeOrder]").val() != "True"){
		$("#content-pages ul").sortable('disable');
	}
})();

function renderTasks(task_ui, tasks){
	var task_len = task_ui.children('li').length;
	$.each(task_ui.children('li'), function(counter, task_dom){
		var task = $(task_dom);
		task.children('a.taskLink')
			.text(tasks[counter]["title"])
			.attr("href", tasks[counter]["url"]);

		if (counter == 0){
			if (task.children("a.robttn.up").length){
				task.children("a.robttn.up").remove();
			}
		} else {
			var button_up = task.children("a.robttn.up");
			if (!button_up.length){
				button_up = $(document.createElement('a'))
							.addClass("robttn up").text("(UP)");
				task.append(button_up);
			}
			button_up.attr("href", tasks[counter]["bttnUpUrl"]);
		}

		if (counter == task_len - 1){
			if (task.children("a.robttn.dwn").length){
				task.children("a.robttn.dwn").remove();
			}
		} else {
			var button_down = task.children("a.robttn.dwn");
			if (!button_down.length){
				button_down = $(document.createElement('a'))
							.addClass("robttn dwn").text("(DOWN)");
				task.prepend(button_down);
			}
			button_down.attr("href", tasks[counter]["bttnDownUrl"]);
		}
	});
}

