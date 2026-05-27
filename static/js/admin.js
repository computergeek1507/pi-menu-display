(function () {
    var toastEl = document.getElementById("toast");
    var toastTimer = null;

    function toast(msg, type) {
        toastEl.textContent = msg;
        toastEl.className = "toast " + (type || "success");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toastEl.className = "toast hidden";
        }, 3000);
    }

    function uploadFile(target, file) {
        var form = new FormData();
        form.append("file", file);
        return fetch("/api/upload/" + target, { method: "POST", body: form })
            .then(function (r) {
                if (!r.ok) return r.json().then(function (d) { throw new Error(d.error); });
                return r.json();
            })
            .then(function (data) {
                toast("Uploaded " + data.filename, "success");
                setTimeout(function () { location.reload(); }, 500);
            })
            .catch(function (err) {
                toast("Upload failed: " + err.message, "error");
            });
    }

    function deleteFile(target, filename) {
        if (!confirm("Delete " + filename + "?")) return;
        fetch("/api/image/" + target + "/" + filename, { method: "DELETE" })
            .then(function (r) {
                if (!r.ok) return r.json().then(function (d) { throw new Error(d.error); });
                return r.json();
            })
            .then(function () {
                toast("Deleted " + filename, "success");
                setTimeout(function () { location.reload(); }, 500);
            })
            .catch(function (err) {
                toast("Delete failed: " + err.message, "error");
            });
    }

    // File input change handlers
    document.querySelectorAll(".file-input").forEach(function (input) {
        input.addEventListener("change", function () {
            if (this.files.length > 0) {
                uploadFile(this.dataset.target, this.files[0]);
            }
        });
    });

    // Drag and drop
    document.querySelectorAll(".upload-zone").forEach(function (zone) {
        zone.addEventListener("dragover", function (e) {
            e.preventDefault();
            zone.classList.add("dragover");
        });
        zone.addEventListener("dragleave", function () {
            zone.classList.remove("dragover");
        });
        zone.addEventListener("drop", function (e) {
            e.preventDefault();
            zone.classList.remove("dragover");
            var target = zone.querySelector(".file-input").dataset.target;
            if (e.dataTransfer.files.length > 0) {
                uploadFile(target, e.dataTransfer.files[0]);
            }
        });
    });

    // Delete buttons
    document.querySelectorAll(".delete-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
            deleteFile(this.dataset.target, this.dataset.filename);
        });
    });
})();
