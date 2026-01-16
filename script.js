// SVG waves animation with distortion + parallax
(function () {
  const waves = document.querySelectorAll("#visual .wave");
  if (!waves || waves.length === 0) return;

  // Animation parameters for each wave
  const params = Array.from(waves).map(() => ({
    ampX: 8 + Math.random() * 10,
    ampY: 4 + Math.random() * 12,
    speed: 0.4 + Math.random(),
    phase: Math.random() * Math.PI * 2,
    rotate: (Math.random() - 0.5) * 0.4,
  }));

  // Check for reduced motion preferences or small screens
  const reduceMotion =
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    window.innerWidth < 600;

  let scrollParallaxY = 0;

  // Main animation function
  function animate(time) {
    const t = time * 0.001;

    waves.forEach((el, i) => {
      const p = params[i];
      const speed = p.speed * 2;
      const maxDX = 10;

      // Base wave distortion
      const dxRaw =
        Math.sin(t * speed + p.phase) * (reduceMotion ? p.ampX * 0.25 : p.ampX);
      const dx = Math.max(-maxDX, Math.min(maxDX, dxRaw));
      const dyWave =
        Math.cos(t * speed + p.phase) * (reduceMotion ? p.ampY * 0.25 : p.ampY);
      const rotate = p.rotate * Math.sin(t * speed + p.phase);

      // Parallax offset depending on layer depth
      const parallaxFactor = 0.3 + i * 0.15;
      const parallaxOffset = scrollParallaxY * parallaxFactor;
      const totalY = dyWave + parallaxOffset;

      // Apply combined transform
      el.setAttribute(
        "transform",
        `translate(${dx.toFixed(2)}, ${totalY.toFixed(2)}) rotate(${(
          rotate * 10
        ).toFixed(2)})`
      );
    });

    requestAnimationFrame(animate);
  }

  // Update parallax value on scroll
  function updateParallax() {
    scrollParallaxY = window.pageYOffset * 0.5;
  }

  // Scroll listener with requestAnimationFrame for performance
  let scrollTimeout;
  window.addEventListener("scroll", function () {
    if (scrollTimeout) {
      window.cancelAnimationFrame(scrollTimeout);
    }
    scrollTimeout = window.requestAnimationFrame(updateParallax);
  });

  requestAnimationFrame(animate);
  updateParallax();
})();

/* =========================================================
   ARROW NAVIGATION - ACTIVE SECTION HIGHLIGHTING
   ========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  const arrowNavs = document.querySelectorAll(".arrow-nav");
  const sections = document.querySelectorAll("section, header");

  // Update active navigation state
  function updateActiveNav() {
    let currentSection = "";
    const scrollPosition = window.scrollY + 100;

    sections.forEach((section) => {
      if (
        scrollPosition >= section.offsetTop &&
        scrollPosition < section.offsetTop + section.clientHeight
      ) {
        currentSection = section.id;
      }
    });

    arrowNavs.forEach((nav) => {
      nav.classList.remove("active");
      if (nav.getAttribute("data-section") === currentSection) {
        nav.classList.add("active");
      }
    });
  }

  window.addEventListener("scroll", updateActiveNav);
  updateActiveNav();

  // Smooth scroll on arrow click
  arrowNavs.forEach((nav) => {
    nav.addEventListener("click", function (e) {
      e.preventDefault();
      const targetElement = document.getElementById(
        this.getAttribute("data-section")
      );

      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop,
          behavior: "smooth",
        });
      }
    });
  });

  // Fade-in animation for sections
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1 }
  );

  sections.forEach((section) => {
    section.style.opacity = "0";
    section.style.transform = "translateY(20px)";
    section.style.transition = "opacity 0.8s ease, transform 0.8s ease";
    observer.observe(section);
  });

  // Enhanced hover effect for artwork cards
  const cards = document.querySelectorAll(".artwork-card");

  cards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-15px) scale(1.02)";
    });

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0) scale(1)";
    });
  });
});

/* =========================================================
   LIGHTBOX (GRAPH AND TOPICS ZOOM) - ENHANCED VERSION WITH PROPER ASPECT RATIO
   ========================================================= */

