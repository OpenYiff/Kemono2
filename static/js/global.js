;(() => {
  "use strict";

  /**
   * The collection of methods related to interacting with API.
   */
  const kemonoAPI = {
    /**
     * @param {string} service 
     * @param {string} user 
     * @param {string} post_id 
     */
    postFavoritePost(service, user, post_id) {
      return new Promise((resolve, reject) => {
        kemonoFetchAsync(`/favorites/post/${service}/${user}/${post_id}`, {
          method: 'POST'
        })
          .then(response => {
          
          if (response.ok) {
            resolve({
              success: true
            })
          }
        })
        .catch(error => reject(alert('Error 001 - could not save favorite')));
      });
      
    },
    /**
     * @param {string} service 
     * @param {string} user 
     * @param {string} post_id 
     */
    deleteUnfavoritePost(service, user, post_id) {
      return new Promise((resolve, reject) => {
        kemonoFetchAsync(`/favorites/post/${service}/${user}/${post_id}`, {
          method: "DELETE"
        })
          .then(response => {
            if (response.ok) {
              resolve({
                success: true
              })
            }
          })
          .catch(error => reject(alert('Error 002 - could not remove favorite')));
      });
     
    },
    /**
     * @param {string} service 
     * @param {string} user 
     */
    postFavoriteArtist(service, user) {
      return new Promise((resolve, reject) => {
        kemonoFetchAsync(`/favorites/artist/${service}/${user}`, {
          method: 'POST'
        })
          .then(response => {
            if (response.ok) {
              resolve({
                success: true
              })
            }
          })
          .catch(error => reject(alert('Error 003 - could not save favorite')));
      });
    },
    /**
     * @param {string} service 
     * @param {string} user 
     */
    deleteUnfavoriteArtist(service, user) {
      return new Promise((resolve, reject) => {
        kemonoFetchAsync(`/favorites/artist/${service}/${user}`, {
          method: "DELETE"
        })
          .then(response => {
            if (response.ok) {
              resolve({
                success: true
              })
            }
          })
          .catch(error => reject(alert('Error 004 - could not remove favorite')));
      });
    }
  };

  /**
   * TODO: use proper DOM elements insertions.
   */
  const loadingImage = document.createElement("img");
  loadingImage.setAttribute("class", "image");
  loadingImage.setAttribute("src", "/static/loading.gif");
  const loadingImageString = loadingImage.outerHTML;

  // select sections
  const sectionRegister = document.querySelector(".site-section--register");
  const sectionPostDetails = document.querySelector('.site-section--post-details');
  const sectionUser = document.querySelector('.site-section--user-details');

  // run the script for present ones
  sectionRegister && initSectionRegister();
  sectionPostDetails && initSectionPostDetails();
  sectionUser && initSectionUserDetails();

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

  /**
   * TODO: replace reading `data` attributes with parsing URL.
   */
  function initSectionPostDetails() {
    /**
     * @type {HTMLElement}
     */
    const userPost = document.querySelector(".user-post");
    const {service, user } = userPost.dataset;
    /**
     * @type {HTMLButtonElement}
     */
    const favButton = userPost.querySelector(".user-post__favorite");

    favButton.addEventListener("click", handleFavClick);

    /**
     * @param {MouseEvent} event 
     */
    function handleFavClick(event) {
      /** 
       * @type {HTMLButtonElement}
       */
      const button = event.target;
      button.disabled = true;
      button.innerHTML = loadingImageString;

      if (button.classList.contains("user-post__favorite--favorited")) {
        kemonoAPI.deleteUnfavoritePost(service, user, userPost.id)
          .then(response => {
            if (response.success) {
              favButton.classList.toggle("user-post__favorite--favorited");
              favButton.textContent = "☆";
              button.disabled = false;
            }
          });

      } else {
        kemonoAPI.postFavoritePost(service, user, userPost.id)
          .then(response => {
            if (response.success) {
              favButton.classList.toggle("user-post__favorite--favorited");
              favButton.textContent = "★";
              button.disabled = false;
            }
          });

      }
    }
  }

  function initSectionUserDetails() {
    /**
     * @type {HTMLElement}
     */
    const userDetails = document.querySelector(".user-header");
    const { service } = userDetails.dataset;
    /**
     * @type {HTMLButtonElement}
     */
    const favButton = userDetails.querySelector(".user-post__favorite");

    favButton.addEventListener("click", handleFavClick);

    /**
     * @param {MouseEvent} event
     */
    function handleFavClick(event) {
      /**
       * @type {HTMLButtonElement}
       */
      const button = event.target;
      button.disabled = true;
      button.innerHTML = loadingImageString;

      if (button.classList.contains("user-post__favorite--favorited")) {
        kemonoAPI.deleteUnfavoriteArtist(service, userDetails.id)
          .then(response => {
            if (response.success) {
              favButton.classList.toggle("user-post__favorite--favorited");
              favButton.textContent = "☆";
              button.disabled = false;
            }
          });

      } else {
        kemonoAPI.postFavoriteArtist(service, userDetails.id)
          .then(response => {
            if (response.success) {
              favButton.classList.toggle("user-post__favorite--favorited");
              favButton.textContent = "★";
              button.disabled = false;
            }
          });
      }
    }
  }

  /**
   * TODO: rewrite to async function after migrating to webpack.
   * @param {RequestInfo} endpoint
   * @param {RequestInit} options
   * @return {Promise<Response>}
   */
  function kemonoFetchAsync(endpoint, options) {
    return new Promise((resolve, reject) => {
      fetch(endpoint, options)
      .then(response => {

        if (response.redirected) {
          return add_url_param(response.url, 'redir', window.location.pathname);
        }

        if (!response.ok) {
          throw new Error("Something went wrong");
        }

        resolve(response);
      })
      .catch(error => reject(error))
    });
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

function attemptFlag (service, user, post_id) {
  if (confirm('Are you sure you want to flag this post for reimport?')) {
    fetch(`/api/${service}/user/${user}/post/${post_id}/flag`, { method: 'post' })
      .then(function (res) {
        window.alert(res.ok ? 'Successfully flagged.' : 'Error. There might already be a flag here.');
      });
  }
}

Array.prototype.forEach.call(document.getElementsByClassName('flag'), function (flag) {
  flag.addEventListener('click', function (_) {
    attemptFlag(
      flag.getAttribute('data-service'),
      flag.getAttribute('data-user'),
      flag.getAttribute('data-post')
    );
  })
});
