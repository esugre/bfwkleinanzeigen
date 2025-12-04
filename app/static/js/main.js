import { search } from "./modules/search.js";

function main() {
  //var b = document.getElementById("searchButton");
  searchButton.addEventListener("click", (e) => {
    search();
  });
  // Hier müssen die Event Listener hinzugefügt werden,
  // so dass die Funktion "search" aufgerufen wird, wenn
  // man auf den Suchen-Button klickt
}

if (document.readyState === "loading") {
  // Dokument lädt noch
  document.addEventListener("DOMContentLoaded", main);
} else {
  // Dokument wurde schon geladen
  main();
}
