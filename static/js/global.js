;(() => {
  "use strict";

  /**
   * @type {HTMLElement | null}
   */
  const globalHeader = document.querySelector(".global-header");
  /**
   * @type {HTMLElement | null}
   */
  const globalFooter = document.querySelector(".global-footer");

  // select registration section
  const sectionRegister = document.querySelector(".site-section--register");

  // run scripts for present parts
  globalHeader && initGlobalHeader(globalHeader);
  globalFooter && initGlobalFooter(globalFooter);
  sectionRegister && initSectionRegister();

  /** 
   * @param {HTMLElement} header
   */
  function initGlobalHeader(header) {
    /**
     * @type {HTMLUListElement}
     */
    const navList = header.querySelector(".nav-list--mid");
    
    initNavBar(navList);
  }

  /**
   * @param {HTMLElement} footer 
   */
  function initGlobalFooter(footer) {
    const navBar = footer.querySelector(".global-footer__navigation");
    const navList = navBar.querySelector(".nav-list--vertical")
    /**
     * @type {HTMLButtonElement | null}
     */
    const navButton = footer.querySelector(".global-footer__nav-button");

    navButton.addEventListener("click", switchNavBar)

    initNavBar(navList);

    function switchNavBar() {
      navBar.classList.toggle("global-footer__navigation--hidden");
      navButton.classList.toggle("global-footer__nav-button--active");
    }
  }

  function initSectionRegister() {
    populate_favorites();
  }

  /**
   * @param {HTMLUListElement} navList 
   */
  function initNavBar(navList) {
    /**
     * @type {HTMLUListElement | null}
     */
    let currentSelection;

    navList.addEventListener("click", switchSubmenu);
    navList.addEventListener("keydown", closeAllSublists)
    /**
     * @param {MouseEvent} event 
     */
    function switchSubmenu(event) {
      event.stopPropagation();
      /**
       * @type {HTMLButtonElement}
       */
      const button = event.target;

      if (button.classList.contains("nav-list__button")) {
        const navItem = button.closest(".nav-list__item");
        const subList = navItem.querySelector(".nav-list__sublist");

        if (currentSelection && currentSelection !== subList) {
          currentSelection.classList.add("nav-list__sublist--hidden");
        }

        if (subList.classList.contains("nav-list__sublist--hidden")) {
          subList.classList.remove("nav-list__sublist--hidden");
          currentSelection = subList;
        } else {
          subList.classList.add("nav-list__sublist--hidden");
          currentSelection = null;
        }
        
      }
    }

    /**
     * @param {KeyboardEvent} event 
     */
    function closeAllSublists(event) {
      if (currentSelection && (event.key === "Esc" || event.key === "Escape")) {
        currentSelection.classList.add("nav-list__sublist--hidden")
      }
      
    }
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