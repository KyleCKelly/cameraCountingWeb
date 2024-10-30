let currentPage = 0;
const itemsPerPage = 16;
let zones = [];  // Array to store created zones
let inZoneView = false;  // Flag to track if the user is in a zone view
let currentZoneId = null;  // Track the current zone being viewed

// Event listener for starting to drag a camera
function startDrag(event, cameraIndex) {
    event.dataTransfer.setData("cameraIndex", cameraIndex);
}

// Function to handle dropping a camera into a zone
function dropCameraToZone(event, zoneId) {
    event.preventDefault();
    const cameraIndex = event.dataTransfer.getData("cameraIndex");
    const zone = zones.find(z => z.id === zoneId);

    if (zone && !zone.cameras.includes(Number(cameraIndex))) {
        zone.cameras.push(Number(cameraIndex));
        updatePage();  // Update the page to reflect the camera being added to the zone
    }
}

// Function to prevent the default behavior for dragover
function allowDrop(event) {
    event.preventDefault();
}

// Show add camera form
function showAddCameraForm() {
    let ip = prompt("Enter IP for new Camera:");
    let username = prompt("Enter Username for new Camera:");
    let password = prompt("Enter Password for new Camera:");

    if (ip && username && password) {
        fetch("/add_camera", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ ip, username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePage(); // Reload page data
            } else {
                alert("Failed to add camera: " + data.error);
            }
        });
    } else {
        alert("Please fill all details for the new camera.");
    }
}

