(() => {
  "use strict";

  class SectionItem {
    /**
     * @param {String} name 
     * @param {(section: HTMLElement) => void} callback 
     */
    constructor(name, callback){
      this.name = name;
      this.callback = callback;
    }
  }

  // class PaySiteParser {};
  // class SiteStorage {};

  // TODO: write a storage manager
  // const localStorage = window.localStorage;
  const main = document.querySelector("main");

  const sectionList = [
    new SectionItem("requests-list", initSectionRequestsList),
    new SectionItem("artists-list", initSectionArtistsList),
    new SectionItem("request-new", initSectionRequestNew)
  ];

  // initialize sections if `<main>` is present
  main && initSections(main, sectionList);

  /**
   * @param {HTMLElement} main 
   * @param {SectionItem[]} sectionList
   */
  function initSections(main, sectionList) {

    for (const sectionItem of sectionList) {
      /**
       * @type HTMLElement
       */
      // select only for children of `<main>`
      const section = main.querySelector(`main > .${sectionItem.name}`);
      // run the callback if the section is present
      section && sectionItem.callback(section);
    }

  }

  /**
   * @param {HTMLElement} section
   */
  function initSectionRequestsList(section) {
    /**
     * @type HTMLFormElement
     */
    const searchForm = section.querySelector(".form");

    /**
     * @type HTMLButtonElement
     */
    const optionsButton = searchForm.querySelector(".form__button--button");

    /**
     * @type HTMLFieldSetElement
     */
    const searchOptions = searchForm.querySelector(".form__options");
  
    optionsButton.addEventListener("click", switchOptions);

    /**
     * TODO: `localStorage` state.
     * @param {*} event 
     */
    function switchOptions(event) {
      searchOptions.classList.toggle("form__options--hidden");
    }
  }

  /**
   * @param {HTMLElement} section 
   */
  function initSectionArtistsList(section) {
    /**
     * @type HTMLFormElement
     */
    const searchForm = section.querySelector(".form");
    const entries = section.querySelectorAll('.user-icon');

    searchForm && initSearchForm(searchForm);
    entries && Array.from(entries).forEach(icon => {
      switch (icon.getAttribute('data-service')) {
        case 'patreon': {
          fetch(`/proxy/patreon/user/${icon.getAttribute('data-user')}`)
            .then(res => res.json())
            .then(user => {
              const avatar = user.included ? user.included[0].attributes.avatar_photo_url : user.data.attributes.image_url;
              icon.setAttribute('style', `background-image: url('${avatar}');`);
            });
          break;
        }
        case 'fanbox': {
          require(['https://unpkg.com/unraw@1.2.5/dist/index.min.js'], unraw => {
            fetch(`/proxy/fanbox/user/${icon.getAttribute('data-user')}`)
              .then(res => res.json())
              .then(user => {
                const avatar = unraw.unraw(user.body.user.iconUrl);
                icon.setAttribute('style', `background-image: url('${avatar}');`);
              });
          });
          break;
        }
        case 'subscribestar': {
          fetch(`/proxy/subscribestar/user/${icon.getAttribute('data-user')}`)
            .then(res => res.json())
            .then(user => {
              const avatar = user.avatar;
              icon.setAttribute('style', `background-image: url('${avatar}');`);
            });
          break;
        }
        case 'gumroad': {
          fetch(`/proxy/gumroad/user/${icon.getAttribute('data-user')}`)
            .then(res => res.json())
            .then(user => {
              const avatar = user.avatar;
              icon.setAttribute('style', `background-image: url('${avatar}');`);
            });
          break;
        }
      }
    });

    function initSearchForm(form) {
      /**
       * @type HTMLButtonElement
       */
      const optionsButton = form.querySelector(".form__button--button");
      const searchOptions = form.querySelector(".form__options");

      optionsButton.addEventListener("click", switchOptions)

      function switchOptions(event) {
        searchOptions.classList.toggle("form__options--hidden");
      }
    };
  }

  /**
   * TODOs: 
   * - write binding between service selection and url provided
   * - image upload handler
   * @param {HTMLElement} section 
   */
  function initSectionRequestNew(section) {
    /**
     * @type HTMLFormElement
     */
    const form = section.querySelector(".form");
    /**
     * @type HTMLInputElement
     */
    const specificCheckbox = form.querySelector("#condition-specific");
    /**
     * @type HTMLFieldSetElement
     */
    const specificSection = form.querySelector("#specific_id").parentElement;

    form.addEventListener("change", switchCondition);

    if (specificCheckbox.checked) {
      specificSection.disabled = false;
    }

    /**
     * Switches the specific section depending on the state of checkbox.
     * @param {Event} event
     */
    function switchCondition(event) {

      if (event.target.id === specificCheckbox.id) {
        event.stopPropagation();

        if (specificCheckbox.checked) {
          specificSection.disabled = false;
        } else {
          specificSection.disabled = true;
        }

      } else {
        specificSection.disabled = true;
      }
      
    };

  }
})();