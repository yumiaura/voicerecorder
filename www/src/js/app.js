/* global httpVueLoader, axios, Vue, VueRouter */

var TOKEN = "vr_access_token";

function getToken() {
  return sessionStorage.getItem(TOKEN) || "";
}

function setToken(t) {
  if (t) {
    sessionStorage.setItem(TOKEN, t);
    axios.defaults.headers.common["Authorization"] = "Bearer " + t;
  } else {
    sessionStorage.removeItem(TOKEN);
    delete axios.defaults.headers.common["Authorization"];
  }
}

window.__vrSetToken = setToken;

if (getToken()) {
  setToken(getToken());
}

var APP_VER = "20260426_001";
const Recordings = httpVueLoader("views/Recordings.vue?v=" + APP_VER);
const Login = httpVueLoader("views/Login.vue?v=" + APP_VER);

const routes = [
  { path: "/login", name: "login", component: Login, meta: { public: true } },
  { path: "/", name: "home", component: Recordings },
];

const router = new VueRouter({ routes: routes, mode: "hash" });

window.__VRRouter = router;

router.beforeEach(function (to, from, next) {
  var hasToken = !!getToken();
  if (to.matched.some(function (r) {
    return r.meta && r.meta.public;
  })) {
    if (hasToken && to.name === "login") {
      next({ name: "home" });
      return;
    }
    next();
    return;
  }
  if (!hasToken) {
    if (to.name === "login") {
      next();
      return;
    }
    next({ name: "login" });
    return;
  }
  next();
});

axios.defaults.headers.common["X-Requested-With"] = "XMLHttpRequest";
axios.interceptors.response.use(
  function (r) {
    return r;
  },
  function (err) {
    if (err.response) {
      if (err.response.status === 403) {
        window.location.reload();
      } else if (err.response.status === 401) {
        var u = (err.config && err.config.url) || "";
        if (u.indexOf("auth/login") === -1) {
          setToken("");
          if (window.__VRRouter) {
            try {
              if (window.__VRRouter.currentRoute.name !== "login") {
                window.__VRRouter.replace({ name: "login" });
              }
            } catch (e) {
              window.location.hash = "#/login";
            }
          } else {
            window.location.hash = "#/login";
          }
        }
      }
    }
    return Promise.reject(err);
  }
);

/* eslint-disable no-new */
new Vue({
  el: "#app",
  data: function () {
    return {};
  },
  router: router,
  template:
    '<div class="d-flex flex-column" style="min-height: 100vh"><router-view/></div>',
});
/* eslint-enable no-new */
