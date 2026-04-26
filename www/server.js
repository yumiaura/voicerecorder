"use strict";

/* Dev server: static www/src, proxy /api to Flask. */

const path = require("path");
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const apiTarget = process.env.VR_API || "http://127.0.0.1:5000";
const staticRoot = path.join(__dirname, "src");

app.use(
  "/api",
  createProxyMiddleware({
    target: apiTarget,
    changeOrigin: true,
    pathRewrite: {
      "^/": "/api/",
    },
  })
);
app.use(express.static(staticRoot));

app.get("*", (req, res) => {
  res.sendFile(path.join(staticRoot, "index.html"));
});

const port = parseInt(process.env.VR_WWW || "3000", 10);
app.listen(port, () => {
  console.log("www dev: http://127.0.0.1:" + port + "  api proxy -> " + apiTarget);
});
