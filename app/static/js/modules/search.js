async function search() {
  const searchTerm = document.getElementById("search").value;
  const url = window.location.origin + "/search?search_term=" + searchTerm;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const result = await response.json();
    //empty list
    let wantedAdIds = result.map((i) => i.ad_id);

    let cards = document.getElementsByClassName("ad-card");

    for (let card of cards) {
      // display all cards (even if previously hidden)
      card.style.display = "grid";
      // hide unwanted cards
      if (
        wantedAdIds.length &&
        wantedAdIds.indexOf(parseInt(card.dataset.id)) < 0
      ) {
        card.style.display = "none";
      }
    }
  } catch (error) {
    console.error(error.message);
  }
  // 1. Es soll der aktuelle Suchbegriff aus dem Suchfeld ausgelesen werden.
  // 2. Es sollen von der API passende Kleinanzeigen zu diesem Begriff geladen werden.
  // 3. Die erhaltenen Anzeigen sollen dann als HTML-Elemente erstellt
  //    und auf der Seite als Children von den Elemente mit
  //    der ID 'anzeigenListe' eingehängt werden.
}

export { search };
