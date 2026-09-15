document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("nav-toggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("is-open"));
    sidebar.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => sidebar.classList.remove("is-open"))
    );
    document.addEventListener("click", (e) => {
      if (!sidebar.contains(e.target) && e.target !== toggle && sidebar.classList.contains("is-open")) {
        sidebar.classList.remove("is-open");
      }
    });
  }
});
