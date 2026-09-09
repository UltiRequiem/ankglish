(function () {
  "use strict";

  var card = document.querySelector(".ankglish-card");
  if (!card) return;

  var translation = card.querySelector(".ankglish-translation");
  if (!translation) return;

  var toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "ankglish-translation-toggle";
  toggle.textContent = "Show translation";
  toggle.setAttribute("aria-expanded", "false");
  translation.hidden = true;
  translation.parentNode.insertBefore(toggle, translation);

  toggle.addEventListener("click", function () {
    var isHidden = translation.hidden;
    translation.hidden = !isHidden;
    toggle.textContent = isHidden ? "Hide translation" : "Show translation";
    toggle.setAttribute("aria-expanded", String(isHidden));
  });
})();