// Create or ensure the lightbox exists
function ensureLightboxExists() {
  let lightbox = document.getElementById("lightbox");

  if (!lightbox) {
    lightbox = document.createElement("div");
    lightbox.id = "lightbox";
    lightbox.innerHTML = `
      <div class="lightbox-content">
        <span class="close-lightbox">&times;</span>
        <div class="lightbox-image-container">
          <img id="lightbox-img" style="display:none;" />
        </div>
        <div id="lightbox-text" class="topic-card" style="display:none;"></div>
      </div>
    `;
    document.body.appendChild(lightbox);

    // Add close event
    lightbox.addEventListener("click", function (e) {
      if (
        e.target === lightbox ||
        e.target.classList.contains("close-lightbox")
      ) {
        closeLightbox();
      }
    });
  }

  return lightbox;
}

// Open the lightbox with proper aspect ratio handling
function openLightbox(contentType, content, graphType = null) {
  const lightbox = ensureLightboxExists();
  const lightboxImg = document.getElementById("lightbox-img");
  const lightboxText = document.getElementById("lightbox-text");

  // Reset
  lightboxImg.style.display = "none";
  lightboxText.style.display = "none";
  lightboxImg.className = ""; // Clear existing classes

  if (contentType === "image") {
    lightboxImg.src = content;
    lightboxImg.style.display = "block";

    // Force proper image loading with correct dimensions
    lightboxImg.onload = function () {
      this.style.width = "auto";
      this.style.height = "auto";
      this.style.maxWidth = "90vw";
      this.style.maxHeight = "85vh";
      this.style.objectFit = "contain";
      this.style.objectPosition = "center";
    };

    // Add specific classes based on image type
    if (content.includes("author_graph")) {
      lightboxImg.classList.add("author-graph-img");

      // Use provided graphType or try to determine from URL
      if (graphType) {
        lightboxImg.classList.add(`${graphType}-graph`);
      } else if (content.includes("full")) {
        lightboxImg.classList.add("full-graph");
      } else if (content.includes("top5")) {
        lightboxImg.classList.add("top5-graph");
      }
    } else {
      lightboxImg.classList.add("panel-img");
    }

    // Load image to trigger onload event
    lightboxImg.src = content;
  } else if (contentType === "topic") {
    lightboxText.innerHTML = content;
    lightboxText.style.display = "block";
  }

  lightbox.classList.add("active");
  document.body.style.overflow = "hidden"; // Prevent background scrolling

  // Add Escape key handling
  document.addEventListener("keydown", handleEscapeKey);
}

// Close the lightbox
function closeLightbox() {
  const lightbox = document.getElementById("lightbox");
  if (lightbox) {
    lightbox.classList.remove("active");
    document.body.style.overflow = ""; // Re-enable scrolling

    // Remove Escape key listener
    document.removeEventListener("keydown", handleEscapeKey);
  }
}

// Handle Escape key
function handleEscapeKey(e) {
  if (e.key === "Escape") {
    closeLightbox();
  }
}

