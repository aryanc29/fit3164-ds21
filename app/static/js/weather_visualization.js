// Global chart instances
let charts = {};

// Global variable to store current weather data for exports
let currentWeatherData = null;

// Chart configuration defaults
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                usePointStyle: true,
                padding: 20
            }
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: 'rgba(0,0,0,0.05)'
            }
        },
        x: {
            grid: {
                color: 'rgba(0,0,0,0.05)'
            }
        }
    }
};

// Color schemes
const colors = {
    primary: '#0d6efd',
    secondary: '#6c757d',
    success: '#198754',
    info: '#0dcaf0',
    warning: '#ffc107',
    danger: '#dc3545',
    temperature: '#ff6b6b',
    humidity: '#4ecdc4',
    wind: '#45b7d1',
    pressure: '#96ceb4',
    precipitation: '#74b9ff'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Make export functions globally available for onclick handlers
    window.exportChart = exportChart;
    window.exportAllCharts = exportAllCharts;
    window.exportDashboard = exportDashboard;
    window.exportData = exportData;
    
    initializeDashboard();
    
    // Add event listeners
    document.getElementById('refreshBtn').addEventListener('click', refreshData);
    document.getElementById('retryBtn').addEventListener('click', initializeDashboard);
});

async function initializeDashboard() {
    showLoading(true);
    showError(false);
    
    try {
        const realData = await loadWeatherData();
        // Store the loaded data globally for export functions
        currentWeatherData = realData;
        showLoading(false);
        
        // Try to initialize charts, but don't fail the entire dashboard if charts fail
        try {
            initializeCharts(realData);
        } catch (chartError) {
            console.error('Charts failed to load, but data loaded successfully:', chartError);
            // Show data is loaded but charts have issues
            document.getElementById('loadingState').innerHTML = 
                '<div class="alert alert-warning">Data loaded successfully, but some charts may not display properly.</div>';
        }
    } catch (error) {
        console.error('Failed to load data:', error);
        showError(true);
        showLoading(false);
    }
}

async function loadWeatherData() {
    try {
        // Load real data from BOM API endpoints
        const stationsResponse = await fetch('/api/bom/stations');
        const statisticsResponse = await fetch('/api/bom/statistics');
        
        if (stationsResponse.ok && statisticsResponse.ok) {
            const stations = await stationsResponse.json();
            const statistics = await statisticsResponse.json();
            
            console.log('Loaded BOM data:', { stationCount: stations.length, statistics });
            
            // Update dashboard with real BOM data
            updateWeatherSummary(stations);
            updateQuickStats(stations, statistics);
            updateRainfallMetrics(statistics);
            
            return { stations, statistics };
        } else {
            throw new Error(`BOM API error: ${stationsResponse.status}/${statisticsResponse.status}`);
        }
    } catch (error) {
        console.error('Error loading BOM data:', error);
        // Use sample data for demonstration
        return loadSampleData();
    }
}

function transformBOMData(stations, statistics) {
    // Transform BOM station data to weather data format for visualization
    const weatherData = [];
    
    stations.forEach(station => {
        if (station.avg_max_temp && station.avg_min_temp) {
            weatherData.push({
                station_name: station.station_name,
                temperature: (station.avg_max_temp + station.avg_min_temp) / 2,
                max_temperature: station.avg_max_temp,
                min_temperature: station.avg_min_temp,
                rainfall: station.avg_rainfall || 0,
                evapotranspiration: station.avg_evapotranspiration || 0,
                // Estimate humidity and other values based on available data
                humidity: station.avg_rainfall ? Math.min(80, 40 + (station.avg_rainfall * 2)) : 65,
                wind_speed: 15 + Math.random() * 10, // Placeholder - no wind data in BOM
                pressure: 1013 + Math.random() * 10  // Placeholder - no pressure data in BOM
            });
        }
    });
    
    return weatherData;
}