// Function to remove a camera
function removeCamera(index) {
    fetch(`/remove_camera/${index}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updatePage(); // Reload page data
        } else {
            alert("Failed to remove camera: " + data.error);
        }
    });
}

// Create a new zone
function createZone() {
    let zoneName = prompt("Enter Zone Name:");
    if (zoneName) {
        const zoneId = `zone-${zones.length}`;
        zones.push({ id: zoneId, name: zoneName, cameras: [] });
        updatePage();  // Update to display the newly created zone box
    }
}

// Remove a zone
function removeZone(zoneId) {
    zones = zones.filter(zone => zone.id !== zoneId);
    updatePage();
}

// Update the page content
function updatePage() {
    fetch("/get_cameras")
    .then(response => response.json())
    .then(data => {
        const cameraGrid = document.getElementById("camera-grid");
        cameraGrid.innerHTML = ""; // Clear grid

        if (inZoneView) {
            renderZoneView(data.cameras, currentZoneId);  // If in zone view, render only cameras in the current zone
        } else {
            renderMainDashboard(data.cameras);  // Otherwise, render the main dashboard view
        }
    })
    .catch(error => {
        console.error("Error fetching camera data:", error);
    });
}

// Render the main dashboard view
function renderMainDashboard(cameraData) {
    const cameraGrid = document.getElementById("camera-grid");
    cameraGrid.innerHTML = ""; // Clear grid

    // Render Zone Boxes First
    zones.forEach(zone => renderZoneBox(zone, cameraData, cameraGrid));

    // Render Camera Boxes Second
    cameraData.forEach((camera, index) => {
        const isAssignedToZone = zones.some(zone => zone.cameras.includes(index));
        if (!isAssignedToZone) {  // Only show unassigned cameras
            const cameraBox = document.createElement("div");
            cameraBox.className = "camera-box";
            cameraBox.draggable = true;
            cameraBox.ondragstart = (e) => e.dataTransfer.setData("cameraIndex", index);
            cameraBox.innerHTML = `
                <h3>Camera ${index + 1}</h3>
                <p>Entered: ${camera.entered}</p>
                <p>Exited: ${camera.exited}</p>
                <button onclick="removeCamera(${index})">Remove</button>
            `;
            cameraGrid.appendChild(cameraBox);
        }
    });

    // Display the Add Camera and Create Zone boxes at the end
    displayAddCameraBox(cameraGrid);
    displayCreateZoneBox(cameraGrid);

    document.getElementById("total-currently-in").textContent = `Current Occupancy: ${calculateTotalOccupancy(cameraData)}`;
}

// Render a zone box on the main dashboard
function renderZoneBox(zone, cameraData, container) {
    const zoneBox = document.createElement("div");
    zoneBox.className = "zone-box";
    zoneBox.ondrop = (event) => dropCameraToZone(event, zone.id); // Enable drop
    zoneBox.ondragover = allowDrop; // Allow dragover

    const enteredCount = zone.cameras.reduce((acc, camIdx) => acc + cameraData[camIdx].entered, 0);
    const exitedCount = zone.cameras.reduce((acc, camIdx) => acc + cameraData[camIdx].exited, 0);
    const currentlyIn = enteredCount - exitedCount;

    zoneBox.innerHTML = `
        <h3>${zone.name}</h3>
        <p>Entered: ${enteredCount}</p>
        <p>Exited: ${exitedCount}</p>
        <p>Currently In: ${currentlyIn}</p>
        <div class="button-group">
            <button onclick="enterZoneView('${zone.id}')">View Zone</button>
            ${zone.cameras.length === 0 ? `<button onclick="removeZone('${zone.id}')">Remove</button>` : ""}
        </div>
    `;
    container.appendChild(zoneBox);
}

// Render the "Add Camera" box
function displayAddCameraBox(container) {
    const addCameraBox = document.createElement("div");
    addCameraBox.className = "empty-camera-box";
    addCameraBox.innerHTML = `<span>+</span><button onclick="showAddCameraForm()">Add Camera</button>`;
    container.appendChild(addCameraBox);
}

// Render the "Create Zone" box
function displayCreateZoneBox(container) {
    const createZoneBox = document.createElement("div");
    createZoneBox.className = "empty-camera-box";
    createZoneBox.style.backgroundColor = "#b533ff";
    createZoneBox.innerHTML = `<span>+</span><button onclick="createZone()">Create Zone</button>`;
    container.appendChild(createZoneBox);
}

// Calculate the total occupancy
function calculateTotalOccupancy(cameraData) {
    return cameraData.reduce((acc, camera) => acc + camera.entered - camera.exited, 0);
}

// View a specific zone
function enterZoneView(zoneId) {
    inZoneView = true;
    currentZoneId = zoneId;
    document.getElementById("return-button").style.display = "inline-block";  // Show the Return button
    updatePage();
}

// Render the zone view
function renderZoneView(cameraData, zoneId) {
    const zone = zones.find(z => z.id === zoneId);
    if (zone) {
        const cameraGrid = document.getElementById("camera-grid");
        cameraGrid.innerHTML = "";  // Clear the grid for zone view

        zone.cameras.forEach(cameraIndex => {
            const camera = cameraData[cameraIndex];
            const cameraBox = document.createElement("div");
            cameraBox.className = "camera-box";
            cameraBox.innerHTML = `
                <h3>Camera ${cameraIndex + 1}</h3>
                <p>Entered: ${camera.entered}</p>
                <p>Exited: ${camera.exited}</p>
                <div class="button-group">
                    <button onclick="removeCamera(${cameraIndex})">Remove</button>
                    <button onclick="returnCameraToDashboard(${cameraIndex}, '${zoneId}')">Return</button>
                </div>
            `;
            cameraGrid.appendChild(cameraBox);
        });
    }
}

// Return a camera to the main dashboard from a zone
function returnCameraToDashboard(cameraIndex, zoneId) {
    const zone = zones.find(z => z.id === zoneId);
    if (zone) {
        zone.cameras = zone.cameras.filter(idx => idx !== cameraIndex);
        updatePage();
    }
}

// Return to the main dashboard
function returnToDashboard() {
    inZoneView = false;
    currentZoneId = null;
    document.getElementById("return-button").style.display = "none";  // Hide the Return button
    updatePage();
}

// Load configuration file
function loadConfig() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = event => {
        const file = event.target.files[0];
        const formData = new FormData();
        formData.append("config_file", file);

        fetch("/load_config", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updatePage();
            } else {
                alert("Failed to load config: " + data.error);
            }
        });
    };
    input.click();
}

// Export configuration
function exportConfig() {
    fetch("/export_config", {
        method: "GET"
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'camera_config.json';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        alert("Failed to export config: " + error.message);
    });
}

// Reset counts
function resetCounts() {
    fetch("/reset_counts", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Counts reset successfully.");
            updatePage();
        } else {
            alert("Failed to reset counts.");
        }
    });
}

// Set occupancy limit
function setOccupancyLimit() {
    let limit = prompt("Enter new occupancy limit:");
    if (limit) {
        fetch("/set_occupancy_limit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ occupancy_limit: limit })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert("Failed to set occupancy limit.");
            }
        });
    }
}

// Initialization on page load
document.addEventListener("DOMContentLoaded", () => {
    updatePage();
    setInterval(updatePage, 5000); // Refresh every 5 seconds

    const returnButton = document.createElement("button");
    returnButton.id = "return-button";
    returnButton.textContent = "Return";
    returnButton.style.display = "none";
    returnButton.onclick = returnToDashboard;
    document.querySelector(".bottom-buttons").appendChild(returnButton);

    // Attach event listeners to bottom buttons
    document.getElementById("next-page-button").addEventListener("click", nextPage);
    document.getElementById("prev-page-button").addEventListener("click", prevPage);
    document.getElementById("load-config-button").addEventListener("click", loadConfig);
    document.getElementById("export-config-button").addEventListener("click", exportConfig);
    document.getElementById("reset-counts-button").addEventListener("click", resetCounts);
    document.getElementById("set-occupancy-limit-button").addEventListener("click", setOccupancyLimit);
});

// Pagination controls
function nextPage() {
    currentPage++;
    updatePage();
}

function prevPage() {
    if (currentPage > 0) {
        currentPage--;
        updatePage();
    }
}