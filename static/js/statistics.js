// Initialize the map
const initializeMap = () => {
    const map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    return map;
};

// Add markers for each user
const addUserMarkers = (map, userInfo) => {
    userInfo.forEach(user => {
        const marker = L.marker([user.latitude, user.longitude]).addTo(map);
        const popupContent = `
            <br>IP: ${user.public_ip}<br>
            Language: ${user.language}<br>
            Timezone: ${user.timezone} Offset: ${user.timezone_offset}<br>
            Screen Size: ${user.screen_size} Window Size: ${user.window_size}<br>
            Platform: ${user.platform} ${user.device_type}<br>
            CPU Cores: ${user.cpu}<br>
            GPU: ${user.gpu}
        `;
        marker.bindPopup(popupContent);
    });
};

// Function to create charts
const createChart = (ctx, type, labels, data, title) => {
    if (data.length > 0) {
        new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#007bff', '#dc3545', '#28a745', '#ffc107', '#17a2b8', '#6610f2', '#e83e8c'],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: title }
                },
                scales: { y: { beginAtZero: true } }
            }
        });
    } else {
        displayNoData(ctx);
    }
};

// Display 'No data available' message on chart
const displayNoData = (ctx) => {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.font = '20px Segoe UI';
    ctx.fillText('No data available', ctx.canvas.width / 2 - 100, ctx.canvas.height / 2);
};

// Aggregate user data
const aggregateData = (userInfo, key) => {
    return userInfo.reduce((acc, user) => {
        const value = user[key];
        if (value) {
            acc[value] = (acc[value] || 0) + 1;
        }
        return acc;
    }, {});
};

// Initialize charts
const initCharts = (userInfo) => {
    const chartsConfig = [
        { key: 'platform', type: 'pie', title: 'User Platform Distribution', canvasId: 'userChart' },
        { key: 'isp', type: 'bar', title: 'ISP Distribution', canvasId: 'ispChart' },
        { key: 'device_type', type: 'pie', title: 'Device Type Distribution', canvasId: 'deviceChart' },
        { key: 'browser_name', type: 'bar', title: 'Browser Distribution', canvasId: 'browserChart' },
        { key: 'installed_plugins', type: 'bar', title: 'Installed Plugins Distribution', canvasId: 'installedPluginsChart', isPlugins: true },
    ];

    chartsConfig.forEach(({ key, type, title, canvasId, isPlugins }) => {
        const data = isPlugins ? aggregateInstalledPlugins(userInfo) : aggregateData(userInfo, key);
        const ctx = document.getElementById(canvasId).getContext('2d');
        createChart(ctx, type, Object.keys(data), Object.values(data), title);
    });

    // Create time on page distribution chart
    const timeOnPage = userInfo.map(user => user.time_on_page);
    const ctxTimeOnPage = document.getElementById('timeOnPageChart').getContext('2d');
    createChart(ctxTimeOnPage, 'line', timeOnPage.map((_, index) => index + 1), timeOnPage, 'Time on Page Distribution');
};

// Aggregate installed plugins data
const aggregateInstalledPlugins = (userInfo) => {
    const installedPlugins = {};
    userInfo.forEach(user => {
        if (user.installed_plugins) {
            user.installed_plugins.split(',').forEach(plugin => {
                const trimmedPlugin = plugin.trim();
                installedPlugins[trimmedPlugin] = (installedPlugins[trimmedPlugin] || 0) + 1;
            });
        }
    });
    return installedPlugins;
};

// Initialize the application
const init = (userInfo) => {
    const map = initializeMap();
    addUserMarkers(map, userInfo);
    initCharts(userInfo);
};

init(userInfo);
