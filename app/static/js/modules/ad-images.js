async function getAdImages(ad_id) {
  const url = window.location.origin + "/ads/" + ad_id + "/images";

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const result = await response.json();
    return result;
  } catch (error) {
    console.error(error.message);
  }
}

let adList = Array.from(document.getElementsByClassName("ad-card"));

adList.forEach((item) => {
  let images;
  //getting async data
  let response = getAdImages(item.dataset.id);
  response.then((data) => {
    images = data;
  });

  // item.addEventListener("mouseover", (e) => {
  //   console.log(images);
  // });
});
