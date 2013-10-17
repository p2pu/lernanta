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
            $(".p2pu-tab").p2puSlider({
                navbarContainer: '.navbar',
                icon: '.p2pu-tab-icon',
                iconUp: 'icon-chevron-sign-down',
                iconDown: 'icon-chevron-sign-up'
            });
            $('.community-member').tooltip({
                placement: 'bottom'
            });
        });
    };

    Lernanta.Homepage = {};
    Lernanta.Homepage.init = init;

}(jQuery, Lernanta));