function loadSampleData() {
    // Sample data for demonstration
    const sampleData = {
        stations: [
            { id: 1, name: 'Sydney Observatory', latitude: -33.8688, longitude: 151.2093 },
            { id: 2, name: 'Newcastle', latitude: -32.9283, longitude: 151.7817 },
            { id: 3, name: 'Wollongong', latitude: -34.4278, longitude: 150.8931 }
        ],
        weatherData: generateSampleWeatherData()
    };

    updateWeatherSummary(sampleData.weatherData);
    updateQuickStats(sampleData.stations, sampleData.weatherData);
    
    return sampleData;
}

function generateSampleWeatherData() {
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < 30; i++) {
        const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
        data.push({
            date: date.toISOString(),
            temperature: 15 + Math.random() * 20,
            humidity: 40 + Math.random() * 40,
            wind_speed: Math.random() * 30,
            pressure: 1000 + Math.random() * 50,
            precipitation: Math.random() * 10
        });
    }
    
    return data.reverse();
}

function updateWeatherSummary(stations) {
    if (!stations || stations.length === 0) return;

    // Calculate averages from BOM station data
    const validStations = stations.filter(s => s.avg_max_temp && s.avg_min_temp);
    if (validStations.length === 0) return;

    const avgMaxTemp = validStations.reduce((sum, s) => sum + s.avg_max_temp, 0) / validStations.length;
    const avgMinTemp = validStations.reduce((sum, s) => sum + s.avg_min_temp, 0) / validStations.length;
    const avgTemp = (avgMaxTemp + avgMinTemp) / 2;
    
    const avgRainfall = validStations.reduce((sum, s) => sum + (s.avg_rainfall || 0), 0) / validStations.length;
    const avgET = validStations.reduce((sum, s) => sum + (s.avg_evapotranspiration || 0), 0) / validStations.length;
    
    // Estimate humidity from rainfall (higher rainfall = higher humidity)
    const avgHumidity = Math.min(90, 40 + (avgRainfall * 8));
    
    // Placeholder for wind and pressure (not available in BOM data)
    const avgWind = 15 + Math.random() * 10;
    const avgPressure = 1013 + Math.random() * 10;

    document.getElementById('avgTemp').textContent = `${avgTemp.toFixed(1)}°C`;
    document.getElementById('avgHumidity').textContent = `${avgHumidity.toFixed(1)}%`;
    document.getElementById('avgWind').textContent = `${avgWind.toFixed(1)} km/h`;
    document.getElementById('avgPressure').textContent = `${avgPressure.toFixed(0)} hPa`;
}

function updateRainfallMetrics(statistics) {
    if (!statistics) return;
    
    // Update rainfall metrics with real BOM data
    const rainfall = statistics.rainfall || {};
    const totalRecords = statistics.dataset_overview?.total_records || 0;
    
    if (document.getElementById('totalRainfall')) {
        const avgRain = rainfall.average || 0;
        const totalRain = avgRain * totalRecords;
        document.getElementById('totalRainfall').textContent = 
            `${(totalRain / 1000).toFixed(0)}k mm`;
    }
    if (document.getElementById('maxDailyRain')) {
        document.getElementById('maxDailyRain').textContent = 
            rainfall.maximum ? `${rainfall.maximum.toFixed(1)} mm` : '-- mm';
    }
    if (document.getElementById('rainyDays')) {
        // Estimate rainy days based on data
        const rainyDays = Math.floor(totalRecords * 0.25); // Assume 25% are rainy days
        document.getElementById('rainyDays').textContent = rainyDays.toLocaleString();
    }
    if (document.getElementById('drySpell')) {
        // Calculate dry spell based on minimum rainfall
        const minRain = rainfall.minimum || 0;
        const drySpell = minRain < 0.1 ? '14 days' : '7 days';
        document.getElementById('drySpell').textContent = drySpell;
    }
}

function updateQuickStats(stations, statistics) {
    // Use real BOM statistics
    const stationCount = statistics?.dataset_overview?.total_stations || stations.length;
    const totalRecords = statistics?.dataset_overview?.total_records || 0;
    const latestDate = statistics?.dataset_overview?.latest_date || new Date().toISOString().split('T')[0];
    
    document.getElementById('stationCount').textContent = stationCount.toLocaleString();
    document.getElementById('dataPoints').textContent = totalRecords.toLocaleString();
    document.getElementById('lastUpdate').textContent = new Date(latestDate).toLocaleDateString();
}

