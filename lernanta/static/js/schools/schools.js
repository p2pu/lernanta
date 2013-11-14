
$(document).ready(function() {
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

