import React, { useState, useEffect, useCallback } from 'react';

function App() {
  const [historyData, setHistoryData] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // CV Analyzer states
  const [analyzing, setByanalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [targetPath, setTargetPath] = useState('C:/Users/DELL1/astrophysics-project/datasets/sky_images/sky.jpg');

  // Multi-Satellite Tracking States
  const [selectedSatellite, setSelectedSatellite] = useState('ISS (ZARYA)');
  const [orbitalData, setOrbitalData] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [isSyncingCoords, setIsSyncingCoords] = useState(false);

  // 3D Ground Station Coordinate Slots & Pass States
  const [obsLat, setObsLat] = useState(17.4124);
  const [obsLon, setObsLon] = useState(78.4350);
  const [obsAlt, setObsAlt] = useState(545);
  const [predictions, setPredictions] = useState([]);

  // The 10 Major Satellite Constellations Matrix Catalog
  const satelliteCatalog = [
    { id: 'ISS', name: 'ISS (ZARYA)', type: 'Space Station (LEO)' },
    { id: 'TIANHE', name: 'TIANHE', type: 'Chinese Station (LEO)' },
    { id: 'HUBBLE', name: 'HST', type: 'Hubble Space Telescope (LEO)' },
    { id: 'STARLINK', name: 'STARLINK-30431', type: 'Broadband Mesh (LEO)' },
    { id: 'GPS', name: 'GPS BIIR-2  (PRN 02)', type: 'Navigation Fleet (MEO)' },
    { id: 'GLONASS', name: 'COSMOS 2559 (GLONASS)', type: 'Navigation Fleet (MEO)' },
    { id: 'GALILEO', name: 'GSAT0223 (GALILEO)', type: 'Navigation Fleet (MEO)' },
    { id: 'METEOSAT', name: 'METEOSAT-11 (MSG-4)', type: 'Weather Station (GEO)' },
    { id: 'INTELSAT', name: 'INTELSAT 39', type: 'Telecom Backbone (GEO)' },
    { id: 'NOAA', name: 'NOAA 19', type: 'Climate Monitoring (LEO)' }
  ];

  const fetchTelemetryHistory = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/history');
      if (!response.ok) throw new Error(`Status ${response.status}`);
      const json = await response.json();
      if (json.status === "success") {
        setHistoryData(json.events || []);
        setTotalRecords(json.total_records || 0);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Dynamic Target Fetch Routine passing 3D slots to Backend
  const fetchLiveOrbitalTracking = useCallback(async (targetName) => {
    setTrackingLoading(true);
    try {
      const activeTarget = targetName || selectedSatellite;
      
      // Fetch Live Telemetry using dynamic ground coordinates
      const response = await fetch(
        `http://localhost:8000/api/v1/tracking/live?target=${encodeURIComponent(activeTarget)}&obs_lat=${obsLat}&obs_lon=${obsLon}&obs_alt=${obsAlt}`
      );
      if (!response.ok) throw new Error("Hardware stream tracking timeout.");
      const data = await response.json();
      setOrbitalData(data);

      // Fetch Pass Predictions using dynamic ground coordinates
      const predictRes = await fetch(
        `http://localhost:8000/api/v1/tracking/predictions?target=${encodeURIComponent(activeTarget)}&obs_lat=${obsLat}&obs_lon=${obsLon}&obs_alt=${obsAlt}`
      );
      if (predictRes.ok) {
        const predictData = await predictRes.json();
        setPredictions(predictData.passes || []);
      }
    } catch (err) {
      console.error("Orbital tracking/prediction array fetch error:", err);
    } finally {
      setTrackingLoading(false);
    }
  }, [selectedSatellite, obsLat, obsLon, obsAlt]);

  // Handle dropdown switch
  const handleSatelliteChange = (e) => {
    const target = e.target.value;
    setSelectedSatellite(target);
    fetchLiveOrbitalTracking(target);
  };

  // Run database and initial track on mount
  useEffect(() => {
    fetchTelemetryHistory();
    fetchLiveOrbitalTracking('ISS (ZARYA)');
  }, []); 

  // AUTOMATIC COORD WATCHER (Debounced at 1 second to prevent spamming your API as you type)
  useEffect(() => {
    const handler = setTimeout(() => {
      setIsSyncingCoords(true);
      fetchLiveOrbitalTracking().finally(() => setIsSyncingCoords(false));
    }, 1000);
    return () => clearTimeout(handler);
  }, [obsLat, obsLon, obsAlt, fetchLiveOrbitalTracking]);

  // Regular 4-second update interval loop
  useEffect(() => {
    const interval = setInterval(() => {
      fetchLiveOrbitalTracking();
    }, 4000);
    
    return () => clearInterval(interval);
  }, [fetchLiveOrbitalTracking]);

  // CV Pipeline trigger routine
  const handleTriggerAnalysis = async () => {
    setByanalyzing(true);
    setAnalysisResult(null);
    try {
      const response = await fetch(`http://localhost:8000/api/analyze?image_path=${encodeURIComponent(targetPath)}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error(`Status ${response.status}`);
      const json = await response.json();
      if (json.status === "success") {
        setAnalysisResult(json.data);
        await fetchTelemetryHistory(); // Update database summary table dynamically
      }
    } catch (err) {
      alert(`Simulation Error: ${err.message}`);
    } finally {
      setByanalyzing(false);
    }
  };

  // Helper for automated native timezone localized translations
  const formatLocalTime = (isoString) => {
    if (!isoString) return "N/A";
    const dateObj = new Date(isoString);
    return dateObj.toLocaleTimeString(undefined, {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  };

  // Compute SVG Graph coordinates
  const generateGraphPaths = () => {
    if (historyData.length < 2) return { linePath: "", points: [] };
    const historicalOrder = [...historyData].reverse();
    const paddingX = 40; const paddingY = 30; const width = 1000; const height = 160;
    const maxVal = Math.max(...historicalOrder.map(e => e.line_segments || 1), 10);
    const valRange = maxVal;

    const points = historicalOrder.map((event, index) => {
      const x = paddingX + (index * (width - paddingX * 2)) / (historicalOrder.length - 1);
      const y = height - paddingY - (((event.line_segments || 0)) * (height - paddingY * 2)) / valRange;
      const timePart = event.timestamp.includes(" ") ? event.timestamp.split(" ")[1] : event.timestamp;
      return { x, y, segments: event.line_segments, time: timePart };
    });
    const linePath = points.reduce((acc, p, i) => i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`, "");
    return { linePath, points };
  };

  const { linePath, points } = generateGraphPaths();

  return (
    <div style={{ backgroundColor: '#0B0F19', minHeight: '100vh', color: '#f8fafc', padding: '24px', fontFamily: 'system-ui, sans-serif' }}>
      
      {/* Header Panel */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '16px', marginBottom: '24px' }}>
        <div style={{ textAlign: 'left' }}>
          <h1 style={{ fontSize: '28px', color: '#00F0FF', margin: 0, fontWeight: 'bold' }}>Project AstroEdge</h1>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: '4px 0 0 0' }}>AI Observatory Core Control Panel • v1.3.0</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => fetchLiveOrbitalTracking()} style={{ padding: '8px 16px', backgroundColor: '#0f172a', color: '#fbbf24', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '4px', cursor: 'pointer', fontWeight: '500' }}>
            {trackingLoading ? 'Propagating SGP4...' : '🛰️ Force Sync Array'}
          </button>
          <button onClick={fetchTelemetryHistory} style={{ padding: '8px 16px', backgroundColor: '#1e293b', color: '#00F0FF', border: '1px solid rgba(0,240,255,0.3)', borderRadius: '4px', cursor: 'pointer', fontWeight: '500' }}>
            {loading ? 'Refreshing...' : 'Refresh Metrics'}
          </button>
        </div>
      </header>

      {/* Interactive 3D Ground Station Configuration Slots Panel */}
      <section style={{ border: '1px solid #1e293b', padding: '16px', borderRadius: '8px', marginBottom: '24px', backgroundColor: '#0f172a', textAlign: 'left' }}>
        <h3 style={{ color: '#a855f7', marginTop: 0, marginBottom: '14px', fontSize: '16px', fontWeight: 'bold' }}>
          📡 Ground Station Coordinate Slots (3D Spatial Configuration) 
          {isSyncingCoords && <span style={{ fontSize: '12px', color: '#fbbf24', marginLeft: '12px', fontWeight: 'normal' }}>⚡ Auto-Syncing Vectors...</span>}
        </h3>
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>OBSERVER LATITUDE (°N)</label>
            <input 
              type="number" step="0.0001" value={obsLat} 
              onChange={(e) => setObsLat(parseFloat(e.target.value) || 0)}
              style={{ backgroundColor: '#0B0F19', color: '#fff', border: '1px solid #1e293b', padding: '8px', borderRadius: '4px', width: '130px', outline: 'none' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>OBSERVER LONGITUDE (°E)</label>
            <input 
              type="number" step="0.0001" value={obsLon} 
              onChange={(e) => setObsLon(parseFloat(e.target.value) || 0)}
              style={{ backgroundColor: '#0B0F19', color: '#fff', border: '1px solid #1e293b', padding: '8px', borderRadius: '4px', width: '130px', outline: 'none' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>STATION ELEVATION (Meters)</label>
            <input 
              type="number" step="1" value={obsAlt} 
              onChange={(e) => setObsAlt(parseFloat(e.target.value) || 0)}
              style={{ backgroundColor: '#0B0F19', color: '#fff', border: '1px solid #1e293b', padding: '8px', borderRadius: '4px', width: '150px', outline: 'none' }}
            />
          </div>
        </div>
      </section>

      {/* Grid Stats Row */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '24px', textAlign: 'left' }}>
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
          <div style={{ fontSize: '14px', color: '#94a3b8' }}>Tracking Target Engine</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#00F0FF' }}>{selectedSatellite}</div>
        </div>
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
          <div style={{ fontSize: '14px', color: '#94a3b8' }}>Database Logs</div>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f8fafc' }}>{totalRecords} Events Rows</div>
        </div>
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
          <div style={{ fontSize: '14px', color: '#94a3b8' }}>Horizon Visibility Status</div>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: orbitalData?.look_angles?.horizon_status?.includes("ABOVE") ? '#34d399' : '#ef4444' }}>
            {orbitalData?.look_angles?.horizon_status || "FETCHING..."}
          </div>
        </div>
      </section>

      {/* Split Window Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        
        {/* Left Card: Trend Array Graph */}
        <section style={{ borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '20px', textAlign: 'left' }}>
          <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '12px', color: '#f1f5f9' }}>
            Transient Tracking Trend Analyzer (Segments Vector Matrix)
          </div>
          {historyData.length < 2 ? (
            <div style={{ height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>Insufficient log metrics.</div>
          ) : (
            <div style={{ width: '100%', overflowX: 'auto' }}>
              <svg viewBox="0 0 1000 180" style={{ width: '100%', height: 'auto', display: 'block' }}>
                <path d={linePath} fill="none" stroke="#aa3bff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                {points.map((pt, idx) => (
                  <g key={idx}>
                    <circle cx={pt.x} cy={pt.y} r="5" fill="#00F0FF" stroke="#0B0F19" strokeWidth="1.5" />
                    <text x={pt.x} y="165" fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="monospace">{pt.time}</text>
                  </g>
                ))}
              </svg>
            </div>
          )}
        </section>

        {/* Right Card: Dynamic Interactive Tracker Console */}
        <section style={{ borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '18px', textAlign: 'left' }}>
          <div style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '12px', color: '#fbbf24' }}>
            📡 Topocentric Array Target Core
          </div>
          
          {/* Target Asset Dropdown Selector */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>SELECT CELESTIAL ASSET:</label>
            <select 
              value={selectedSatellite} 
              onChange={handleSatelliteChange}
              style={{ width: '100%', padding: '8px', backgroundColor: '#0B0F19', border: '1px solid #1e293b', borderRadius: '4px', color: '#fff', fontWeight: 'bold', cursor: 'pointer' }}
            >
              {satelliteCatalog.map((sat) => (
                <option key={sat.id} value={sat.name}>{sat.name} ({sat.type})</option>
              ))}
            </select>
          </div>

          {/* Comprehensive Ground Station Physics Breakdown */}
          {orbitalData ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'monospace', fontSize: '13px', backgroundColor: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.03)' }}>
              <div>🛰️ <span style={{ color: '#94a3b8' }}>ID/Name:</span> <span style={{ color: '#00F0FF', fontWeight: 'bold' }}>{orbitalData.name}</span></div>
              <hr style={{ border: 'none', borderTop: '1px solid #1e293b', margin: '4px 0' }} />
              <div>🌐 <span style={{ color: '#94a3b8' }}>Sub-Satellite Lat:</span> {Number(orbitalData.lat).toFixed(4)}°</div>
              <div>🌐 <span style={{ color: '#94a3b8' }}>Sub-Satellite Lon:</span> {Number(orbitalData.lon).toFixed(4)}°</div>
              <div>🚀 <span style={{ color: '#94a3b8' }}>Orbital Altitude:</span> {Number(orbitalData.alt_km).toFixed(1)} km</div>
              <hr style={{ border: 'none', borderTop: '1px solid #1e293b', margin: '4px 0' }} />
              <div>🧭 <span style={{ color: '#94a3b8' }}>Azimuth Look:</span> <span style={{ color: '#fbbf24' }}>{orbitalData.look_angles?.azimuth_deg}°</span></div>
              <div>📈 <span style={{ color: '#94a3b8' }}>Elevation Angle:</span> <span style={{ color: '#fbbf24' }}>{orbitalData.look_angles?.elevation_deg}°</span></div>
              <div>📏 <span style={{ color: '#94a3b8' }}>Slant Range:</span> {orbitalData.look_angles?.range_km} km</div>
            </div>
          ) : (
            <div style={{ color: '#64748b', fontSize: '12px' }}>Locking onto target telemetry matrices...</div>
          )}
        </section>

      </div>

      {/* Pass Predictions Forecasting Section */}
      <section style={{ borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '20px', marginBottom: '24px', textAlign: 'left' }}>
        <div style={{ fontWeight: 'bold', fontSize: '17px', marginBottom: '14px', color: '#06b6d4' }}>
          📅 Upcoming Local Horizon Pass Track Forecasting (Dynamic UTC-to-Local conversion)
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', fontFamily: 'monospace' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #1e293b', backgroundColor: 'rgba(0,0,0,0.2)', color: '#cbd5e1' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>AOS (Acquisition Rise)</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>TCA (Max Zenith Peak)</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>LOS (Loss Horizon Set)</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Max Elevation</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Duration Window</th>
              </tr>
            </thead>
            <tbody>
              {predictions.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ padding: '15px', color: '#64748b', textAlign: 'center' }}>
                    No tracking prediction tracks found for coordinates slot.
                  </td>
                </tr>
              ) : (
                predictions.map((pass, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid rgba(30,41,59,0.3)', backgroundColor: index % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent' }}>
                    <td style={{ padding: '12px', color: '#f8fafc' }}>{formatLocalTime(pass.aos)}</td>
                    <td style={{ padding: '12px', color: '#cbd5e1' }}>{formatLocalTime(pass.tca)}</td>
                    <td style={{ padding: '12px', color: '#cbd5e1' }}>{formatLocalTime(pass.los)}</td>
                    <td style={{ padding: '12px', textAlign: 'center', color: '#a855f7', fontWeight: 'bold' }}>{pass.max_elevation_deg}°</td>
                    <td style={{ padding: '12px', textAlign: 'center', color: '#94a3b8' }}>
                      {Math.floor(pass.duration_seconds / 60)}m {pass.duration_seconds % 60}s
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Optical Sensor Execution Console */}
      <section style={{ borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '20px', marginBottom: '24px', textAlign: 'left' }}>
        <div style={{ fontWeight: 'bold', fontSize: '17px', marginBottom: '14px', color: '#f1f5f9' }}>
          📷 Optical Sensor Capture Frame Analyzer Execution Console
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px' }}>
          <input type="text" value={targetPath} onChange={(e) => setTargetPath(e.target.value)} style={{ flex: 1, padding: '10px', backgroundColor: '#0B0F19', border: '1px solid #1e293b', borderRadius: '4px', color: '#cbd5e1', fontFamily: 'monospace' }} />
          <button onClick={handleTriggerAnalysis} disabled={analyzing} style={{ padding: '10px 20px', backgroundColor: '#aa3bff', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
            {analyzing ? 'Executing OpenCV...' : 'Run CV Pipeline Engine'}
          </button>
        </div>
        {analysisResult && (
          <div style={{ padding: '14px', backgroundColor: 'rgba(0,240,255,0.05)', border: '1px solid rgba(0,240,255,0.2)', borderRadius: '6px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '14px', fontFamily: 'monospace' }}>
            <div>⏱️ <span style={{ color: '#94a3b8' }}>Processed At:</span> {analysisResult.timestamp}</div>
            <div>📂 <span style={{ color: '#94a3b8' }}>Target File:</span> {analysisResult.filename}</div>
            <div>💡 <span style={{ color: '#94a3b8' }}>Mean Luminance:</span> {analysisResult.mean_brightness}</div>
            <div>📊 <span style={{ color: '#94a3b8' }}>Standard Deviation:</span> {analysisResult.std_dev}</div>
            <div>✨ <span style={{ color: '#94a3b8' }}>Sky Quality Factor:</span> {analysisResult.sky_quality}</div>
            <div>⭐ <span style={{ color: '#94a3b8' }}>Isolated Star Fields:</span> <span style={{ color: '#fbbf24', fontWeight: 'bold' }}>{analysisResult.stars_detected} objects</span></div>
          </div>
        )}
      </section>

      {/* Historical Data Logs Table */}
      <section style={{ borderRadius: '8px', border: '1px solid #1e293b', backgroundColor: '#0f172a', overflow: 'hidden', textAlign: 'left' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #1e293b', fontWeight: 'bold', fontSize: '18px' }}>
          Database Telemetry Log Records Matrix
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', backgroundColor: 'rgba(0,0,0,0.2)', color: '#cbd5e1' }}>
                <th style={{ padding: '12px', textAlign: 'center' }}>ID</th>
                <th style={{ padding: '12px' }}>Timestamp</th>
                <th style={{ padding: '12px' }}>Classification</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Confidence</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Line Segments</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Aspect Ratio</th>
              </tr>
            </thead>
            <tbody>
              {historyData.map((event) => (
                <tr key={event.id} style={{ borderBottom: '1px solid rgba(30,41,59,0.5)' }}>
                  <td style={{ padding: '12px', textAlign: 'center', fontFamily: 'monospace', color: '#94a3b8' }}>{event.id}</td>
                  <td style={{ padding: '12px', fontFamily: 'monospace' }}>{event.timestamp}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', backgroundColor: '#1e293b', color: '#a78bfa' }}>
                      {event.classification}
                    </span>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', color: '#34d399', fontFamily: 'monospace' }}>{event.confidence_score}</td>
                  <td style={{ padding: '12px', textAlign: 'center', fontFamily: 'monospace' }}>{event.line_segments}</td>
                  <td style={{ padding: '12px', textAlign: 'center', color: '#c084fc', fontFamily: 'monospace' }}>{event.aspect_ratio}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default App;