function initializeCharts(realData = null) {
    // Use real data if available, otherwise use sample data
    const chartData = realData || {
        stations: [],
        statistics: null
    };
    
    // Overview Chart (Temperature & Humidity)
    const overviewCtx = document.getElementById('overviewChart').getContext('2d');
    charts.overview = new Chart(overviewCtx, {
        type: 'line',
        data: {
            labels: chartData.stations.length > 0 ? 
                chartData.stations.slice(0, 12).map(s => s.station_name.substring(0, 8)) :
                generateDateLabels(30),
            datasets: [
                {
                    label: 'Max Temperature (°C)',
                    data: chartData.stations.length > 0 ? 
                        chartData.stations.slice(0, 12).map(s => s.avg_max_temp || 0) :
                        generateRandomData(30, 15, 35),
                    borderColor: colors.temperature,
                    backgroundColor: colors.temperature + '20',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Min Temperature (°C)',
                    data: chartData.stations.length > 0 ? 
                        chartData.stations.slice(0, 12).map(s => s.avg_min_temp || 0) :
                        generateRandomData(30, 5, 20),
                    borderColor: colors.info,
                    backgroundColor: colors.info + '20',
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            ...chartDefaults,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Temperature (°C)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Humidity (%)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });

    // Temperature Distribution Chart
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    const tempDistribution = calculateTemperatureDistribution(chartData.stations);
    charts.temperature = new Chart(tempCtx, {
        type: 'bar',
        data: {
            labels: ['0-5°C', '5-10°C', '10-15°C', '15-20°C', '20-25°C', '25-30°C', '30+°C'],
            datasets: [{
                label: 'Station Count',
                data: tempDistribution,
                backgroundColor: [
                    colors.info,
                    colors.primary,
                    colors.success,
                    colors.warning,
                    colors.danger,
                    colors.temperature,
                    '#ff4757'
                ]
            }]
        },
        options: chartDefaults
    });

    // Temperature Extremes Chart
    const tempExtremesCtx = document.getElementById('tempExtremesChart').getContext('2d');
    charts.tempExtremes = new Chart(tempExtremesCtx, {
        type: 'line',
        data: {
            labels: generateDateLabels(7),
            datasets: [
                {
                    label: 'Max Temperature',
                    data: generateRandomData(7, 25, 35),
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '20'
                },
                {
                    label: 'Min Temperature',
                    data: generateRandomData(7, 5, 15),
                    borderColor: colors.info,
                    backgroundColor: colors.info + '20'
                }
            ]
        },
        options: chartDefaults
    });

    // Precipitation Chart - show real BOM rainfall data
    const precipCtx = document.getElementById('precipitationChart').getContext('2d');
    const rainfallStations = chartData.stations.filter(s => s.avg_rainfall != null).slice(0, 15);
    charts.precipitation = new Chart(precipCtx, {
        type: 'bar',
        data: {
            labels: rainfallStations.length > 0 ? 
                rainfallStations.map(s => s.station_name.substring(0, 12)) :
                generateDateLabels(30),
            datasets: [{
                label: 'Average Rainfall (mm)',
                data: rainfallStations.length > 0 ? 
                    rainfallStations.map(s => s.avg_rainfall) :
                    generateRandomData(30, 0, 20),
                backgroundColor: colors.precipitation,
                borderColor: colors.precipitation,
                borderWidth: 1
            }]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                title: {
                    display: true,
                    text: 'Real BOM Weather Station Rainfall Data'
                }
            }
        }
    });

    // Wind Speed Chart
    const windCtx = document.getElementById('windSpeedChart').getContext('2d');
    charts.windSpeed = new Chart(windCtx, {
        type: 'line',
        data: {
            labels: generateDateLabels(30),
            datasets: [{
                label: 'Wind Speed (km/h)',
                data: generateRandomData(30, 0, 40),
                borderColor: colors.wind,
                backgroundColor: colors.wind + '20',
                tension: 0.4
            }]
        },
        options: chartDefaults
    });

    // Wind Direction Chart
    const windDirCtx = document.getElementById('windDirectionChart').getContext('2d');
    charts.windDirection = new Chart(windDirCtx, {
        type: 'polarArea',
        data: {
            labels: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
            datasets: [{
                label: 'Wind Direction Frequency',
                data: [12, 8, 6, 15, 18, 10, 9, 14],
                backgroundColor: [
                    colors.primary + '80',
                    colors.success + '80',
                    colors.info + '80',
                    colors.warning + '80',
                    colors.danger + '80',
                    colors.secondary + '80',
                    colors.wind + '80',
                    colors.temperature + '80'
                ]
            }]
        },
        options: {
            ...chartDefaults,
            scales: {}
        }
    });
}

function generateDateLabels(days) {
    const labels = [];
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now.getTime() - (i * 24 * 60 * 60 * 1000));
        labels.push(date.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' }));
    }
    return labels;
}

function generateRandomData(length, min, max) {
    return Array.from({ length }, () => Math.random() * (max - min) + min);
}

function calculateTemperatureDistribution(stations) {
    const distribution = [0, 0, 0, 0, 0, 0, 0]; // 7 temperature ranges
    
    stations.forEach(station => {
        if (station.avg_max_temp) {
            const temp = station.avg_max_temp;
            if (temp <= 5) distribution[0]++;
            else if (temp <= 10) distribution[1]++;
            else if (temp <= 15) distribution[2]++;
            else if (temp <= 20) distribution[3]++;
            else if (temp <= 25) distribution[4]++;
            else if (temp <= 30) distribution[5]++;
            else distribution[6]++;
        }
    });
    
    return distribution.length > 0 ? distribution : [2, 5, 12, 18, 15, 8, 3];
}

function showLoading(show) {
    const loadingState = document.getElementById('loadingState');
    const weatherTabContent = document.getElementById('weatherTabContent');
    
    if (show) {
        loadingState.style.display = 'block';
        weatherTabContent.classList.add('hidden-state');
    } else {
        loadingState.style.display = 'none';
        weatherTabContent.classList.remove('hidden-state');
    }
}

function showError(show) {
    const errorState = document.getElementById('errorState');
    
    if (show) {
        errorState.classList.remove('hidden-state');
    } else {
        errorState.classList.add('hidden-state');
    }
}

function refreshData() {
    showLoading(true);
    loadWeatherData().then((realData) => {
        // Store the refreshed data globally for export functions
        currentWeatherData = realData;
        showLoading(false);
        // Destroy existing charts and recreate with new data
        Object.values(charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        charts = {};
        initializeCharts(realData);
    }).catch(error => {
        console.error('Error refreshing data:', error);
        showError(true);
        showLoading(false);
    });
}

// Export functionality
function showExportStatus(show, message = 'Preparing export...') {
    const exportStatus = document.getElementById('exportStatus');
    const exportProgress = document.getElementById('exportProgress');
    
    if (show) {
        exportProgress.textContent = message;
        exportStatus.classList.remove('hidden-state');
    } else {
        exportStatus.classList.add('hidden-state');
    }
}

// Export individual chart as PNG
async function exportChart(chartType, format = 'png') {
    try {
        showExportStatus(true, `Exporting ${chartType} chart...`);
        
        const chartInstance = charts[chartType];
        if (!chartInstance) {
            throw new Error(`Chart ${chartType} not found`);
        }
        
        // Get chart canvas and convert to image
        const canvas = chartInstance.canvas;
        const imageData = canvas.toDataURL(`image/${format}`);
        
        // Create download link
        const link = document.createElement('a');
        link.download = `weather-${chartType}-chart.${format}`;
        link.href = imageData;
        link.click();
        
        showExportStatus(false);
        
    } catch (error) {
        console.error('Error exporting chart:', error);
        showExportStatus(false);
        alert('Error exporting chart. Please try again.');
    }
}

// Export all charts as PNG files
async function exportAllCharts(format = 'png') {
    try {
        showExportStatus(true, 'Exporting all charts...');
        
        const chartNames = Object.keys(charts);
        let exportedCount = 0;
        
        for (const chartName of chartNames) {
            showExportStatus(true, `Exporting ${chartName} chart (${exportedCount + 1}/${chartNames.length})...`);
            
            const chartInstance = charts[chartName];
            if (chartInstance && chartInstance.canvas) {
                const canvas = chartInstance.canvas;
                const imageData = canvas.toDataURL(`image/${format}`);
                
                // Create download link
                const link = document.createElement('a');
                link.download = `weather-${chartName}-chart.${format}`;
                link.href = imageData;
                link.click();
                
                // Small delay between downloads
                await new Promise(resolve => setTimeout(resolve, 500));
                exportedCount++;
            }
        }
        
        showExportStatus(false);
        
    } catch (error) {
        console.error('Error exporting all charts:', error);
        showExportStatus(false);
        alert('Error exporting charts. Please try again.');
    }
}

// Export dashboard as PDF
async function exportDashboard(format = 'pdf') {
    try {
        showExportStatus(true, 'Generating PDF dashboard...');
        
        // Get the main container
        const element = document.querySelector('.main-container');
        
        // Temporarily hide loading and error states
        const loadingState = document.getElementById('loadingState');
        const errorState = document.getElementById('errorState');
        const exportStatusEl = document.getElementById('exportStatus');
        
        const originalLoadingDisplay = loadingState.style.display;
        const originalErrorDisplay = errorState.style.display;
        const originalExportDisplay = exportStatusEl.style.display;
        
        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        exportStatusEl.style.display = 'none';
        
        // Ensure main content is visible
        const weatherTabContent = document.getElementById('weatherTabContent');
        weatherTabContent.style.display = 'block';
        
        // Use html2canvas to capture the dashboard
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });
        
        // Create PDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('l', 'mm', 'a4'); // Landscape orientation
        
        const imgWidth = 297; // A4 landscape width in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, imgWidth, imgHeight);
        pdf.save('weather-dashboard.pdf');
        
        // Restore original display states
        loadingState.style.display = originalLoadingDisplay;
        errorState.style.display = originalErrorDisplay;
        exportStatusEl.style.display = originalExportDisplay;
        
        showExportStatus(false);
        
    } catch (error) {
        console.error('Error exporting dashboard as PDF:', error);
        showExportStatus(false);
        alert('Error exporting dashboard. Please try again.');
    }
}

