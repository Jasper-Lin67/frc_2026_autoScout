const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PASSWORD = "your-hardcoded-password-here";

// Use raw parser to handle the incoming file stream from the worker
app.use(express.raw({ type: '*/*', limit: '50mb' }));

app.all('/gateway/:processId', (req, res) => {
    const { processId } = req.params;

    // 1. Security Check
    if (req.headers['authorization'] !== PASSWORD) {
        return res.status(403).send('Unauthorized');
    }

    // 2. GET: Send Video to Worker
    if (req.method === 'GET') {
        const videoPath = path.join(__dirname, 'tasks', `video_${processId}.mp4`);
        if (fs.existsSync(videoPath)) {
            console.log(`[GET] Sending video for ID: ${processId}`);
            return res.download(videoPath);
        }
        return res.status(404).send('Video not found');
    }

    // 3. POST: Receive JSON from Worker
    if (req.method === 'POST') {
        const outputPath = path.join(__dirname, 'results', `OUT#${processId}.json`);
        
        if (!fs.existsSync('./results')) fs.mkdirSync('./results');

        // req.body is a Buffer containing the raw file data
        fs.writeFile(outputPath, req.body, (err) => {
            if (err) {
                console.error(`[!] Failed to save ${processId}:`, err);
                return res.status(500).send('Save failed');
            }
            console.log(`[POST] Saved result for ID: ${processId}`);
            res.status(200).send('Received');
        });
        return;
    }

    res.status(405).send('Method Not Allowed');
});

app.listen(3000, () => console.log('Server running on port 3000'));