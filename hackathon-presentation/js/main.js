import { introSlides } from "./slides-intro.js";
import { teamSlides } from "./slides-team.js";
import { storySlides } from "./slides-story.js";
import { solutionSlides } from "./slides-solution.js";
import { closingSlides } from "./slides-closing.js";

const slides = [
  ...introSlides,
  ...teamSlides,
  ...storySlides,
  ...solutionSlides,
  ...closingSlides
];

let currentSlide = 0;

const titleEl = document.getElementById("slide-title");
const contentEl = document.getElementById("slide-content");
const shellEl = document.querySelector(".slide-shell");
const indicatorEl = document.getElementById("slide-indicator");
const dotsEl = document.getElementById("dots");
const nextBtn = document.getElementById("next-btn");
const prevBtn = document.getElementById("prev-btn");
const progressBarEl = document.getElementById("progress-bar");

function renderDots() {
  dotsEl.innerHTML = "";
  slides.forEach((_, index) => {
    const dot = document.createElement("div");
    dot.className = "dot" + (index === currentSlide ? " active" : "");
    dot.title = `Go to slide ${index + 1}`;
    dot.addEventListener("click", () => {
      goToSlide(index);
    });
    dotsEl.appendChild(dot);
  });
}

function updateProgress() {
  const ratio = (currentSlide + 1) / slides.length;
  progressBarEl.style.width = `${ratio * 100}%`;
}

function renderSlide() {
  const slide = slides[currentSlide];
  titleEl.textContent = slide.title;
  contentEl.innerHTML = slide.render();
  indicatorEl.textContent = `Slide ${currentSlide + 1} / ${slides.length}`;
  updateProgress();
  renderDots();

  // retrigger content animation
  shellEl.classList.remove("active");
  void shellEl.offsetWidth; // force reflow to restart CSS animation
  shellEl.classList.add("active");
}

function goToSlide(index) {
  if (index < 0) index = 0;
  if (index >= slides.length) index = slides.length - 1;
  currentSlide = index;
  renderSlide();
}

function nextSlide() {
  currentSlide = (currentSlide + 1) % slides.length;
  renderSlide();
}

function prevSlide() {
  currentSlide = (currentSlide - 1 + slides.length) % slides.length;
  renderSlide();
}

// Fullscreen toggle
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.exitFullscreen().catch(() => {});
  }
}

// Event listeners
nextBtn.addEventListener("click", nextSlide);
prevBtn.addEventListener("click", prevSlide);

document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
    e.preventDefault();
    nextSlide();
  } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
    e.preventDefault();
    prevSlide();
  } else if (e.key.toLowerCase() === "f") {
    toggleFullscreen();
  }
});

// Initial render
renderSlide();