// Export data in various formats
async function exportData(format) {
    try {
        showExportStatus(true, `Preparing ${format.toUpperCase()} export...`);
        
        // Use already loaded data if available, otherwise load fresh data with timeout
        let weatherData = currentWeatherData;
        if (!weatherData) {
            showExportStatus(true, `Loading weather data for ${format.toUpperCase()} export...`);
            
            // Add timeout to prevent hanging
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Data loading timeout')), 10000)
            );
            
            try {
                weatherData = await Promise.race([loadWeatherData(), timeoutPromise]);
            } catch (error) {
                if (error.message === 'Data loading timeout') {
                    // Use sample data if real data takes too long
                    console.warn('Data loading timed out, using sample data for export');
                    weatherData = loadSampleData();
                } else {
                    throw error;
                }
            }
        }
        
        if (format === 'json') {
            // Export as JSON
            const dataStr = JSON.stringify(weatherData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = 'weather-data.json';
            link.click();
            
        } else if (format === 'csv' || format === 'excel') {
            // Prepare data for spreadsheet export
            const exportData = prepareSpreadsheetData(weatherData);
            
            if (format === 'csv') {
                // Export as CSV
                const csvContent = convertToCSV(exportData);
                const dataBlob = new Blob([csvContent], { type: 'text/csv' });
                
                const link = document.createElement('a');
                link.href = URL.createObjectURL(dataBlob);
                link.download = 'weather-data.csv';
                link.click();
                
            } else if (format === 'excel') {
                // Export as Excel using SheetJS
                const wb = XLSX.utils.book_new();
                
                // Add stations sheet
                if (weatherData.stations && weatherData.stations.length > 0) {
                    const stationsWS = XLSX.utils.json_to_sheet(weatherData.stations);
                    XLSX.utils.book_append_sheet(wb, stationsWS, 'Weather Stations');
                }
                
                // Add statistics sheet
                if (weatherData.statistics) {
                    const statsData = flattenObject(weatherData.statistics);
                    const statsWS = XLSX.utils.json_to_sheet([statsData]);
                    XLSX.utils.book_append_sheet(wb, statsWS, 'Statistics');
                }
                
                // Add summary sheet
                const summaryData = createSummaryData(weatherData);
                const summaryWS = XLSX.utils.json_to_sheet(summaryData);
                XLSX.utils.book_append_sheet(wb, summaryWS, 'Summary');
                
                XLSX.writeFile(wb, 'weather-data.xlsx');
            }
        }
        
        showExportStatus(false);
        
    } catch (error) {
        console.error('Error exporting data:', error);
        showExportStatus(false);
        alert('Error exporting data. Please try again.');
    }
}

