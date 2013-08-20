/**************************************************************
 * Lernanta home.html template helper.
 **************************************************************/

/*global window */
/*global jQuery */
/*global console */

var Lernanta = window.Lernanta || {};

(function ($, Lernanta) {

    "use strict";
    var init = function () {
        $(function () {
            $(".p2pu-tab").click(function () {
                var $this = $(this),
                    panel = $(".p2pu-panel-wrap"),
                    icon_name = 'icon-chevron-sign-',
                    icon = $this.find('i');

                panel.slideToggle("fast", function () {
                    var $this = $(this);
                    if ($this.is(':visible')) {
                        icon.attr('class', icon_name + 'up');
                    } else {
                        icon.attr('class', icon_name + 'down');
                    }
                });
            });

            $('.community-member').tooltip({
                placement: 'bottom'
            });
        });
    };

    Lernanta.Homepage = {};
    Lernanta.Homepage.init = init;

}(jQuery, Lernanta));
