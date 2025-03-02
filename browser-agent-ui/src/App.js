import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Container, Form, Button, Card, Spinner, Alert, Tabs, Tab, Accordion } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  const [command, setCommand] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [screenshotUrl, setScreenshotUrl] = useState('');
  const [history, setHistory] = useState([]);
  const [debugUrl, setDebugUrl] = useState('');
  const [viewMode, setViewMode] = useState('screenshot'); // 'screenshot' o 'live'
  const [wsConnected, setWsConnected] = useState(false);
  const [liveImage, setLiveImage] = useState('');
  const [isLiveMode, setIsLiveMode] = useState(false);
  const liveInterval = useRef(null);
  const ws = useRef(null);

  // Obtener la URL de depuración al cargar la página
  useEffect(() => {
    const fetchDebugUrl = async () => {
      try {
        const res = await axios.get('http://localhost:8000/debug-url/');
        setDebugUrl(res.data.debug_url);
      } catch (err) {
        console.error("Error obteniendo la URL de depuración:", err);
      }
    };
    
    fetchDebugUrl();
  }, []);

  useEffect(() => {
    // Conectar WebSocket
    const connectWebSocket = () => {
      ws.current = new WebSocket('ws://localhost:8000/ws/browser');
      
      ws.current.onopen = () => {
        setWsConnected(true);
        console.log('WebSocket conectado');
      };
      
      ws.current.onmessage = (event) => {
        // Actualizar imagen en vivo con los datos recibidos
        setLiveImage(`data:image/jpeg;base64,${event.data}`);
      };
      
      ws.current.onclose = () => {
        setWsConnected(false);
        console.log('WebSocket desconectado');
        
        // Intentar reconectar después de un tiempo
        setTimeout(connectWebSocket, 2000);
      };
      
      ws.current.onerror = (error) => {
        console.error('Error de WebSocket:', error);
        ws.current.close();
      };
    };
    
    connectWebSocket();
    
    // Limpiar WebSocket al desmontar
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (isLiveMode) {
      // Iniciar intervalo de actualización
      liveInterval.current = setInterval(() => {
        const timestamp = new Date().getTime();
        setScreenshotUrl(`http://localhost:8000/screenshots/browser_screenshot_latest.png?t=${timestamp}`);
      }, 1000); // Actualizar cada segundo
    } else {
      // Limpiar intervalo si existe
      if (liveInterval.current) {
        clearInterval(liveInterval.current);
        liveInterval.current = null;
      }
    }
    
    // Limpiar al desmontar
    return () => {
      if (liveInterval.current) {
        clearInterval(liveInterval.current);
      }
    };
  }, [isLiveMode]);

  const executeCommand = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:8000/execute/', { command });
      setResponse(res.data);
      
      // Get the latest screenshot with timestamp to prevent caching
      const timestamp = new Date().getTime();
      const screenshotUrl = `http://localhost:8000/screenshots/browser_screenshot_latest.png?t=${timestamp}`;
      
      // Add to history with screenshot URL
      setHistory(prev => [...prev, { 
        command, 
        response: res.data.response,
        timestamp: new Date().toLocaleTimeString(),
        screenshotUrl: screenshotUrl
      }]);
      
      setCommand('');
    } catch (err) {
      setError('Error executing command: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (command.trim()) {
      executeCommand();
    }
  };

  const handleTabChange = (key) => {
    setViewMode(key);
    setIsLiveMode(key === 'live');
  };

  return (
    <Container fluid className="py-4">
      <h1 className="mb-4 text-center">Browser Automation Agent</h1>
      
      <div className="row mb-4">
        <div className="col-md-8">
          <Card>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Enter your command:</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    placeholder="e.g. 'Open Google and search for React tutorials'"
                    disabled={loading}
                  />
                </Form.Group>
                <Button 
                  variant="primary" 
                  type="submit" 
                  disabled={loading || !command.trim()}
                >
                  {loading ? (
                    <>
                      <Spinner
                        as="span"
                        animation="border"
                        size="sm"
                        role="status"
                        aria-hidden="true"
                      />
                      <span className="ms-2">Executing...</span>
                    </>
                  ) : 'Execute Command'}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </div>

        <div className="col-md-4">
          <Card>
            <Card.Header>Command History</Card.Header>
            <Card.Body>
              <Accordion className="command-history">
                {history.length === 0 ? (
                  <p className="text-muted">No commands yet</p>
                ) : (
                  history.map((item, index) => (
                    <Accordion.Item key={index} eventKey={index.toString()}>
                      <Accordion.Header>
                        <div className="d-flex justify-content-between w-100 me-3">
                          <span>{item.command}</span>
                          <small className="text-muted">{item.timestamp}</small>
                        </div>
                      </Accordion.Header>
                      <Accordion.Body>
                        <div className="response-text">{item.response}</div>
                        {item.screenshotUrl && (
                          <div className="mt-2">
                            <a 
                              href={item.screenshotUrl} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="btn btn-sm btn-outline-secondary"
                            >
                              View Screenshot
                            </a>
                          </div>
                        )}
                      </Accordion.Body>
                    </Accordion.Item>
                  ))
                )}
              </Accordion>
            </Card.Body>
          </Card>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <div className="row">
        <div className="col-12">
          <Card>
            <Card.Header>Live View</Card.Header>
            <Card.Body className="p-0">
              {liveImage ? (
                <div className="live-browser-container">
                  <img 
                    src={liveImage} 
                    alt="Live Browser View" 
                    className="img-fluid browser-screenshot" 
                  />
                </div>
              ) : (
                <p className="text-muted p-3">Live view connecting...</p>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    </Container>
  );
}

export default App;