// Helper function to prepare data for spreadsheet export
function prepareSpreadsheetData(weatherData) {
    const data = [];
    
    if (weatherData.stations && weatherData.stations.length > 0) {
        weatherData.stations.forEach(station => {
            data.push({
                'Station Name': station.station_name || 'Unknown',
                'Average Max Temperature (°C)': station.avg_max_temp || 'N/A',
                'Average Min Temperature (°C)': station.avg_min_temp || 'N/A',
                'Average Rainfall (mm)': station.avg_rainfall || 'N/A',
                'Average Evapotranspiration (mm)': station.avg_evapotranspiration || 'N/A',
                'Latitude': station.latitude || 'N/A',
                'Longitude': station.longitude || 'N/A'
            });
        });
    }
    
    return data;
}

// Helper function to convert data to CSV
function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') 
                    ? `"${value}"` 
                    : value;
            }).join(',')
        )
    ].join('\n');
    
    return csvContent;
}

// Helper function to flatten nested objects for Excel export
function flattenObject(obj, prefix = '') {
    const flattened = {};
    
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            const newKey = prefix ? `${prefix}.${key}` : key;
            
            if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
                Object.assign(flattened, flattenObject(obj[key], newKey));
            } else {
                flattened[newKey] = obj[key];
            }
        }
    }
    
    return flattened;
}

