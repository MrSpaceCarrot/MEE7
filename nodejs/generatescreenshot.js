// Module import
const DiscordScreenshot = require('discord-screenshot');

// Define constants
const username = process.argv[2];
const color = JSON.parse(process.argv[3]);
const content = process.argv[4];
const screenshot = new DiscordScreenshot(content);

// Create screenshot and export it
screenshot
  .setPfp('./pfp.png')
  .then(() => screenshot.setUsername(username, color))
  .then(() => screenshot.setTimestamp(new Date()))
  .then(() => screenshot.setContent(content))
  .then(() => screenshot.construct().write('./output.png'))