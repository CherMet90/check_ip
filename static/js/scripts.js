// scripts.js
function handleEnter(event) {
    if (event.key === 'Enter') {
        fetchIPInfo();
    }
}

async function fetchIPInfo() {
    const ipAddress = document.getElementById('ipAddress').value;

    // Display the loading spinner
    document.getElementById('loadingSpinner').style.display = 'flex';
    
    // Clear old data
    const ipInfoDiv = document.getElementById('ipInfo');
    ipInfoDiv.innerHTML = '';

    try {
        const response = await fetch('/check_ip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ip: ipAddress })
        });

        const data = await response.json();
        displayInfo(data);
    } catch (error) {
        console.error('Error fetching IP information:', error);
    } finally {
        // Hide the loading spinner when the request is completed
        document.getElementById('loadingSpinner').style.display = 'none';
    }
}

function displayInfo(data) {
    const ipInfoDiv = document.getElementById('ipInfo');

    let arpStatusHTML = '';
    if (data.ip_in_arp === true) {
        arpStatusHTML = '<p style="color: red;">Найдена ARP-запись на pfSense - IP используется</p>';
    } else {
        arpStatusHTML = '<p style="color: green;">ARP-запись не найдена</p>';
    }

    let ipInNetboxHTML = '';
    if (data.ip_in_netbox === null) {
        ipInNetboxHTML = '<p>Данные в Netbox не найдены</p>';
    } else if (data.ip_in_netbox) {
        ipInNetboxHTML = `<p>Данные по Netbox: <a href="${data.ip_in_netbox}" target="_blank">${data.ip_in_netbox}</a></p>`;
    }

    ipInfoDiv.innerHTML = `
        ${arpStatusHTML}
        ${ipInNetboxHTML}
    `;
}
