// bGeigie Import Map Visualization
class BGeigieMap {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.markers = [];
        this.heatmapLayer = null;
        this.importData = null;
    }

    // Initialize the map
    init(centerLat = 35.6762, centerLng = 139.6503, zoom = 10) {
        this.map = L.map(this.containerId).setView([centerLat, centerLng], zoom);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        return this;
    }

    // Convert CPM to µSv/h using LND7317 tube conversion factor
    cpmToMicroSvPerHour(cpm) {
        return cpm / 334;
    }

    // Get color based on µSv/h value (radiation level) - detailed logarithmic scale
    getCPMColor(cpm) {
        const microSvPerHour = this.cpmToMicroSvPerHour(cpm);
        
        // Detailed logarithmic scale with 12 levels
        if (microSvPerHour >= 100) return '#ffff00';       // Yellow: extreme (100+)
        if (microSvPerHour >= 65.54) return '#ffff80';     // Light yellow: very extreme (65.54-100)
        if (microSvPerHour >= 10) return '#ff8000';        // Orange: very high (10-65.54)
        if (microSvPerHour >= 5) return '#ff4000';         // Red-orange: high (5-10)
        if (microSvPerHour >= 1.65) return '#ff0000';      // Red: elevated high (1.65-5)
        if (microSvPerHour >= 1.0) return '#ff0080';       // Red-magenta: moderate high (1.0-1.65)
        if (microSvPerHour >= 0.43) return '#ff00ff';      // Magenta: moderate (0.43-1.0)
        if (microSvPerHour >= 0.25) return '#8000ff';      // Purple: low-moderate (0.25-0.43)
        if (microSvPerHour >= 0.14) return '#0080ff';      // Blue-cyan: elevated normal (0.14-0.25)
        if (microSvPerHour >= 0.08) return '#00ffff';      // Cyan: normal (0.08-0.14)
        if (microSvPerHour >= 0.03) return '#0000ff';      // Blue: low normal (0.03-0.08)
        return '#000000';                                   // Black: very low (< 0.03)
    }

    // Get marker size based on µSv/h value - detailed logarithmic scale
    getMarkerSize(cpm) {
        const microSvPerHour = this.cpmToMicroSvPerHour(cpm);
        if (microSvPerHour >= 100) return 12;
        if (microSvPerHour >= 65.54) return 11;
        if (microSvPerHour >= 10) return 10;
        if (microSvPerHour >= 5) return 9;
        if (microSvPerHour >= 1.65) return 8;
        if (microSvPerHour >= 1.0) return 7;
        if (microSvPerHour >= 0.43) return 6;
        if (microSvPerHour >= 0.25) return 5;
        if (microSvPerHour >= 0.14) return 4;
        if (microSvPerHour >= 0.08) return 4;
        if (microSvPerHour >= 0.03) return 3;
        return 3;
    }

    // Create radiation level legend
    createLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'radiation-legend');
            div.innerHTML = `
                <h4>Radiation Levels (µSv/h)</h4>
                <div class="legend-item"><span style="background: #ffff00"></span> ≥ 100 (Extreme)</div>
                <div class="legend-item"><span style="background: #ffff80"></span> 65.54-100 (Very Extreme)</div>
                <div class="legend-item"><span style="background: #ff8000"></span> 10-65.54 (Very High)</div>
                <div class="legend-item"><span style="background: #ff4000"></span> 5-10 (High)</div>
                <div class="legend-item"><span style="background: #ff0000"></span> 1.65-5 (Elevated High)</div>
                <div class="legend-item"><span style="background: #ff0080"></span> 1.0-1.65 (Moderate High)</div>
                <div class="legend-item"><span style="background: #ff00ff"></span> 0.43-1.0 (Moderate)</div>
                <div class="legend-item"><span style="background: #8000ff"></span> 0.25-0.43 (Low-Moderate)</div>
                <div class="legend-item"><span style="background: #0080ff"></span> 0.14-0.25 (Elevated Normal)</div>
                <div class="legend-item"><span style="background: #00ffff"></span> 0.08-0.14 (Normal)</div>
                <div class="legend-item"><span style="background: #0000ff"></span> 0.03-0.08 (Low Normal)</div>
                <div class="legend-item"><span style="background: #000000; color: white;"></span> < 0.03 (Very Low)</div>
            `;
            return div;
        };
        
        legend.addTo(this.map);
    }

    // Load and display bGeigie import data
    async loadImportData(importId) {
        try {
            const response = await fetch(`/bgeigie-imports/${importId}/measurements`);
            if (!response.ok) throw new Error('Failed to load import data');
            
            this.importData = await response.json();
            this.displayMeasurements();
            this.fitMapToBounds();
            this.createLegend();
            this.updateStats();
            
        } catch (error) {
            console.error('Error loading import data:', error);
            alert('Failed to load measurement data');
        }
    }

    // Display measurements on the map
    displayMeasurements() {
        if (!this.importData || !this.importData.measurements) return;

        // Clear existing markers
        this.clearMarkers();

        const measurements = this.importData.measurements;
        
        measurements.forEach(measurement => {
            if (measurement.latitude && measurement.longitude) {
                const marker = L.circleMarker([measurement.latitude, measurement.longitude], {
                    radius: this.getMarkerSize(measurement.cpm),
                    fillColor: this.getCPMColor(measurement.cpm),
                    color: '#000',
                    weight: 1,
                    opacity: 0.8,
                    fillOpacity: 0.7
                });

                // Create tooltip for hover and popup for click
                const microSvPerHour = this.cpmToMicroSvPerHour(measurement.cpm);
                const capturedDate = new Date(measurement.captured_at);
                
                // Tooltip content for hover
                const tooltipContent = `
                    <div class="measurement-tooltip" style="background: white; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); font-size: 12px; line-height: 1.3;">
                        <div style="position: relative;">
                            <button onclick="this.parentElement.parentElement.parentElement.style.display='none'" style="position: absolute; top: -4px; right: -4px; background: #f0f0f0; border: 1px solid #ccc; width: 20px; height: 20px; border-radius: 2px; cursor: pointer; font-size: 14px; line-height: 1;">×</button>
                            <strong>${microSvPerHour.toFixed(2)}µSv/h</strong><br>
                            <strong>${measurement.cpm}CPM</strong><br>
                            4SLog CPM<br>
                            5Log CP5s<br>
                            ${measurement.altitude || 0}m alt<br>
                            ${measurement.heading || 0}° heading<br>
                            ${capturedDate.getFullYear()}-${String(capturedDate.getMonth() + 1).padStart(2, '0')}-${String(capturedDate.getDate()).padStart(2, '0')}<br>
                            ${String(capturedDate.getHours()).padStart(2, '0')}:${String(capturedDate.getMinutes()).padStart(2, '0')}:${String(capturedDate.getSeconds()).padStart(2, '0')} UTC
                        </div>
                    </div>
                `;
                
                // Bind both tooltip (hover) and popup (click)
                marker.bindTooltip(tooltipContent, {
                    permanent: false,
                    direction: 'top',
                    offset: [0, -10],
                    className: 'custom-tooltip'
                });
                
                marker.bindPopup(tooltipContent);
                marker.addTo(this.map);
                this.markers.push(marker);
            }
        });
    }

    // Fit map view to show all measurements
    fitMapToBounds() {
        if (this.markers.length === 0) return;

        const group = new L.featureGroup(this.markers);
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    // Clear all markers from the map
    clearMarkers() {
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];
    }

    // Update statistics display
    updateStats() {
        if (!this.importData) return;

        const measurements = this.importData.measurements;
        const totalMeasurements = measurements.length;
        const avgCPM = measurements.reduce((sum, m) => sum + m.cpm, 0) / totalMeasurements;
        const maxCPM = Math.max(...measurements.map(m => m.cpm));
        const minCPM = Math.min(...measurements.map(m => m.cpm));

        // Update stats in the UI
        document.getElementById('total-measurements').textContent = totalMeasurements;
        document.getElementById('avg-cpm').textContent = avgCPM.toFixed(1);
        document.getElementById('max-cpm').textContent = maxCPM;
        document.getElementById('min-cpm').textContent = minCPM;
    }

    // Toggle between marker and heatmap view
    toggleHeatmap() {
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
            this.heatmapLayer = null;
            this.displayMeasurements();
        } else {
            this.clearMarkers();
            this.createHeatmap();
        }
    }

    // Create heatmap layer
    createHeatmap() {
        if (!this.importData) return;

        const heatmapData = this.importData.measurements
            .filter(m => m.latitude && m.longitude)
            .map(m => [m.latitude, m.longitude, m.cpm / 100]); // Normalize CPM for heatmap

        this.heatmapLayer = L.heatLayer(heatmapData, {
            radius: 20,
            blur: 15,
            maxZoom: 17,
            gradient: {
                0.0: '#00ff00',
                0.2: '#80ff00', 
                0.4: '#ffff00',
                0.6: '#ff8000',
                0.8: '#ff0000',
                1.0: '#800080'
            }
        }).addTo(this.map);
    }
}

// Initialize map when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Map will be initialized when import data is loaded
    window.bgeigieMap = new BGeigieMap('import-map');
});
