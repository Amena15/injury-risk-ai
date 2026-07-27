<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Injury Risk AI – Professional README</title>
  <style>
    /* Reset & base */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: #0b0e14;
      color: #e8edf5;
      line-height: 1.6;
      padding: 2rem 1.5rem;
    }
    .container {
      max-width: 960px;
      margin: 0 auto;
      background: #141a24;
      border-radius: 24px;
      padding: 2.5rem 3rem;
      box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }
    h1, h2, h3 {
      font-weight: 600;
      letter-spacing: -0.02em;
    }
    h1 {
      font-size: 2.8rem;
      background: linear-gradient(135deg, #7ee8fa 0%, #5b9aff 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 0.3rem;
    }
    .subtitle {
      font-size: 1.2rem;
      color: #9aa9bb;
      margin-bottom: 2rem;
      border-left: 4px solid #3b82f6;
      padding-left: 1rem;
    }
    .badge-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.7rem;
      margin-bottom: 2rem;
    }
    .badge {
      background: #1e293b;
      color: #b9c7d9;
      padding: 0.25rem 0.9rem;
      border-radius: 40px;
      font-size: 0.8rem;
      font-weight: 500;
      letter-spacing: 0.01em;
      border: 1px solid #2d3a4b;
    }
    .badge.primary {
      background: #1e3a5f;
      color: #7bc0ff;
      border-color: #2b4b7a;
    }
    hr {
      border: none;
      height: 1px;
      background: #28323f;
      margin: 2rem 0;
    }
    .section-title {
      font-size: 1.6rem;
      margin-top: 2.2rem;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }
    .section-title span {
      background: #1e293b;
      padding: 0.1rem 0.6rem;
      border-radius: 30px;
      font-size: 0.8rem;
      color: #8aa3c0;
    }
    p, li {
      color: #d1dce8;
    }
    p {
      margin-bottom: 1rem;
    }
    a {
      color: #6da8ff;
      text-decoration: none;
      border-bottom: 1px dotted #3b6a9e;
      transition: color 0.2s ease;
    }
    a:hover {
      color: #a8c9ff;
    }
    code {
      background: #0d141f;
      padding: 0.15rem 0.5rem;
      border-radius: 6px;
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 0.85rem;
      color: #d4e0f0;
      border: 1px solid #25303d;
    }
    pre {
      background: #0b111c;
      padding: 1.2rem 1.5rem;
      border-radius: 14px;
      overflow-x: auto;
      border: 1px solid #1d2a38;
      font-size: 0.85rem;
      margin-bottom: 1.5rem;
    }
    pre code {
      background: transparent;
      border: none;
      padding: 0;
      color: #d4e0f0;
    }
    ul, ol {
      padding-left: 1.6rem;
      margin: 0.6rem 0 1.5rem 0;
    }
    li {
      margin-bottom: 0.4rem;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
      margin: 1.2rem 0 2rem 0;
    }
    .card {
      background: #0f1722;
      border-radius: 16px;
      padding: 1.2rem 1.5rem;
      border: 1px solid #1f2d3d;
      transition: transform 0.2s ease;
    }
    .card:hover {
      transform: translateY(-2px);
    }
    .card h4 {
      font-size: 1rem;
      color: #bfd0e0;
      margin-bottom: 0.4rem;
    }
    .card p {
      font-size: 0.9rem;
      color: #9eb0c4;
      margin-bottom: 0;
    }
    h3 {
      margin-top: 1.5rem;
      margin-bottom: 0.5rem;
      color: #e8edf5;
    }
    .footer {
      margin-top: 3rem;
      font-size: 0.9rem;
      text-align: center;
      color: #6a7e96;
      border-top: 1px solid #1f2d3d;
      padding-top: 2rem;
    }
    @media (max-width: 640px) {
      .container {
        padding: 1.5rem;
      }
      h1 {
        font-size: 2.2rem;
      }
      .grid-2 {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <h1>🏸 Injury Risk AI</h1>
  <div class="subtitle">AI-powered tennis injury prevention – analyze movement, predict risk, stay on court.</div>

  <!-- BADGES -->
  <div class="badge-row">
    <span class="badge primary">⚡ Machine Learning</span>
    <span class="badge primary">🎯 Computer Vision</span>
    <span class="badge">📱 React Native</span>
    <span class="badge">🐍 FastAPI</span>
    <span class="badge">🧠 MediaPipe</span>
    <span class="badge">🏷️ TensorFlow Lite ready</span>
    <span class="badge">🔄 Real-time</span>
  </div>

  <hr />

  <!-- DESCRIPTION -->
  <h2 class="section-title">📖 Overview</h2>
  <p>
    <strong>Injury Risk AI</strong> is a mobile-first wellness platform for tennis players.
    Using your smartphone’s camera, it records a short video of your serve or stroke,
    runs real-time pose estimation to extract joint angles, and predicts your injury risk level
    (Low / Moderate / High) using a trained machine learning model.
  </p>
  <p>
    The app then gives you <strong>personalized corrective exercises</strong> and
    highlights the <strong>specific biomechanical issues</strong> that may lead to
    common tennis injuries like tennis elbow, shoulder impingement, or knee stress.
  </p>

  <!-- FEATURES -->
  <h2 class="section-title">✨ Key Features</h2>
  <div class="grid-2">
    <div class="card">
      <h4>🎥 Video Capture</h4>
      <p>Record 5–13 seconds of a tennis stroke using the built-in camera, or upload from your gallery.</p>
    </div>
    <div class="card">
      <h4>🧍 Pose Estimation</h4>
      <p>MediaPipe extracts 33 body landmarks, computing left/right elbow, knee, shoulder, and hip angles.</p>
    </div>
    <div class="card">
      <h4>🤖 ML Risk Prediction</h4>
      <p>Random Forest classifier (96% accuracy) trained on 260 annotated frames – predicts risk level instantly.</p>
    </div>
    <div class="card">
      <h4>📊 Actionable Feedback</h4>
      <p>Get detailed risk factors, a risk score (0–100), and tailored “prehab” exercises to correct your form.</p>
    </div>
    <div class="card">
      <h4>📈 Progress Tracking</h4>
      <p>Monitor your risk trend over time (future feature – ready for extension).</p>
    </div>
    <div class="card">
      <h4>🔒 Privacy-First</h4>
      <p>Videos are processed on-the-fly and never stored – all analysis is temporary and local.</p>
    </div>
  </div>

  <!-- TECH STACK -->
  <h2 class="section-title">🛠️ Tech Stack</h2>
  <ul>
    <li><strong>Frontend:</strong> React Native (Expo) – cross-platform mobile app with a clean, dark theme.</li>
    <li><strong>Backend:</strong> FastAPI (Python) – RESTful API serving the ML model and pose analysis.</li>
    <li><strong>Pose Estimation:</strong> MediaPipe (0.10.8) – classic <code>mp.solutions.pose</code> for fast landmark detection.</li>
    <li><strong>ML Model:</strong> Scikit-learn RandomForest – trained on joint-angle features from the Tennis Player Actions dataset.</li>
    <li><strong>Video Upload:</strong> Base64 encoding (JSON) – bypasses iOS <code>FormData</code> issues, ensures reliability.</li>
    <li><strong>Deployment:</strong> Docker-ready (backend) + Expo EAS (mobile builds).</li>
  </ul>

  <!-- INSTALLATION -->
  <h2 class="section-title">📦 Installation & Setup</h2>
  <h3>Backend (FastAPI)</h3>
  <pre><code>cd backend
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload</code></pre>
  <p>The server runs at <code>http://localhost:8000</code>. The ML model loads automatically on startup.</p>

  <h3>Frontend (React Native / Expo)</h3>
  <pre><code>cd frontend
npm install
npx expo start</code></pre>
  <p>Scan the QR code with Expo Go on your phone, or press <code>i</code> for iOS simulator / <code>a</code> for Android emulator.</p>

  <h3>Environment Variables</h3>
  <p>Create a <code>.env</code> file in the backend root (optional):</p>
  <pre><code># backend/.env
MIN_CONFIDENCE=0.5
MAX_VIDEO_SIZE_MB=20</code></pre>

  <!-- API ENDPOINTS -->
  <h2 class="section-title">🔌 API Endpoints</h2>
  <ul>
    <li><code>POST /analyze-json</code> – Upload a base64-encoded video (JSON) → returns risk analysis.</li>
    <li><code>POST /analyze</code> – Multipart video upload (alternative, but not recommended for iOS).</li>
    <li><code>GET /health</code> – Health check; reports if ML engine is available.</li>
    <li><code>POST /analyze/compare</code> – Compare ML vs rule-based outputs (debugging).</li>
  </ul>
  <p><strong>Example JSON payload:</strong></p>
  <pre><code>{
  "file": "base64_encoded_video_string",
  "filename": "serve.mp4",
  "type": "video/mp4"
}</code></pre>

  <!-- DATASET & TRAINING -->
  <h2 class="section-title">📊 Dataset & Training</h2>
  <p>
    The ML model was trained on the <strong>Tennis Player Actions Dataset</strong>
    (<a href="https://www.kaggle.com/datasets/orvile/tennis-player-actions-dataset" target="_blank">Kaggle</a>),
    which contains 2,000 images of forehand, backhand, serve, and ready positions.
    We extracted 7 joint angles per image and labelled them with our rule-based risk engine,
    then trained a RandomForest classifier achieving <strong>~96% test accuracy</strong>.
  </p>
  <p>
    To extend the model, you can use the <strong>THETIS dataset</strong> (8,374 video sequences)
    with 3D skeleton data – ideal for more advanced time-series models (LSTM / Transformers).
  </p>

  <!-- CONTRIBUTING -->
  <h2 class="section-title">🤝 Contributing</h2>
  <p>We welcome contributions! Please follow standard GitHub flow:</p>
  <ol>
    <li>Fork the repository</li>
    <li>Create a feature branch</li>
    <li>Commit your changes</li>
    <li>Open a pull request</li>
  </ol>
  <p>For major changes, please open an issue first to discuss what you would like to change.</p>

  <!-- LICENSE -->
  <h2 class="section-title">📄 License</h2>
  <p>
    This project is licensed under the <strong>MIT License</strong> – see the <code>LICENSE</code> file for details.
  </p>

  <!-- ACKNOWLEDGEMENTS -->
  <h2 class="section-title">🙏 Acknowledgements</h2>
  <ul>
    <li><a href="https://google.github.io/mediapipe/" target="_blank">MediaPipe</a> – for seamless pose estimation.</li>
    <li><a href="https://fastapi.tiangolo.com/" target="_blank">FastAPI</a> – for the lightning-fast Python API.</li>
    <li><a href="https://scikit-learn.org/" target="_blank">Scikit-learn</a> – for the RandomForest classifier.</li>
    <li><a href="https://expo.dev/" target="_blank">Expo</a> – for making React Native development a breeze.</li>
    <li><a href="https://www.kaggle.com/datasets/orvile/tennis-player-actions-dataset" target="_blank">Tennis Player Actions Dataset</a> – for providing the annotated images.</li>
  </ul>

  <!-- FOOTER -->
  <div class="footer">
    Built with ❤️ by Amena &bull; 🎾 Stay healthy, play longer.
  </div>

</div>
</body>
</html>
