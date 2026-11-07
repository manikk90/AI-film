'use strict';

// Use an explicitly selected local browser when the Playwright download is
// unavailable. With no override, Playwright retains its normal bundled browser.
const fs = require('fs');
const path = require('path');

function launchOptions(env = process.env) {
  const executable = env.AIFILM_CHROMIUM_EXECUTABLE;
  if (!executable) return {};
  if (!path.isAbsolute(executable)) {
    throw new Error('AIFILM_CHROMIUM_EXECUTABLE must be an absolute executable path');
  }
  try {
    if (!fs.statSync(executable).isFile()) throw new Error('not a file');
    fs.accessSync(executable, fs.constants.X_OK);
  } catch (_) {
    throw new Error('AIFILM_CHROMIUM_EXECUTABLE is not an executable file: ' + executable);
  }
  return { executablePath: executable };
}

module.exports = { launchOptions };
