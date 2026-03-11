const { format } = require("./lib");
const fs = require("fs");

function run() {
  return format(String(fs.existsSync(".")));
}

module.exports = { run };

