<template>
  <div class="mx-auto" style="max-width: 400px; margin-top: 2rem">
    <h4 class="mb-3">Sign in</h4>
    <div
      v-if="error"
      class="alert alert-danger p-1 mb-2 d-flex align-items-center"
      @click="error = ''"
    >
      <div class="m-auto text-center" style="cursor: pointer">
        {{ error }} <i class="fa fa-times" />
      </div>
    </div>
    <div
      v-show="wait.length"
      class="alert alert-secondary text-center p-1 mb-2"
    >
      <i class="fa fa-spinner fa-pulse" /> {{ wait.join(", ") }}
    </div>
    <form @submit.prevent="submit">
      <div class="mb-2">
        <label class="form-label mb-0 small">Username</label>
        <input
          v-model.trim="form.username"
          class="form-control form-control-sm"
          type="text"
          name="username"
          autocomplete="username"
          :disabled="wait.length > 0"
          required
        />
      </div>
      <div class="mb-2">
        <label class="form-label mb-0 small">Password</label>
        <input
          v-model="form.password"
          class="form-control form-control-sm"
          type="password"
          name="password"
          autocomplete="current-password"
          :disabled="wait.length > 0"
          required
        />
      </div>
      <div>
        <button
          class="btn btn-primary btn-sm fw-bold w-100"
          type="submit"
          :disabled="wait.length > 0"
        >
          <i class="fa fa-sign-in-alt" /> LOGIN
        </button>
      </div>
    </form>
  </div>
</template>

<script>
/* global axios, sessionStorage */

module.exports = {
  name: "Login",
  data: function () {
    return {
      wait: [],
      error: "",
      form: { username: "", password: "" },
    };
  },
  methods: {
    submit: function () {
      var self = this;
      self.error = "";
      self.wait.push("login");
      axios
        .post("/api/auth/login", {
          username: self.form.username,
          password: self.form.password,
        })
        .then(function (r) {
          var t = (r.data && r.data.access_token) || "";
          if (!t) {
            self.error = "No token in response";
            return;
          }
          if (window.__vrSetToken) {
            window.__vrSetToken(t);
          } else {
            sessionStorage.setItem("vr_access_token", t);
            axios.defaults.headers.common["Authorization"] = "Bearer " + t;
          }
          self.$router.push({ name: "home" });
        })
        .catch(function (err) {
          self.error = err.response
            ? err.response.data && err.response.data.error
              ? (typeof err.response.data.error === "string"
                  ? err.response.data.error
                  : JSON.stringify(err.response.data.error))
              : (err.response.status + " " + err.response.statusText)
            : err.message;
        })
        .finally(function () {
          var k = "login";
          var i = self.wait.indexOf(k);
          if (i !== -1) {
            self.wait.splice(i, 1);
          }
        });
    },
  },
};
</script>
<style>
</style>
