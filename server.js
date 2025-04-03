const express = require('express');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const morgan = require('morgan');
const fs = require('fs');

// Create uploads directory if it doesn't exist
const uploadDir = path.join(__dirname, 'public', 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  fileFilter: (req, file, cb) => {
    const filetypes = /pdf|docx|txt/;
    const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = filetypes.test(file.mimetype);

    if (extname && mimetype) {
      return cb(null, true);
    } else {
      cb(new Error('Only PDF, DOCX, and TXT files are allowed!'));
    }
  }
});

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.post('/api/upload', upload.single('resume'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    const { spawn } = require('child_process');
    const pythonProcess = spawn('python3', [
      path.join(__dirname, 'analyze_resume.py'),
      path.join(uploadDir, req.file.filename)
    ]);

    let resultData = '';
    pythonProcess.stdout.on('data', (data) => {
      resultData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Analysis Error: ${data}`);
      // Clean up failed upload immediately
      fs.unlink(path.join(uploadDir, req.file.filename), (err) => {
        if (err) console.error('Error deleting failed upload:', err);
      });
      // Send user-friendly error message
      const errorMsg = data.toString().includes('image-based') 
        ? 'Error: PDF appears to be scanned (image-based). Please upload a text-based PDF.'
        : 'Error processing resume. Please try a different file.';
      res.status(400).json({ error: errorMsg });
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        return res.status(500).json({ 
          error: 'Analysis failed',
          details: resultData || 'Unknown error occurred'
        });
      }

      try {
        const analysis = JSON.parse(resultData);
        res.json({
          success: true,
          file: req.file.filename,
          analysis: analysis
        });

        // Clean up file after processing
        fs.unlink(path.join(uploadDir, req.file.filename), (err) => {
          if (err) console.error('Error deleting file:', err);
        });
      } catch (parseError) {
        console.error('Error parsing analysis results:', parseError);
        res.status(500).json({ 
          error: 'Invalid analysis results',
          details: resultData
        });
      }
    });
  } catch (execError) {
    console.error('Error executing Python script:', execError);
    res.status(500).json({ 
      error: 'Analysis service unavailable',
      details: execError.message
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    res.status(400).json({ error: err.message });
  } else if (err) {
    res.status(500).json({ error: err.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});