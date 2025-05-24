document.addEventListener('DOMContentLoaded', (event) => {

    let table = document.getElementById('myTable');
    let rows = table.getElementsByTagName('tr');
    let rowCount = rows.length - 2;
    document.getElementById('rowCount').innerText = `${rowCount}`;
});

function filterSearch() {
    let searchInput = document.getElementById('search').value.toLowerCase();
    let table = document.getElementById('myTable');
    let rows = table.getElementsByTagName('tr');
    let columnSearches = table.querySelectorAll('thead tr:nth-child(2) input, thead tr:nth-child(2) select');
    let columnSearchValues = Array.from(columnSearches).map(input => input.value.toLowerCase());
    let visibleRowCount = 0;
    const specificDateInput = document.getElementById('specificDate').value;
    let specificDateObj = specificDateInput ? new Date(specificDateInput) : null;

    // Set the current date and time to midnight for consistent comparisons
    let today = new Date();
    today.setHours(0, 0, 0, 0);

    // Define the start and end of the current week
    let weekStart = new Date(today);
    weekStart.setDate(today.getDate() - today.getDay()); // Start of the week (Sunday)
    let weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6); // End of the week (Saturday
    // Define the start and end of the current month
    let monthStart = new Date(today.getFullYear(), today.getMonth(), 1); // First day of the month
    let monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of the month

    for (let i = 2; i < rows.length; i++) { // Start at 2 to skip header rows
        let cells = rows[i].getElementsByTagName('td');
        let match = false;

        if (searchInput) {
            for (let j = 0; j < cells.length; j++) {
                if (cells[j].innerText.toLowerCase().includes(searchInput)) {
                    match = true;
                    break;
                }
            }
        } else {
            match = true;
        }

        // Handle the renewal date filter from the dropdown
        let renewalDateFilter = columnSearchValues[5]; // Date filter column index

        // Get the renewal date text from the table cell
        let renewalDateText = cells[5].innerText.trim(); // Ensure there are no extra spaces
        let renewalDate = renewalDateText.split('-').reverse().join('-'); // Convert to YYYY-MM-DD format
        let renewalDateObj = new Date(renewalDate);
        renewalDateObj.setHours(0, 0, 0, 0); // Set to midnight for consistent comparison

        if (renewalDateFilter) {
            switch (renewalDateFilter) {
                case 'this-week':
                    match = (renewalDateObj >= weekStart && renewalDateObj <= weekEnd);
                    break;
                case 'this-month':
                    match = (renewalDateObj >= monthStart && renewalDateObj <= monthEnd);
                    break;
                case 'after-specific-date':
                    if (specificDateObj) {
                        match = (renewalDateObj > specificDateObj);
                    }
                    break;
                case 'before-specific-date':
                    if (specificDateObj) {
                        match = (renewalDateObj < specificDateObj);
                    }
                    break;
                default:
                    match = true; // If "All" is selected, show all rows
            }
        }

        // Check other column filters and searches
        for (let col = 0; col < columnSearchValues.length; col++) {
            if (col !== 5 && col !== 6 && columnSearchValues[col] && !cells[col].innerText.toLowerCase().includes(columnSearchValues[col])) {
                match = false;
                break;
            }
        }

        // Display or hide the row based on the match status
        rows[i].style.display = match ? '' : 'none';
        if (match) visibleRowCount++;
    }

    // Display the count of visible rows
    document.getElementById('rowCount').innerText = `${visibleRowCount}`;
}

function filterSearchOthers() {
    let searchInput = document.getElementById('search').value.toLowerCase();
    let searchSelect = document.getElementById('financialYear') ? document.getElementById('financialYear').value.toLowerCase() : null;
    let table = document.getElementById('myTable');
    let rows = table.getElementsByTagName('tr');
    let columnSearches = table.querySelectorAll('thead tr:nth-child(2) input, thead tr:nth-child(2) select');
    let columnSearchValues = Array.from(columnSearches).map(input => input.value.toLowerCase());

    if (searchSelect) {
        columnSearchValues[3] = searchSelect; // Set the financial year filter
    }

    let visibleRowCount = 0;
    for (let i = 2; i < rows.length; i++) {
        let cells = rows[i].getElementsByTagName('td');
        let match = false;

        if (searchInput) {
            for (let j = 0; j < cells.length; j++) {
                if (cells[j].innerText.toLowerCase().includes(searchInput)) {
                    match = true;
                    break;
                }
            }
        } else {
            match = true;
        }

        for (let col = 0; col < columnSearchValues.length; col++) {
            if (columnSearchValues[col] && !cells[col].innerText.toLowerCase().includes(columnSearchValues[col])) {
                match = false;
                break;
            }
        }

        if (match) {
            rows[i].style.display = '';
            visibleRowCount++;
        } else {
            rows[i].style.display = 'none';
        }
    }

    // Display the count of visible rows
    document.getElementById('rowCount').innerText = `${visibleRowCount}`;
}


function toggleDateInputs() {
    const filterDropdown = document.getElementById('renewalDateFilter');
    const dateInputContainer = document.getElementById('dateInputContainer');

    if (filterDropdown.value === 'after-specific-date' || filterDropdown.value === 'before-specific-date') {
        dateInputContainer.style.display = 'block';
    } else {
        dateInputContainer.style.display = 'none';
    }
}

let sortDirections = Array(8).fill(false); // Track sort directions for each column

function sortTable(columnIndex) {
    let table = document.getElementById('myTable');
    let rows = Array.from(table.getElementsByTagName('tr')).slice(2); // Skip the header rows
    let direction = sortDirections[columnIndex] ? 1 : -1;

    rows.sort((a, b) => {
        let cellA = a.getElementsByTagName('td')[columnIndex].innerText.trim();
        let cellB = b.getElementsByTagName('td')[columnIndex].innerText.trim();

        // Check if values are numbers
        if (!isNaN(cellA) && !isNaN(cellB)) {
            return (parseFloat(cellA) - parseFloat(cellB)) * direction;
        }

        // Check if values are dates (in DD-MM-YYYY format)
        let dateRegex = /^\d{2}-\d{2}-\d{4}$/;
        if (dateRegex.test(cellA) && dateRegex.test(cellB)) {
            let dateA = new Date(cellA.split('-').reverse().join('-'));
            let dateB = new Date(cellB.split('-').reverse().join('-'));
            return (dateA - dateB) * direction;
        }

        // Default: Sort as text (case insensitive)
        cellA = cellA.toLowerCase();
        cellB = cellB.toLowerCase();
        if (cellA < cellB) return -1 * direction;
        if (cellA > cellB) return 1 * direction;
        return 0;
    });

    // Toggle sort direction for next click
    sortDirections[columnIndex] = !sortDirections[columnIndex];

    // Reattach sorted rows to the table body
    let tbody = table.getElementsByTagName('tbody')[0];
    rows.forEach(row => tbody.appendChild(row));
}