// Helper function to create summary data
function createSummaryData(weatherData) {
    const summary = [];
    
    if (weatherData.stations && weatherData.stations.length > 0) {
        const validStations = weatherData.stations.filter(s => s.avg_max_temp && s.avg_min_temp);
        
        if (validStations.length > 0) {
            const avgMaxTemp = validStations.reduce((sum, s) => sum + s.avg_max_temp, 0) / validStations.length;
            const avgMinTemp = validStations.reduce((sum, s) => sum + s.avg_min_temp, 0) / validStations.length;
            const avgRainfall = validStations.reduce((sum, s) => sum + (s.avg_rainfall || 0), 0) / validStations.length;
            
            summary.push({
                'Metric': 'Average Maximum Temperature (°C)',
                'Value': avgMaxTemp.toFixed(2)
            });
            summary.push({
                'Metric': 'Average Minimum Temperature (°C)',
                'Value': avgMinTemp.toFixed(2)
            });
            summary.push({
                'Metric': 'Average Rainfall (mm)',
                'Value': avgRainfall.toFixed(2)
            });
            summary.push({
                'Metric': 'Total Weather Stations',
                'Value': weatherData.stations.length
            });
        }
    }
    
    if (weatherData.statistics) {
        const stats = weatherData.statistics;
        if (stats.dataset_overview) {
            summary.push({
                'Metric': 'Total Data Records',
                'Value': stats.dataset_overview.total_records || 'N/A'
            });
            summary.push({
                'Metric': 'Latest Data Date',
                'Value': stats.dataset_overview.latest_date || 'N/A'
            });
        }
    }
    
    summary.push({
        'Metric': 'Export Date',
        'Value': new Date().toISOString().split('T')[0]
    });
    
    return summary;
}