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

    // Get color based on CPM value (radiation level)
    getCPMColor(cpm) {
        if (cpm <= 30) return '#00ff00';      // Green: Normal background
        if (cpm <= 50) return '#80ff00';      // Light green
        if (cpm <= 100) return '#ffff00';     // Yellow: Elevated
        if (cpm <= 200) return '#ff8000';     // Orange: High
        if (cpm <= 500) return '#ff4000';     // Red-orange: Very high
        if (cpm <= 1000) return '#ff0000';    // Red: Dangerous
        return '#800080';                     // Purple: Extremely high
    }

    // Get marker size based on CPM value
    getMarkerSize(cpm) {
        if (cpm <= 30) return 4;
        if (cpm <= 100) return 6;
        if (cpm <= 500) return 8;
        return 10;
    }

    // Create radiation level legend
    createLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = function(map) {
            const div = L.DomUtil.create('div', 'radiation-legend');
            div.innerHTML = `
                <h4>Radiation Levels (CPM)</h4>
                <div class="legend-item"><span style="background: #00ff00"></span> 0-30 (Normal)</div>
                <div class="legend-item"><span style="background: #80ff00"></span> 31-50 (Low)</div>
                <div class="legend-item"><span style="background: #ffff00"></span> 51-100 (Elevated)</div>
                <div class="legend-item"><span style="background: #ff8000"></span> 101-200 (High)</div>
                <div class="legend-item"><span style="background: #ff4000"></span> 201-500 (Very High)</div>
                <div class="legend-item"><span style="background: #ff0000"></span> 501-1000 (Dangerous)</div>
                <div class="legend-item"><span style="background: #800080"></span> >1000 (Extreme)</div>
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

                // Create popup with measurement details
                const popupContent = `
                    <div class="measurement-popup">
                        <h5>Measurement Details</h5>
                        <p><strong>CPM:</strong> ${measurement.cpm}</p>
                        <p><strong>Location:</strong> ${measurement.latitude.toFixed(6)}, ${measurement.longitude.toFixed(6)}</p>
                        <p><strong>Time:</strong> ${new Date(measurement.captured_at).toLocaleString()}</p>
                        <p><strong>GPS Quality:</strong> ${measurement.gps_fix_indicator === 'A' ? 'Valid' : 'Invalid'}</p>
                        ${measurement.altitude ? `<p><strong>Altitude:</strong> ${measurement.altitude}m</p>` : ''}
                    </div>
                `;
                
                marker.bindPopup(popupContent);
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
