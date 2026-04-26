<template>
  <div class="mx-auto" style="max-width: 400px; margin-top: 2rem">
    <h4 class="mb-3">Sign in</h4>
    <div
      v-if="error"
      class="alert alert-danger p-1 mb-2 d-flex align-items-center"
      @click="error = ''"
    >
      <div class="m-auto text-center" style="cursor: pointer">
        {{ error }}
      </div>
    </div>
    <div v-if="submitting" class="alert alert-secondary text-center p-1 mb-2">
      Signing in...
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
          :disabled="submitting"
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
          :disabled="submitting"
          required
        />
      </div>
      <div>
        <button
          class="btn btn-primary btn-sm fw-bold w-100"
          type="submit"
          :disabled="submitting"
        >
          LOGIN
        </button>
      </div>
    </form>
  </div>
</template>

<script>
/* global sessionStorage */

module.exports = {
  name: "Login",
  data: function () {
    return {
      submitting: false,
      error: "",
      form: { username: "", password: "" },
    };
  },
  created: function () {
    if (sessionStorage.getItem("vr_access_token")) {
      this.$router.replace({ name: "home" });
    }
  },
  methods: {
    submit: async function () {
      var self = this;
      if (self.submitting) {
        return;
      }
      self.error = "";
      self.submitting = true;
      var timer = null;
      try {
        // Safety valve: never leave the form blocked forever.
        timer = setTimeout(function () {
          self.submitting = false;
          if (!self.error) {
            self.error = "Login timeout. Check network and server logs.";
          }
        }, 15000);

        var response = await fetch("/api/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: self.form.username,
            password: self.form.password,
          }),
        });
        var data = await response.json().catch(function () {
          return {};
        });
        if (!response.ok) {
          self.error = data && data.error
            ? (typeof data.error === "string"
                ? data.error
                : JSON.stringify(data.error))
            : (response.status + " " + response.statusText);
          return;
        }
        var token = data && data.access_token ? data.access_token : "";
        if (!token) {
          self.error = "No token in response";
          return;
        }
        if (window.__vrSetToken) {
          window.__vrSetToken(token);
        } else {
          sessionStorage.setItem("vr_access_token", token);
        }
        self.$router.push({ name: "home" });
      } catch (err) {
        self.error = err && err.message ? err.message : String(err);
      } finally {
        if (timer) {
          clearTimeout(timer);
        }
        self.submitting = false;
      }
    },
  },
};
</script>
<style>
</style>
