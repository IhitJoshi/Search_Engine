document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('results');
    const statsContainer = document.getElementById('stats');
    const loadingElement = document.getElementById('loading');
    
    // Focus on search input when page loads
    searchInput.focus();
    
    // Search when button is clicked
    searchBtn.addEventListener('click', performSearch);
    
    // Search when Enter key is pressed
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    function performSearch() {
        const query = searchInput.value.trim();
        
        if (query === '') {
            showNotification('Please enter a search query', 'error');
            return;
        }
        
        // Show loading state
        loadingElement.classList.remove('hidden');
        resultsContainer.innerHTML = '';
        statsContainer.classList.add('hidden');
        
        // Send search request to backend
        fetch('http://localhost:5000/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayResults(data, query);
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error performing search. Please try again later.', 'error');
        })
        .finally(() => {
            loadingElement.classList.add('hidden');
        });
    }
    
    function displayResults(data, query) {
        // Clear previous results
        resultsContainer.innerHTML = '';
        
        if (!data.results || data.results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search fa-2x"></i>
                    <h3>No results found for "${query}"</h3>
                    <p>Try different keywords or more general terms</p>
                </div>
            `;
            statsContainer.textContent = '0 results found';
            statsContainer.classList.remove('hidden');
            return;
        }
        
        // Update stats
        statsContainer.textContent = `Found ${data.results.length} results for "${query}"`;
        statsContainer.classList.remove('hidden');
        
        // Display results
        data.results.forEach(result => {
            const resultElement = document.createElement('div');
            resultElement.className = 'result-card';
            
            // Create result HTML
            resultElement.innerHTML = `
                <div class="result-header">
                    <span class="doc-id">Document ${result.doc_id}</span>
                    <span class="score">Score: ${result.score.toFixed(4)}</span>
                </div>
                <div class="result-content">
                    <p>${result.preview}</p>
                </div>
            `;
            
            resultsContainer.appendChild(resultElement);
        });
    }
    
    function showNotification(message, type = 'info') {
        // Remove any existing notifications
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px 20px';
        notification.style.borderRadius = '4px';
        notification.style.color = 'white';
        notification.style.zIndex = '1000';
        notification.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        
        if (type === 'error') {
            notification.style.background = '#e74c3c';
        } else {
            notification.style.background = '#2ecc71';
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});