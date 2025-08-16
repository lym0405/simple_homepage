# 🚀 Quick Start Guide - Subway Accessibility Contour Maps

This guide will help you quickly set up and run the subway accessibility contour map generator.

## 📋 Prerequisites

- Python 3.13+
- System packages: `python3-venv`, `python3-pip`, `python3-numpy`, `python3-scipy`, `python3-matplotlib`

## ⚡ Quick Setup

### 1. Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip python3-numpy python3-scipy python3-matplotlib
```

### 2. Install Python Packages
```bash
pip3 install --break-system-packages Flask Flask-CORS python-dotenv haversine
```

### 3. Set Up API Keys (Optional for Testing)
```bash
cp .env.example .env
# Edit .env file with your actual API keys
```

## 🧪 Test the Contour Generation

### Option 1: Run Test Script (Recommended for First Test)
```bash
python3 test_contour.py
```

This will generate 4 sample contour maps:
- `contour_강남역.png` - Gangnam Station area
- `contour_홍대입구역.png` - Hongik University Station area  
- `contour_명동역.png` - Myeongdong Station area
- `contour_서울역.png` - Seoul Station area

### Option 2: Run Flask Server
```bash
python3 app.py
```

Then open `contour_demo.html` in your browser and test with the web interface.

## 🎨 Understanding the Contour Maps

### Color Scheme (Pastel Pink-Purple)
- **Light Pink**: Short travel time (good accessibility)
- **Dark Purple**: Long travel time (poor accessibility)
- **White Dots**: Subway station locations
- **Red Star**: Starting point

### Contour Lines
- Lines represent equal travel time zones
- Numbers on lines show travel time in minutes
- Closer lines indicate steeper accessibility gradients

## 📊 Sample Output

The test script generates realistic contour maps showing:
- **Gangnam Station**: Excellent connectivity (avg 60.9 min)
- **Hongdae Station**: Good connectivity (avg 98.4 min)
- **Myeongdong Station**: Good connectivity (avg 80.7 min)
- **Seoul Station**: Good connectivity (avg 84.9 min)

## 🔧 API Endpoints

### Generate Contour Image
```bash
curl -X POST http://localhost:5000/api/contour \
  -H "Content-Type: application/json" \
  -d '{"lat": 37.498095, "lng": 127.027610}'
```

### Get Contour Data (for frontend)
```bash
curl -X POST http://localhost:5000/api/contour-data \
  -H "Content-Type: application/json" \
  -d '{"lat": 37.498095, "lng": 127.027610}'
```

## 🐛 Troubleshooting

### Common Issues

1. **Font Warnings**: These are cosmetic and don't affect functionality
2. **API Key Errors**: Use test script first, which works without API keys
3. **Permission Errors**: Use `--break-system-packages` flag with pip

### Verification Steps

1. Check if files are generated: `ls -la contour_*.png`
2. Verify images can be opened with any image viewer
3. Look for the characteristic pink-purple gradient pattern

## 🎯 Next Steps

1. **Integrate with Real APIs**: Add your ODsay and Kakao API keys
2. **Customize Visualization**: Modify colors, labels, and styling in `app.py`
3. **Expand Data**: Add more subway stations to `station_coords.json`
4. **Deploy**: Set up production environment with proper CORS and security

## 📝 Files Overview

- `app.py` - Main Flask application with contour APIs
- `test_contour.py` - Standalone test script with mock data
- `station_coords.json` - Seoul subway station coordinates
- `contour_demo.html` - Web interface for testing
- `requirements.txt` - Python dependencies

---

🎉 **You're ready to generate beautiful subway accessibility contour maps!**