// Handle clicks with event delegation
document.addEventListener("click", function (e) {
  // Handle images (graphs) - click on link
  if (e.target.closest(".graph-zoom") && !e.target.matches("img")) {
    e.preventDefault();

    const link = e.target.closest(".graph-zoom");
    if (link) {
      const imgSrc = link.getAttribute("href");
      if (imgSrc) {
        // Try to determine graph type from parent element
        const parentDiv = link.closest(".viz-item");
        let graphType = null;
        if (parentDiv) {
          if (parentDiv.classList.contains("full-graph")) {
            graphType = "full";
          } else if (parentDiv.classList.contains("top5-graph")) {
            graphType = "top5";
          }
        }
        openLightbox("image", imgSrc, graphType);
      }
    }
  }

  // Handle images (graphs) - direct click on image
  else if (e.target.matches(".graph-zoom img")) {
    e.preventDefault();

    const link = e.target.closest(".graph-zoom");
    if (link) {
      const imgSrc = link.getAttribute("href");
      if (imgSrc) {
        // Try to determine graph type from parent element
        const parentDiv = link.closest(".viz-item");
        let graphType = null;
        if (parentDiv) {
          if (parentDiv.classList.contains("full-graph")) {
            graphType = "full";
          } else if (parentDiv.classList.contains("top5-graph")) {
            graphType = "top5";
          }
        }
        openLightbox("image", imgSrc, graphType);
      }
    }
  }

  // Handle topic cards
  else if (e.target.closest(".graph-zoom-topic")) {
    e.preventDefault();

    const card = e.target.closest(".graph-zoom-topic");
    if (card) {
      const cardContent = card.innerHTML;
      openLightbox("topic", cardContent);
    }
  }

  // Handle images directly in graph containers (without link)
  else if (
    e.target.matches(".author-graph-img, .panel-img, .artwork-image img")
  ) {
    e.preventDefault();

    // For images, look for parent link if it exists
    const parentLink = e.target.closest("a");
    if (parentLink && parentLink.getAttribute("href")) {
      // Try to determine graph type from parent element
      const parentDiv = e.target.closest(".viz-item");
      let graphType = null;
      if (parentDiv) {
        if (parentDiv.classList.contains("full-graph")) {
          graphType = "full";
        } else if (parentDiv.classList.contains("top5-graph")) {
          graphType = "top5";
        }
      }
      openLightbox("image", parentLink.getAttribute("href"), graphType);
    } else {
      // Otherwise use the image directly
      // Try to determine graph type from parent element
      const parentDiv = e.target.closest(".viz-item");
      let graphType = null;
      if (parentDiv) {
        if (parentDiv.classList.contains("full-graph")) {
          graphType = "full";
        } else if (parentDiv.classList.contains("top5-graph")) {
          graphType = "top5";
        }
      }
      openLightbox("image", e.target.src, graphType);
    }
  }
});

// Initialization: ensure lightbox exists on load
document.addEventListener("DOMContentLoaded", function () {
  ensureLightboxExists();
});

/* =========================================================
   PROJECTS OVERLAY PANEL
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
  const overlayPanel = document.getElementById("overlay-panel");
  const panelSections = document.querySelectorAll(".panel-section");
  const closePanelBtn = document.querySelector(".close-panel-btn");
  const projectCards = document.querySelectorAll(".project-card");

  // Open panel when clicking a project card
  projectCards.forEach((card) => {
    card.addEventListener("click", function (e) {
      // Don't trigger if clicking the button specifically
      if (
        e.target.closest(".open-panel-btn") ||
        e.target.classList.contains("open-panel-btn")
      ) {
        return;
      }

      const panelId = this.getAttribute("data-panel");
      openPanel(panelId);
    });
  });

  // Open panel when clicking "Explore" button
  document.querySelectorAll(".open-panel-btn").forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent card click event
      const card = this.closest(".project-card");
      const panelId = card.getAttribute("data-panel");
      openPanel(panelId);
    });
  });

  // Close panel
  closePanelBtn.addEventListener("click", closePanel);

  // Close panel when clicking outside content
  overlayPanel.addEventListener("click", function (e) {
    if (e.target === overlayPanel) {
      closePanel();
    }
  });

  // Close panel with Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlayPanel.classList.contains("active")) {
      closePanel();
    }
  });

  function openPanel(panelId) {
    // Hide all panel sections
    panelSections.forEach((section) => {
      section.classList.remove("active");
    });

    // Show the requested panel
    const targetPanel = document.getElementById(`panel-${panelId}`);
    if (targetPanel) {
      targetPanel.classList.add("active");
    }

    // Show overlay
    overlayPanel.classList.add("active");
    document.body.style.overflow = "hidden"; // Prevent background scrolling
  }

  function closePanel() {
    overlayPanel.classList.remove("active");
    document.body.style.overflow = ""; // Restore scrolling

    // Small delay before hiding content for smooth animation
    setTimeout(() => {
      panelSections.forEach((section) => {
        section.classList.remove("active");
      });
    }, 300);
  }
});

/* =========================================================
   NAVIGATION SIZE BASED ON CURRENT SECTION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {
  const sections = document.querySelectorAll("section, header");

  function updateNavigationSize() {
    let currentSection = "";
    const scrollPosition = window.scrollY + 100;

    sections.forEach((section) => {
      if (
        scrollPosition >= section.offsetTop &&
        scrollPosition < section.offsetTop + section.clientHeight
      ) {
        currentSection = section.id;
      }
    });

    // Add or remove 'home-section' class from body
    if (currentSection === "home") {
      document.body.classList.add("home-section");
    } else {
      document.body.classList.remove("home-section");
    }
  }

  // Update on scroll
  window.addEventListener("scroll", updateNavigationSize);

  // Initial check
  updateNavigationSize();

  // Also update when clicking navigation arrows
  document.querySelectorAll(".arrow-nav").forEach((nav) => {
    nav.addEventListener("click", function () {
      // Small delay to allow scroll to complete
      setTimeout(updateNavigationSize, 100);
    });
  });
});

/* =========================================================
   LDA TOPICS DYNAMIC SEARCH
   ========================================================= */
