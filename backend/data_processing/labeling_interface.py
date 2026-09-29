"""
labeling_interface.py

Simple web-based expert labeling interface for tennis injury risk assessment.
Uses Flask for compatibility with existing dependencies.

Usage:
    python -m data_processing.labeling_interface
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import json
from pathlib import Path
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Configuration
DATA_DIR = Path(__file__).parent
DATASET_PATH = DATA_DIR / 'enhanced_tennis_dataset.csv'
LABELS_PATH = DATA_DIR / 'expert_labels.csv'
LABELING_BATCH_PATH = DATA_DIR / 'labeling_batch.csv'

class LabelingManager:
    def __init__(self):
        self.dataset = None
        self.labels = None
        self.current_batch = None
        self.load_data()
    
    def load_data(self):
        """Load dataset and existing labels"""
        if DATASET_PATH.exists():
            self.dataset = pd.read_csv(DATASET_PATH)
            print(f"Loaded dataset: {len(self.dataset)} samples")
        else:
            print("Dataset not found. Run enhanced_dataset_processor first.")
            self.dataset = pd.DataFrame()
        
        if LABELS_PATH.exists():
            self.labels = pd.read_csv(LABELS_PATH)
            print(f"Loaded existing labels: {len(self.labels)} samples")
        else:
            self.labels = pd.DataFrame(columns=['sample_id', 'expert_risk_level', 'expert_notes', 'labeler_id', 'timestamp'])
    
    def create_labeling_batch(self, batch_size=20, strategy='diverse'):
        """Create a batch of samples for labeling"""
        if self.dataset is None or len(self.dataset) == 0:
            return None
        
        # Get samples that haven't been labeled yet
        labeled_ids = set(self.labels['sample_id'].tolist()) if len(self.labels) > 0 else set()
        unlabeled = self.dataset[~self.dataset.index.isin(labeled_ids)]
        
        if len(unlabeled) == 0:
            return None
        
        if strategy == 'diverse':
            # Select diverse samples across risk score ranges
            unlabeled['risk_bin'] = pd.cut(unlabeled['risk_score'], bins=5, labels=['very_low', 'low', 'medium', 'high', 'very_high'])
            samples = unlabeled.groupby('risk_bin', group_keys=False).apply(
                lambda x: x.sample(min(len(x), batch_size // 5))
            )
        elif strategy == 'high_risk':
            # Focus on high-risk samples
            samples = unlabeled.nlargest(batch_size, 'risk_score')
        else:
            # Random sampling
            samples = unlabeled.sample(min(batch_size, len(unlabeled)))
        
        self.current_batch = samples.reset_index(drop=True)
        
        # Save batch for persistence
        self.current_batch.to_csv(LABELING_BATCH_PATH, index=False)
        
        return self.current_batch
    
    def save_label(self, sample_id, risk_level, notes, labeler_id='expert'):
        """Save an expert label"""
        new_label = {
            'sample_id': sample_id,
            'expert_risk_level': risk_level,
            'expert_notes': notes,
            'labeler_id': labeler_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.labels = pd.concat([self.labels, pd.DataFrame([new_label])], ignore_index=True)
        self.labels.to_csv(LABELS_PATH, index=False)
        
        return True
    
    def get_labeling_progress(self):
        """Get progress statistics"""
        total_samples = len(self.dataset) if self.dataset is not None else 0
        labeled_samples = len(self.labels)
        progress = (labeled_samples / total_samples * 100) if total_samples > 0 else 0
        
        return {
            'total_samples': total_samples,
            'labeled_samples': labeled_samples,
            'progress_percentage': progress,
            'remaining_samples': total_samples - labeled_samples
        }

# Global labeling manager
labeling_manager = LabelingManager()

@app.route('/')
def index():
    """Main labeling interface"""
    progress = labeling_manager.get_labeling_progress()
    return render_template('labeling_interface.html', progress=progress)

@app.route('/api/batch', methods=['GET', 'POST'])
def api_batch():
    """Create or get current labeling batch"""
    if request.method == 'POST':
        batch_size = int(request.form.get('batch_size', 20))
        strategy = request.form.get('strategy', 'diverse')
        
        batch = labeling_manager.create_labeling_batch(batch_size, strategy)
        
        if batch is not None:
            return jsonify({
                'success': True,
                'batch_size': len(batch),
                'samples': batch.to_dict('records')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No unlabeled samples available'
            })
    else:
        # Get current batch
        if LABELING_BATCH_PATH.exists():
            batch = pd.read_csv(LABELING_BATCH_PATH)
            return jsonify({
                'success': True,
                'batch_size': len(batch),
                'samples': batch.to_dict('records')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No active batch. Create a batch first.'
            })

@app.route('/api/label', methods=['POST'])
def api_label():
    """Save a label"""
    data = request.json
    sample_id = data.get('sample_id')
    risk_level = data.get('risk_level')
    notes = data.get('notes', '')
    labeler_id = data.get('labeler_id', 'expert')
    
    if labeling_manager.save_label(sample_id, risk_level, notes, labeler_id):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to save label'})

@app.route('/api/progress')
def api_progress():
    """Get labeling progress"""
    progress = labeling_manager.get_labeling_progress()
    return jsonify(progress)

@app.route('/api/statistics')
def api_statistics():
    """Get labeling statistics"""
    if len(labeling_manager.labels) == 0:
        return jsonify({'success': False, 'message': 'No labels yet'})
    
    # Label distribution
    label_dist = labeling_manager.labels['expert_risk_level'].value_counts()
    
    # Labels by action
    if 'action' in labeling_manager.dataset.columns:
        labeled_ids = labeling_manager.labels['sample_id'].tolist()
        labeled_samples = labeling_manager.dataset[labeling_manager.dataset.index.isin(labeled_ids)]
        action_dist = labeled_samples['action'].value_counts()
    else:
        action_dist = {}
    
    return jsonify({
        'success': True,
        'label_distribution': label_dist.to_dict(),
        'action_distribution': action_dist.to_dict(),
        'total_labels': len(labeling_manager.labels)
    })

def create_templates():
    """Create HTML templates for the labeling interface"""
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Main labeling interface template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tennis Injury Risk Labeling Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .progress-bar {
            background: #e0e0e0;
            border-radius: 10px;
            padding: 3px;
            margin: 20px 0;
        }
        .progress-fill {
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 20px;
            border-radius: 7px;
            transition: width 0.3s ease;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .sample-display {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
        }
        .sample-display.active {
            display: block;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .risk-options {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .risk-option {
            flex: 1;
            min-width: 120px;
        }
        .risk-option input[type="radio"] {
            display: none;
        }
        .risk-option label {
            display: block;
            padding: 15px;
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }
        .risk-option input[type="radio"]:checked + label {
            border-color: #667eea;
            background: #e8eaf6;
        }
        .risk-option label:hover {
            border-color: #667eea;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-family: inherit;
            resize: vertical;
            min-height: 80px;
        }
        .guidelines {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .guidelines h3 {
            margin-top: 0;
            color: #856404;
        }
        .sample-counter {
            text-align: center;
            margin: 10px 0;
            font-size: 18px;
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎾 Tennis Injury Risk Labeling Interface</h1>
        <p class="subtitle">Expert review panel for biomechanical risk assessment</p>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ progress.progress_percentage }}%"></div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ progress.total_samples }}</div>
                <div class="stat-label">Total Samples</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ progress.labeled_samples }}</div>
                <div class="stat-label">Labeled Samples</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ progress.progress_percentage }}%</div>
                <div class="stat-label">Progress</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ progress.remaining_samples }}</div>
                <div class="stat-label">Remaining</div>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="createBatch('diverse')">Create Diverse Batch</button>
            <button onclick="createBatch('high_risk')">Create High-Risk Batch</button>
            <button onclick="getStatistics()">View Statistics</button>
        </div>
        
        <div class="guidelines">
            <h3>📋 Labeling Guidelines</h3>
            <ul>
                <li><strong>Safe (0)</strong>: Normal biomechanical range, no extreme angles, proper form</li>
                <li><strong>Low Risk (1)</strong>: Slightly outside optimal range but acceptable, minor concerns</li>
                <li><strong>Moderate Risk (2)</strong>: Clear biomechanical concerns (e.g., elbow > 160°, knee < 80°)</li>
                <li><strong>High Risk (3)</strong>: Dangerous movement patterns (hyperextension, valgus collapse, extreme angles)</li>
            </ul>
        </div>
        
        <div id="sampleDisplay" class="sample-display">
            <div class="sample-counter">
                Sample <span id="currentSample">0</span> of <span id="totalSamples">0</span>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Left Elbow</div>
                    <div class="metric-value" id="leftElbow">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Right Elbow</div>
                    <div class="metric-value" id="rightElbow">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Left Knee</div>
                    <div class="metric-value" id="leftKnee">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Right Knee</div>
                    <div class="metric-value" id="rightKnee">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Left Shoulder</div>
                    <div class="metric-value" id="leftShoulder">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Right Shoulder</div>
                    <div class="metric-value" id="rightShoulder">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Hip Angle</div>
                    <div class="metric-value" id="hipAngle">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Risk Score</div>
                    <div class="metric-value" id="riskScore">--</div>
                </div>
            </div>
            
            <div class="risk-options">
                <div class="risk-option">
                    <input type="radio" name="riskLevel" value="Safe" id="risk0">
                    <label for="risk0">Safe (0)</label>
                </div>
                <div class="risk-option">
                    <input type="radio" name="riskLevel" value="Low Risk" id="risk1">
                    <label for="risk1">Low Risk (1)</label>
                </div>
                <div class="risk-option">
                    <input type="radio" name="riskLevel" value="Moderate Risk" id="risk2">
                    <label for="risk2">Moderate Risk (2)</label>
                </div>
                <div class="risk-option">
                    <input type="radio" name="riskLevel" value="High Risk" id="risk3">
                    <label for="risk3">High Risk (3)</label>
                </div>
            </div>
            
            <textarea id="expertNotes" placeholder="Expert notes (optional) - describe specific concerns or observations..."></textarea>
            
            <div class="controls">
                <button onclick="saveLabel()">Save Label</button>
                <button onclick="nextSample()">Next Sample →</button>
                <button onclick="skipSample()">Skip Sample</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentBatch = [];
        let currentSampleIndex = 0;
        
        async function createBatch(strategy) {
            const response = await fetch('/api/batch', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `batch_size=20&strategy=${strategy}`
            });
            const data = await response.json();
            
            if (data.success) {
                currentBatch = data.samples;
                currentSampleIndex = 0;
                displaySample();
                alert(`Created batch with ${data.batch_size} samples`);
            } else {
                alert(data.message);
            }
        }
        
        function displaySample() {
            if (currentSampleIndex >= currentBatch.length) {
                alert('Batch complete! Create a new batch or view statistics.');
                document.getElementById('sampleDisplay').classList.remove('active');
                return;
            }
            
            const sample = currentBatch[currentSampleIndex];
            
            document.getElementById('sampleDisplay').classList.add('active');
            document.getElementById('currentSample').textContent = currentSampleIndex + 1;
            document.getElementById('totalSamples').textContent = currentBatch.length;
            
            // Display metrics
            document.getElementById('leftElbow').textContent = sample.left_elbow_angle?.toFixed(1) + '°' || '--';
            document.getElementById('rightElbow').textContent = sample.right_elbow_angle?.toFixed(1) + '°' || '--';
            document.getElementById('leftKnee').textContent = sample.left_knee_angle?.toFixed(1) + '°' || '--';
            document.getElementById('rightKnee').textContent = sample.right_knee_angle?.toFixed(1) + '°' || '--';
            document.getElementById('leftShoulder').textContent = sample.left_shoulder_angle?.toFixed(1) + '°' || '--';
            document.getElementById('rightShoulder').textContent = sample.right_shoulder_angle?.toFixed(1) + '°' || '--';
            document.getElementById('hipAngle').textContent = sample.hip_angle?.toFixed(1) + '°' || '--';
            document.getElementById('riskScore').textContent = sample.risk_score?.toFixed(1) || '--';
            
            // Clear previous selection
            document.querySelectorAll('input[name="riskLevel"]').forEach(radio => radio.checked = false);
            document.getElementById('expertNotes').value = '';
        }
        
        async function saveLabel() {
            const sample = currentBatch[currentSampleIndex];
            const selectedRisk = document.querySelector('input[name="riskLevel"]:checked');
            
            if (!selectedRisk) {
                alert('Please select a risk level');
                return;
            }
            
            const response = await fetch('/api/label', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    sample_id: sample.index,
                    risk_level: selectedRisk.value,
                    notes: document.getElementById('expertNotes').value
                })
            });
            
            const data = await response.json();
            if (data.success) {
                alert('Label saved successfully!');
                nextSample();
            } else {
                alert('Failed to save label');
            }
        }
        
        function nextSample() {
            currentSampleIndex++;
            displaySample();
        }
        
        function skipSample() {
            currentSampleIndex++;
            displaySample();
        }
        
        async function getStatistics() {
            const response = await fetch('/api/statistics');
            const data = await response.json();
            
            if (data.success) {
                let stats = 'Labeling Statistics:\\n\\n';
                stats += 'Label Distribution:\\n';
                for (const [level, count] of Object.entries(data.label_distribution)) {
                    stats += `  ${level}: ${count}\\n`;
                }
                stats += '\\nAction Distribution:\\n';
                for (const [action, count] of Object.entries(data.action_distribution)) {
                    stats += `  ${action}: ${count}\\n`;
                }
                stats += `\\nTotal Labels: ${data.total_labels}`;
                
                alert(stats);
            } else {
                alert(data.message);
            }
        }
        
        // Load current batch on page load
        async function loadCurrentBatch() {
            const response = await fetch('/api/batch');
            const data = await response.json();
            
            if (data.success) {
                currentBatch = data.samples;
                if (currentBatch.length > 0) {
                    displaySample();
                }
            }
        }
        
        loadCurrentBatch();
    </script>
</body>
</html>
    '''
    
    template_path = templates_dir / 'labeling_interface.html'
    with open(template_path, 'w') as f:
        f.write(html_template)
    
    print(f"Created HTML template at {template_path}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Expert labeling interface')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create templates
    create_templates()
    
    print("🎾 Starting Tennis Injury Risk Labeling Interface...")
    print(f"📊 Dataset: {len(labeling_manager.dataset)} samples")
    print(f"🏷️  Existing labels: {len(labeling_manager.labels)} samples")
    print(f"🌐 Interface will be available at http://localhost:{args.port}")
    print(f"📋 Open your browser to start labeling!")
    
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()