(function () {
    const overlay = document.getElementById("specials-overlay");
    const overlayImg = document.getElementById("specials-image");
    const mainImg = document.getElementById("main-image");
    const nextImg = document.getElementById("next-image");

    let currentImages = IMAGES.slice();
    let currentIndex = 0;
    let specialsUrl = null;

    // --- CSS custom properties from config ---
    if (SPECIALS.enabled) {
        document.documentElement.style.setProperty("--fade-duration", SPECIALS.fade_ms + "ms");
        document.documentElement.style.setProperty("--max-opacity", SPECIALS.max_opacity);
    }

    // --- Image rotation (if multiple images per screen) ---
    if (currentImages.length > 1 && ROTATION_INTERVAL > 0 && nextImg) {
        setInterval(function () {
            currentIndex = (currentIndex + 1) % currentImages.length;
            var url = IMAGE_BASE + "/" + currentImages[currentIndex] + "?t=" + Date.now();
            nextImg.src = url;
            nextImg.onload = function () {
                nextImg.classList.remove("hidden");
                mainImg.style.opacity = "0";
                setTimeout(function () {
                    mainImg.src = url;
                    mainImg.style.opacity = "1";
                    nextImg.classList.add("hidden");
                }, 1100);
            };
        }, ROTATION_INTERVAL * 1000);
    }

    // --- Monthly specials overlay ---
    function loadSpecial() {
        return fetch("/api/specials/" + SCREEN_ID + "/current")
            .then(function (resp) {
                if (resp.ok) return resp.json();
                throw new Error("no special");
            })
            .then(function (data) {
                specialsUrl = data.url;
                overlayImg.src = specialsUrl;
            })
            .catch(function () {
                specialsUrl = null;
            });
    }

    function showSpecial() {
        if (!specialsUrl) return;
        overlay.classList.add("visible");
        setTimeout(function () {
            overlay.classList.remove("visible");
        }, SPECIALS.duration_ms);
    }

    if (SPECIALS.enabled) {
        loadSpecial();
        setTimeout(function () {
            loadSpecial().then(showSpecial);
        }, 10000);
        setInterval(function () {
            loadSpecial().then(showSpecial);
        }, SPECIALS.interval_ms);
    }

    // --- SSE live refresh ---
    var evtSource = new EventSource("/events/" + SCREEN_ID);

    evtSource.addEventListener("refresh", function () {
        fetch("/api/images/" + SCREEN_ID)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                currentImages = data.images;
                if (mainImg && currentImages.length > 0) {
                    currentIndex = 0;
                    mainImg.src = IMAGE_BASE + "/" + currentImages[0] + "?t=" + Date.now();
                }
                var noImg = document.getElementById("no-image");
                if (noImg && currentImages.length > 0) {
                    noImg.style.display = "none";
                    if (!mainImg) location.reload();
                }
            });
    });

    evtSource.addEventListener("specials", function () {
        loadSpecial();
    });

    evtSource.onerror = function () {
        setTimeout(function () {
            evtSource.close();
            evtSource = new EventSource("/events/" + SCREEN_ID);
        }, 5000);
    };
})();
