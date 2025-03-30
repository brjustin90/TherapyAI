/**
 * Dashboard functionality
 * For user dashboard interaction
 */

document.addEventListener('DOMContentLoaded', function() {
    const dashboardContainer = document.getElementById('dashboard-container');
    
    if (!dashboardContainer) return;
    
    // Get chart container
    const moodChartContainer = document.getElementById('mood-chart');
    
    if (moodChartContainer) {
        // Sample data - in a real app, this would come from the server
        const moodData = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Mood Score',
                data: [4, 5, 3, 4, 6, 7, 5],
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                fill: true,
                tension: 0.4
            }]
        };
        
        // Create chart if Chart.js is available
        if (window.Chart) {
            const ctx = moodChartContainer.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: moodData,
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 10,
                            title: {
                                display: true,
                                text: 'Mood (1-10)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Day'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Mood: ${context.raw}/10`;
                                }
                            }
                        }
                    }
                }
            });
        } else {
            // Fallback if Chart.js is not available
            moodChartContainer.innerHTML = '<p class="text-center">Chart visualization not available</p>';
        }
    }
    
    // Get upcoming sessions
    const upcomingSessionsContainer = document.getElementById('upcoming-sessions');
    
    if (upcomingSessionsContainer) {
        // Refresh sessions button
        const refreshBtn = document.getElementById('refresh-sessions-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
                
                // Fetch updated sessions
                fetch('/api/v1/sessions')
                    .then(response => response.json())
                    .then(data => {
                        // Update UI with new sessions
                        if (data.sessions && data.sessions.length > 0) {
                            refreshSessionsList(data.sessions);
                        } else {
                            upcomingSessionsContainer.innerHTML = '<p class="text-center">No upcoming sessions.</p>';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching sessions:', error);
                        upcomingSessionsContainer.innerHTML = '<p class="text-center text-danger">Failed to load sessions.</p>';
                    })
                    .finally(() => {
                        refreshBtn.disabled = false;
                        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                    });
            });
        }
    }
    
    // Quick mood check-in form
    const moodForm = document.getElementById('mood-check-in-form');
    
    if (moodForm) {
        moodForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const moodScore = document.getElementById('mood-score').value;
            const moodNotes = document.getElementById('mood-notes').value;
            
            // Submit mood data
            fetch('/api/v1/moods', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    score: moodScore,
                    notes: moodNotes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const alertContainer = document.getElementById('mood-alert-container');
                    alertContainer.innerHTML = `
                        <div class="alert alert-success alert-dismissible fade show">
                            Mood check-in recorded successfully!
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                    
                    // Clear form
                    document.getElementById('mood-score').value = '5';
                    document.getElementById('mood-notes').value = '';
                }
            })
            .catch(error => {
                console.error('Error submitting mood:', error);
                // Show error message
                const alertContainer = document.getElementById('mood-alert-container');
                alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show">
                        Failed to record mood check-in. Please try again.
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
            });
        });
    }
    
    // Helper function to refresh sessions list
    function refreshSessionsList(sessions) {
        if (!upcomingSessionsContainer) return;
        
        // Clear current content
        upcomingSessionsContainer.innerHTML = '';
        
        // Add each session
        sessions.forEach(session => {
            const sessionDate = new Date(session.scheduled_start);
            const sessionCard = document.createElement('div');
            sessionCard.className = 'card mb-2';
            
            sessionCard.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${session.title || 'Therapy Session'}</h5>
                    <p class="card-text">
                        <i class="far fa-calendar-alt"></i> ${sessionDate.toLocaleDateString()}
                        <i class="far fa-clock ms-3"></i> ${sessionDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </p>
                    <a href="/sessions/${session.id}" class="btn btn-sm btn-primary">View Details</a>
                </div>
            `;
            
            upcomingSessionsContainer.appendChild(sessionCard);
        });
    }
}); 