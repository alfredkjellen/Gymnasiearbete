// Funktion för att hämta innehåll från en tabell på en angiven URL
function fetchTableContent(url) {
// Hämtar innehållet från URL:en som text
var response = UrlFetchApp.fetch(url).getContentText();

// Extrahera alla <h2>-taggar för att hitta ett namn för kalkylbladet
var h2Matches = response.match(/<h2>\s*([\s\S]+?)\s*<\/h2>/g);
var sheetName = 'Ny Flik'; // Standardnamn om ingen <h2> hittas
if (h2Matches && h2Matches[1]) {
// Dekodar HTML-entiteter och tar bort HTML-taggar från den första <h2>-taggen och trimmar
resultatet
sheetName = decodeHtmlEntities(stripTags(h2Matches[1])).trim();
}

// Extraherar alla tabellrader från svaret
var matches = response.match(/<tr id="res_[^>]+>[\s\S]+?<\/tr>/g);
var data = [];
// Bearbetar varje tabellrad för att extrahera data
if (matches) {
for (var i = 0; i < matches.length; i++) {
var row = matches[i];
// Extraherar alla dataceller från raden
var tdMatches = row.match(/<td[^>]*>[\s\S]+?<\/td>/g);
// Kontrollerar att det finns minst 5 kolumner
if (tdMatches && tdMatches.length >= 5) {
// Behandlar den tredje och fjärde kolumnen
var thirdColumnData = decodeHtmlEntities(stripTags(tdMatches[2])).trim();
var fourthColumnData = decodeHtmlEntities(stripTags(tdMatches[3])).trim();

// Kontrollerar innehållet i den tredje och fjärde kolumnen enligt specifika kriterier
if ((thirdColumnData.includes("Me") || thirdColumnData.includes("Lå") ||
thirdColumnData.includes("Na")) &&

(fourthColumnData.includes("21") || fourthColumnData.includes("20") ||

fourthColumnData.includes("18"))) {

var rowData = [];

var firstColumnData = decodeHtmlEntities(stripTags(tdMatches[0])); // Första <td>

// Trimma första kolumnens data om det överstiger 10 tecken
if (firstColumnData.length > 10) {
firstColumnData = firstColumnData.slice(-10);
}

// Lägger till den bearbetade datan för kolumnerna i rowData
rowData.push(firstColumnData);
rowData.push(thirdColumnData);
rowData.push(fourthColumnData);
rowData.push(decodeHtmlEntities(stripTags(tdMatches[4]))); // Femte <td>
data.push(rowData);
}
}
}
}

// Skapar ett nytt kalkylblad med det extraherade namnet och lägger in data
var sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet(sheetName);
for (var i = 0; i < data.length; i++) {
// Skriver in raderna av data i det nya kalkylbladet
sheet.getRange(i + 1, 1, 1, data[i].length).setValues([data[i]]);
}

// Uppdaterar fliken 'Resultat' med det nya kalkylbladsnamnet
var resultSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Resultat');
var lastRowInA = resultSheet.getRange('A:A').getValues().findIndex(row => !row[0]) + 1;
if (lastRowInA === 0) lastRowInA = resultSheet.getLastRow() + 1;
resultSheet.getRange(lastRowInA, 1).setValue(sheetName);
}

// Funktion för att ta bort HTML-taggar från en sträng
function stripTags(input) {
return input.replace(/<\/?[^>]+(>|$)/g, "").trim();

}

// Funktion för att dekoda HTML-entiteter till text
function decodeHtmlEntities(input) {
return input.replace(/&#(\d+);/g, function(match, dec) {
return String.fromCharCode(dec);
});
}

// Funktion för att logga löparlänkar från en specifik URL
function logRunnerLinks() {
var mainUrl = "https://eventor.orientering.se/Ranking/ol/List/Index/311?pageIndex=5";
var mainResponse = UrlFetchApp.fetch(mainUrl).getContentText();
// Extraherar tabellinnehåll från <div id="main">
var linkMatches = mainResponse.match(/<div id="main">[\s\S]*?<table[^>]*>[\s\S]*?<\/table>/);
if (!linkMatches) return;
var runnerLinks = [];
var linkRegex = /<td[^>]*>\s*<a href="\/Ranking\/ol\/Runner\/Index\/[^"]+">/g;
var match;
// Hittar och samlar alla löparlänkar
while (match = linkRegex.exec(linkMatches[0])) {
runnerLinks.push('"' + 'https://eventor.orientering.se' +
match[0].match(/href="([^"]+)"/)[1] + '"');
}

// Skriver ut löparlänkarna till konsolen
Logger.log(runnerLinks.join(', '));
}

// Funktion för att hämta flera tabeller från olika länkar på en webbsida
function fetchMultipleTables() {
var mainUrl = "https://eventor.orientering.se/Ranking/ol/List/Index/311?pageIndex=5";
var mainResponse = UrlFetchApp.fetch(mainUrl).getContentText();
// Extraherar tabellinnehåll från <div id="main">
var linkMatches = mainResponse.match(/<div id="main">[\s\S]*?<table[^>]*>[\s\S]*?<\/table>/);

if (!linkMatches) return;
var links = [];
var linkRegex = /<td[^>]*>\s*<a href="([^"]+)">/g;
var match;
// Hittar och samlar alla länkar
while (match = linkRegex.exec(linkMatches[0])) {
links.push('https://eventor.orientering.se' + match[1]);
}

// Loopar genom alla länkar och anropar fetchTableContent() för varje länk
while (links.length > 0) {
var link = links.shift(); // Tar bort den första länken från listan och bearbetar den
fetchTableContent(link);
}
}
