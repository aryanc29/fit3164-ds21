"""
Simple test to validate JavaScript button functionality
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/test")
async def test_button():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Button Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="container mt-4">
    <h2>Station Toggle Test</h2>
    
    <button id="toggleStationsBtn" class="btn btn-outline-secondary mb-3">
        <i class="fas fa-eye-slash"></i> Hide Stations
    </button>
    
    <div id="stationCount" class="mb-2 text-muted">3 test stations</div>
    
    <div id="stationsGrid" class="row">
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5>Station 1</h5>
                    <p>Test data</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5>Station 2</h5>
                    <p>Test data</p>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5>Station 3</h5>
                    <p>Test data</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing button...');
            
            const toggleBtn = document.getElementById('toggleStationsBtn');
            const stationsGrid = document.getElementById('stationsGrid');
            const stationCount = document.getElementById('stationCount');
            
            console.log('Elements found:', {
                button: !!toggleBtn,
                grid: !!stationsGrid,
                count: !!stationCount
            });
            
            if (toggleBtn && stationsGrid) {
                let isHidden = false;
                
                toggleBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log('Button clicked! Current state:', isHidden);
                    
                    isHidden = !isHidden;
                    
                    if (isHidden) {
                        this.innerHTML = '<i class="fas fa-eye"></i> Show Stations';
                        this.classList.remove('btn-outline-secondary');
                        this.classList.add('btn-outline-success');
                        stationsGrid.classList.add('d-none');
                        stationCount.classList.add('d-none');
                    } else {
                        this.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Stations';
                        this.classList.remove('btn-outline-success');
                        this.classList.add('btn-outline-secondary');
                        stationsGrid.classList.remove('d-none');
                        stationCount.classList.remove('d-none');
                    }
                    
                    console.log('Toggle complete! New state:', isHidden);
                });
                
                console.log('Button initialized successfully!');
            } else {
                console.error('Missing elements!');
            }
        });
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)