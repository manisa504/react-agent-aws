const diagram = document.querySelector("#diagram-dialog");
document
  .querySelector("#open-diagram")
  .addEventListener("click", () => diagram.showModal());
document
  .querySelector("#close-diagram")
  .addEventListener("click", () => diagram.close());
diagram.addEventListener("click", (event) => {
  if (event.target === diagram) diagram.close();
});
