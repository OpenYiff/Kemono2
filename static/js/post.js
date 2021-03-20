function attemptFlag (_, api) {
  if (confirm('Are you sure you want to flag this post for reimport?')) {
    fetch(api, { method: 'post' })
      .then(function (res) {
        window.alert(res.ok ? 'Successfully flagged.' : 'Error. There might already be a flag here.');
      });
  }
}

(function () {
  const pathname = window.location.pathname.split('/');
  const resultsView = document.getElementById('results');
  let cacheApi, flagApi;
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ]
  switch (document.getElementsByName('service')[0].content) {
    case 'patreon': {
      cacheApi = `/api/lookup/cache/${pathname[3]}?service=patreon`;
      flagApi = `/api/patreon/user/${pathname[3]}/post/${pathname[5]}/flag`;
      break;
    }
    case 'gumroad': {
      cacheApi = `/api/lookup/cache/${pathname[3]}?service=gumroad`;
      flagApi = `/api/gumroad/user/${pathname[3]}/post/${pathname[5]}/flag`;
      break;
    }
    case 'subscribestar': {
      cacheApi = `/api/lookup/cache/${pathname[3]}?service=subscribestar`;
      flagApi = `/api/subscribestar/user/${pathname[3]}/post/${pathname[5]}/flag`;
      break;
    }
    case 'dlsite': {
      cacheApi = `/api/lookup/cache/${pathname[3]}?service=dlsite`;
      flagApi = `/api/dlsite/user/${pathname[3]}/post/${pathname[5]}/flag`;
      break;
    }
    default: {
      cacheApi = `/api/lookup/cache/${pathname[3]}?service=fanbox`;
      flagApi = `/api/fanbox/user/${pathname[3]}/post/${pathname[5]}/flag`;
    }
  }

  // TODO: use date-fns after migrating to webpack
  const publishedAt = !document.getElementsByName('published').length 
    ? undefined
    : new Date(document.getElementsByName('published')[0].content);

  const addedAt = !document.getElementsByName('added').length 
    ? undefined  
    : new Date(document.getElementsByName('added')[0].content);

  const publishedAtFormatted = !publishedAt
    ? "unknown"
    : `${publishedAt.getDate()} 
      ${months[publishedAt.getMonth()]} 
      ${publishedAt.getFullYear()}`;

  const addedAtFormatted = !addedAt
    ? "unknown"
    : `${addedAt.getDate()} 
      ${months[addedAt.getMonth()]} 
      ${addedAt.getFullYear()}`;
    

  fetch(cacheApi)
    .then(function (data) { return data.json(); })
    .then(function (cache) {
      
      resultsView.innerHTML += `
        <li>
          User: <a href="../">${cache.name}</a>
        </li>
        <li>
          ID: <a href="">${document.getElementsByName('id')[0].content}</a>
        </li>
        <li>
          <time 
            datetime=${publishedAt.toISOString()}
          >
            Published at: ${publishedAtFormatted}
          </time>
        </li>
        <li>
          <time
            datetime=${addedAt.toISOString()}
          >
            Added at: ${addedAtFormatted}
          </time>
        </li>
      `;
    })
    .then(function () {
      return fetch(flagApi);
    })
    .then(function (res) {
      resultsView.innerHTML += res.ok ? `
        <li><span class="subtitle">This post has been flagged for reimport.</span></li>
      ` : `
        <li><a href="javascript:;" id="flag-button">Flag for reimport</a> </li>
      `;
      if (!res.ok) {
        document.getElementById('flag-button').addEventListener('click', function (e) {
          attemptFlag(e, flagApi);
        });
      }
    });
})();
