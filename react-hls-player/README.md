# React HLS Player

A modern, responsive React application for playing HLS (HTTP Live Streaming) video streams using hls.js.

## Features

- 🎥 **HLS Stream Support**: Play HLS streams using hls.js with fallback to native HLS support
- 🎮 **User-Friendly Controls**: Easy-to-use interface with play/pause and URL input
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- 🔄 **Error Handling**: Comprehensive error handling with user-friendly messages
- ⚡ **Performance Optimized**: Efficient video loading and playback with proper cleanup

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn package manager

### Installation

1. Navigate to the react-hls-player directory:
```bash
cd react-hls-player
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Start the development server:
```bash
npm start
# or
yarn start
```

4. Open your browser and navigate to `http://localhost:3000`

## Usage

1. **Enter HLS URL**: Input a valid HLS stream URL in the text field
2. **Load Stream**: Click the "Load Stream" button to initialize the video player
3. **Control Playback**: Use the play/pause button or the video player's built-in controls
4. **Sample URL**: Click "Sample URL" to fill in a test URL (requires running HLS server)

### Example HLS URLs

The player works with any valid HLS stream. Here are some test URLs you can try:

- Local HLS Server: `http://localhost:8080/hls/{video-id}/index.m3u8`
- Apple's Sample Stream: `https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8`

## Browser Support

- **Chrome/Edge**: Full support via hls.js
- **Firefox**: Full support via hls.js  
- **Safari**: Native HLS support
- **Mobile browsers**: Responsive design with touch-friendly controls

## Technical Details

### Dependencies

- **React 18**: Modern React with hooks
- **hls.js**: JavaScript library for HLS video streaming
- **Create React App**: Development and build tooling

### Key Features

#### HLS.js Integration
- Automatic quality switching
- Error recovery mechanisms
- Low latency mode support
- Worker-based processing

#### Responsive Design
- Mobile-first approach
- Flexible layout system
- Touch-friendly controls
- Optimized for various screen sizes

#### Error Handling
- Network error detection and recovery
- Media format validation
- User-friendly error messages
- Automatic retry mechanisms

## Development

### Available Scripts

- `npm start`: Run development server
- `npm build`: Build for production
- `npm test`: Run test suite
- `npm eject`: Eject from Create React App (not recommended)

### Project Structure

```
src/
├── components/
│   ├── HLSPlayer.js      # Main HLS player component
│   └── HLSPlayer.css     # Player styles
├── App.js                # Main app component
├── App.css              # App styles
├── index.js             # React entry point
└── index.css            # Global styles
```

## Integration with HLS Server

This React player is designed to work with the FastAPI HLS server. To use both together:

1. Start the HLS server (Docker or local)
2. Start the React player: `npm start`
3. Upload a video to the HLS server via `/upload`
4. Copy the returned HLS URL to the React player
5. Enjoy seamless video streaming!

## Customization

The player can be easily customized:

- **Styling**: Modify CSS files for custom themes
- **Features**: Add new controls or functionality in the component
- **HLS Settings**: Adjust hls.js configuration in the component

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure your HLS server allows cross-origin requests
2. **Video Won't Play**: Check that the HLS URL is accessible and valid
3. **Mobile Playback**: Some mobile browsers require user interaction before playing

### Debug Mode

Open browser developer tools to see console logs for detailed error information and HLS events.

## License

This project is open source and available under the MIT License. 