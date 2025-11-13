document.addEventListener("DOMContentLoaded", () => {
    const current = document.body.dataset.page;
    if (!current) return;

    document.querySelectorAll(".nav-link").forEach(link => {
        if (link.dataset.id === current) {
            link.classList.add("active");
        }
    });
});
