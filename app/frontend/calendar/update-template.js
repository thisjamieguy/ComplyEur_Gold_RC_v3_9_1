const fs = require('fs');
const path = require('path');

// Read the built assets
const buildDir = path.join(__dirname, '../../static/build/assets');
const files = fs.readdirSync(buildDir);

// Find CSS and JS files
const cssFile = files.find(f => f.startsWith('index-') && f.endsWith('.css'));
const jsFile = files.find(f => f.startsWith('index-') && f.endsWith('.js'));

if (!cssFile || !jsFile) {
  console.error('Could not find built assets');
  process.exit(1);
}

// Read the template
const templatePath = path.join(__dirname, '../../templates/calendar.html');
let template = fs.readFileSync(templatePath, 'utf8');

// Update the template with correct filenames
template = template.replace(
  /build\/assets\/index-[^"]+\.css/g,
  `build/assets/${cssFile}`
);
template = template.replace(
  /build\/assets\/index-[^"]+\.js/g,
  `build/assets/${jsFile}`
);

// Write the updated template
fs.writeFileSync(templatePath, template);

console.log(`Updated template with assets: ${cssFile}, ${jsFile}`);
