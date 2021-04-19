; (() => {
  "use strict";

  /**
   * @type {HTMLElement | null}
   */
  const globalFooter = document.querySelector(".global-footer");

  // select registration section
  const sectionRegister = document.querySelector(".site-section--register");

  // run scripts for present parts
  globalFooter && initGlobalFooter(globalFooter);
  sectionRegister && initSectionRegister();

  /**
   * @param {HTMLElement} footer 
   */
  function initGlobalFooter(footer) {
    const navBar = footer.querySelector(".global-footer__navigation");
    /**
     * @type {HTMLButtonElement | null}
     */
    const navButton = footer.querySelector(".global-footer__nav-button");

    navButton.addEventListener("click", switchNavBar)

    function switchNavBar() {
      navBar.classList.toggle("global-footer__navigation--hidden");
      navButton.classList.toggle("global-footer__nav-button--active");
    }
  }

  function initSectionRegister() {
    populate_favorites();
  }

  function populate_favorites() {
    var input = document.getElementById('serialized-favorites');
    var favorites = localStorage.favorites;
    var to_serialize = [];
    if (input && favorites) {
      var artists = favorites.split(',');
      artists.forEach(function (artist) {
        var split = artist.split(':');
        if (split.length != 2) { return; }
        var elem = {
          'service': split[0],
          'artist_id': split[1]
        };
        to_serialize.push(elem);
      });
      var serialized = JSON.stringify(to_serialize);
      input.value = serialized;
    }
  }
})();

/**
 * @param {string} url 
 * @param {string} param_name 
 * @param {string} param_value 
 * @returns {string}
 */
function add_url_param(url, param_name, param_value) {
  var newURL = new URL(url);
  newURL.searchParams.set(param_name, param_value);
  return newURL.toString();
}