const searchInput = document.getElementById("topicSearch");
const topicCards = document.querySelectorAll(".topic-card");

if (searchInput) {
  searchInput.addEventListener("input", function (e) {
    // Get search term in lowercase
    const term = e.target.value.toLowerCase();

    topicCards.forEach((card) => {
      // Get keywords stored in data-words attribute
      const words = card.getAttribute("data-words").toLowerCase();
      // Also get the title (e.g., Topic 42)
      const topicTitle = card.querySelector("h4").innerText.toLowerCase();

      // If term is present in words or title, show, otherwise hide
      if (words.includes(term) || topicTitle.includes(term)) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  });
}

/* =========================================================
   AUTHOR TOPICS DYNAMIC DISPLAY – FETCH SERVER GRAPHS
   ========================================================= */
document.addEventListener("DOMContentLoaded", function () {
  const authorSelect = document.getElementById("authorSelect");
  const plotBtn = document.getElementById("plotAuthorBtn");
  const graphTypeSelect = document.getElementById("graphTypeSelect");
  const authorGraphsContainer = document.getElementById("authorGraphs");

  if (authorSelect && plotBtn && authorGraphsContainer) {
    plotBtn.addEventListener("click", async function () {
      const author = authorSelect.value;
      const graphType = graphTypeSelect ? graphTypeSelect.value : "full";

      if (!author) {
        authorGraphsContainer.innerHTML = "<p>Please select an author.</p>";
        return;
      }

      // Clear previous graph and show loading
      authorGraphsContainer.innerHTML = "<p>Loading graph...</p>";

      try {
        // Fetch the graph from the server
        const response = await fetch("/author_graphs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ author: author, graph_type: graphType }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Clear loading text
        authorGraphsContainer.innerHTML = "";

        if (data.img) {
          // Title above the graph
          const title = document.createElement("div");
          title.className = "graph-title";
          title.textContent = `${
            graphType === "full" ? "All Topics" : "Top 5 Topics"
          } for ${author}`;
          authorGraphsContainer.appendChild(title);

          // Graph container
          const divGraph = document.createElement("div");
          divGraph.className = `viz-item ${graphType}-graph`;

          divGraph.innerHTML = `
              <div class="graph-container">
                <a href="data:image/png;base64,${data.img}" class="graph-zoom">
                  <img src="data:image/png;base64,${data.img}" 
                       alt="${
                         graphType === "full" ? "All Topics" : "Top 5 Topics"
                       } for ${author}" 
                       class="author-graph-img" />
                </a>
              </div>
            `;

          authorGraphsContainer.appendChild(divGraph);

          // Re-enable lightbox zoom for this new graph
          const newZoomLink = divGraph.querySelector(".graph-zoom");
          if (newZoomLink) {
            newZoomLink.addEventListener("click", function (e) {
              e.preventDefault();

              // Get graph type from parent div
              const parentDiv = this.closest(".viz-item");
              let graphType = "full";
              if (parentDiv.classList.contains("top5-graph")) {
                graphType = "top5";
              }

              openLightbox("image", this.getAttribute("href"), graphType);
            });
          }
        } else {
          authorGraphsContainer.innerHTML =
            "<p>No graph data received from server.</p>";
        }
      } catch (err) {
        console.error("Error loading graph:", err);
        authorGraphsContainer.innerHTML =
          "<p>Error loading graph. Please try again.</p>";
      }
    });

    // Optional: trigger automatically on author or graph type change
    if (authorSelect && graphTypeSelect) {
      const triggerPlot = () => {
        if (authorSelect.value) {
          plotBtn.click();
        }
      };

      authorSelect.addEventListener("change", triggerPlot);
      graphTypeSelect.addEventListener("change", triggerPlot);
    }
  }
});
