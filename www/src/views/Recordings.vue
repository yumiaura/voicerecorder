<template>
  <div>
    <div
      v-if="error"
      class="alert alert-danger p-1 mb-2 d-flex align-items-center"
      @click="error = ''"
    >
      <div class="m-auto text-center" style="cursor: pointer">
        {{ error }} <i class="fa fa-times"></i>
      </div>
    </div>
    <div
      v-if="success"
      class="alert alert-success p-1 mb-2 d-flex align-items-center"
      @click="success = ''"
    >
      <div class="m-auto text-center" style="cursor: pointer">
        {{ success }} <i class="fa fa-check"></i>
      </div>
    </div>
    <div
      v-show="wait.length"
      class="alert alert-secondary text-center p-1 mb-2"
    >
      <i class="fa fa-spinner fa-pulse"></i> {{ wait.join(", ") }}
    </div>

    <div
      class="d-flex align-items-center justify-content-between flex-wrap gap-1 mb-2"
    >
      <h4 class="mb-0">Recordings</h4>
      <button
        class="btn btn-sm btn-outline-secondary"
        type="button"
        @click="logout"
      >
        <i class="fa fa-sign-out-alt"></i> Logout
      </button>
    </div>

    <div class="form-check-inline m-1 d-flex flex-wrap align-items-end row-gap-1 mb-2">
      <div style="margin-right: 0.5rem">
        <label class="form-label mb-0 small">Date</label>
        <input
          v-model="selectedDate"
          class="form-control form-control-sm"
          type="date"
          :disabled="wait.length > 0"
          @change="onDateInput"
        />
      </div>
      <div
        v-if="days.length"
        class="d-flex flex-column"
        style="min-width: 220px"
      >
        <label class="form-label mb-0 small"
          >Day in range ({{ daySlider + 1 }} / {{ days.length }})</label
        >
        <input
          v-model.number="daySlider"
          :max="Math.max(0, days.length - 1)"
          min="0"
          :disabled="wait.length > 0"
          class="form-range"
          type="range"
          @input="onDaySlider"
        />
      </div>
      <div>
        <button
          class="btn btn-sm btn-primary fw-bold"
          type="button"
          :disabled="wait.length > 0"
          @click="loadAll"
        >
          <i class="fa fa-sync"></i> RELOAD
        </button>
      </div>
    </div>

    <div
      v-if="segments.length === 0 && !wait.length"
      class="text-muted"
    >
      No segments for this day.
    </div>

    <div v-else>
      <audio
        v-if="activeSrc"
        ref="player"
        :key="activeSrc"
        class="w-100"
        :src="activeSrc"
        controls
      />

      <div class="d-flex flex-wrap gap-1 my-2 align-items-center">
        <span class="small me-1">Jump</span>
        <button
          v-for="b in seekButtons"
          :key="'m' + b.v"
          class="btn btn-sm btn-outline-secondary"
          type="button"
          :disabled="wait.length > 0 || !segments.length"
          @click="seekBySec(-b.v * 60)"
        >
          −{{ b.l }}
        </button>
        <button
          v-for="b in seekSecButtons"
          :key="'s' + b"
          class="btn btn-sm btn-outline-secondary"
          type="button"
          :disabled="wait.length > 0 || !segments.length"
          @click="seekBySec(-b)"
        >
          −{{ b }}s
        </button>
        <span class="px-1">|</span>
        <button
          v-for="b in seekSecButtonsP"
          :key="'p' + b"
          class="btn btn-sm btn-outline-primary"
          type="button"
          :disabled="wait.length > 0 || !segments.length"
          @click="seekBySec(b)"
        >
          +{{ b }}s
        </button>
        <button
          v-for="b in seekButtons"
          :key="'pm' + b.v"
          class="btn btn-sm btn-outline-primary"
          type="button"
          :disabled="wait.length > 0 || !segments.length"
          @click="seekBySec(b.v * 60)"
        >
          +{{ b.l }}
        </button>
      </div>

      <div
        v-if="currentTr"
        class="border rounded p-2 small bg-light"
        style="max-height: 220px; overflow: auto; white-space: pre-wrap"
      >
        <strong>Transcript</strong> (segment #{{ showSegId }})
        <div>{{ currentTr || "—" }}</div>
      </div>
    </div>
  </div>
</template>

<script>
module.exports = {
  name: "Recordings",
  data: function () {
    return {
      wait: [],
      error: "",
      success: "",
      days: [],
      daySlider: 0,
      selectedDate: "",
      segments: [],
      currentIndex: 0,
      seekSecButtons: [5, 15, 60],
      seekSecButtonsP: [5, 15, 60],
      seekButtons: [
        { l: "5m", v: 5 },
      ],
    };
  },
  computed: {
    activeSrc: function () {
      if (!this.segments.length) {
        return "";
      }
      var s = this.segments[this.currentIndex];
      if (!s) {
        return "";
      }
      var base = this.absUrl(s.stream_url);
      var tok = sessionStorage.getItem("vr_access_token");
      if (!tok) {
        return base;
      }
      return (
        base
        + (base.indexOf("?") >= 0 ? "&" : "?")
        + "access_token="
        + encodeURIComponent(tok)
      );
    },
    currentTr: function () {
      if (!this.segments.length) {
        return "";
      }
      var s = this.segments[this.currentIndex];
      return s ? s.transcript || "" : "";
    },
    showSegId: function () {
      if (!this.segments.length) {
        return "—";
      }
      var s = this.segments[this.currentIndex];
      return s ? s.id : "—";
    },
  },
  created: function () {
    this.loadAll();
  },
  methods: {
    logout: function () {
      if (window.__vrSetToken) {
        window.__vrSetToken("");
      } else {
        sessionStorage.removeItem("vr_access_token");
      }
      this.$router.push({ name: "login" });
    },
    absUrl: function (u) {
      if (u && u.indexOf("http") === 0) {
        return u;
      }
      return window.location.origin + (u || "");
    },
    loadAll: function () {
      var self = this;
      self.wait.push("days");
      return axios
        .get("/api/days")
        .then(function (r) {
          self.days = r.data.items || [];
          if (self.days.length) {
            self.syncSliderToEnd();
            return self.loadSegments();
          }
          self.segments = [];
          return null;
        })
        .catch(function (err) {
          self.setErr(err);
        })
        .then(function () {
          self.popWait("days");
        });
    },
    popWait: function (k) {
      var i = this.wait.indexOf(k);
      if (i !== -1) {
        this.wait.splice(i, 1);
      }
    },
    setErr: function (err) {
      this.error = err.response
        ? (err.response.data && err.response.data.error
            ? (typeof err.response.data.error === "string"
                ? err.response.data.error
                : JSON.stringify(err.response.data.error))
            : (err.response.status + " " + err.response.statusText))
        : err.message;
    },
    syncSliderToEnd: function () {
      this.daySlider = Math.max(0, this.days.length - 1);
      this.selectedDate = this.days[this.daySlider] || "";
    },
    onDaySlider: function () {
      if (!this.days.length) {
        return;
      }
      this.daySlider = Math.max(
        0,
        Math.min(this.daySlider, this.days.length - 1)
      );
      this.selectedDate = this.days[this.daySlider] || "";
      this.loadSegments();
    },
    onDateInput: function () {
      var idx = this.days.indexOf(this.selectedDate);
      if (idx === -1) {
        this.loadSegments();
        return;
      }
      this.daySlider = idx;
      this.loadSegments();
    },
    loadSegments: function () {
      var self = this;
      if (!this.selectedDate) {
        this.segments = [];
        return Promise.resolve();
      }
      this.wait.push("segments");
      return axios
        .get("/api/segments", { params: { day: this.selectedDate } })
        .then(function (r) {
          self.segments = r.data.items || [];
          if (self.currentIndex >= self.segments.length) {
            self.currentIndex = 0;
          }
          if (!self.segments.length) {
            self.currentIndex = 0;
          }
        })
        .catch(function (err) {
          self.setErr(err);
        })
        .then(function () {
          self.popWait("segments");
        });
    },
    seekBySec: function (d) {
      if (!this.segments.length) {
        return;
      }
      var a = this.$refs.player;
      if (!a) {
        return;
      }
      var c = a.currentTime || 0;
      var du = a.duration;
      if (!isFinite(du) || du <= 0) {
        return;
      }
      if (d >= 0) {
        this.forwardDelta(d, c, du);
      } else {
        this.backDelta(-d, c);
      }
    },
    backDelta: function (need, cur) {
      var a = this.$refs.player;
      if (!a) {
        return;
      }
      if (need <= cur) {
        a.currentTime = cur - need;
        return;
      }
      this.loadPrevAndSetFromEnd(need - cur);
    },
    loadPrevAndSetFromEnd: function (remaining) {
      var self = this;
      if (self.currentIndex === 0) {
        self.$nextTick(function () {
          if (self.$refs.player) {
            self.$refs.player.currentTime = 0;
          }
        });
        return;
      }
      self.currentIndex = self.currentIndex - 1;
      self.$nextTick(function () {
        var a = self.$refs.player;
        if (!a) {
          return;
        }
        var h = function hfn() {
          a.removeEventListener("loadedmetadata", hfn);
          var d2 = a.duration;
          if (!isFinite(d2) || d2 <= 0) {
            a.currentTime = 0;
            return;
          }
          if (remaining <= d2) {
            a.currentTime = d2 - remaining;
          } else {
            self.loadPrevAndSetFromEnd(remaining - d2);
          }
        };
        a.addEventListener("loadedmetadata", h);
      });
    },
    forwardDelta: function (d, c, du) {
      if (c + d <= du) {
        this.$refs.player.currentTime = c + d;
        return;
      }
      var over = c + d - du;
      this.applyForward(over);
    },
    applyForward: function (over) {
      var self = this;
      if (self.currentIndex >= self.segments.length - 1) {
        self.$nextTick(function () {
          var a = self.$refs.player;
          if (a && isFinite(a.duration)) {
            a.currentTime = a.duration;
          }
        });
        return;
      }
      this.currentIndex += 1;
      this.$nextTick(function () {
        var a = self.$refs.player;
        if (!a) {
          return;
        }
        var h2 = function h2fn() {
          a.removeEventListener("loadedmetadata", h2fn);
          var d2 = a.duration;
          if (!isFinite(d2) || d2 <= 0) {
            return;
          }
          if (over <= d2) {
            a.currentTime = over;
          } else {
            self.applyForward(over - d2);
          }
        };
        a.addEventListener("loadedmetadata", h2);
      });
    },
  },
};
</script>
<style>
</style>
