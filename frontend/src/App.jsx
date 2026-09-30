import { useEffect, useRef, useState } from 'react';
import { getValidActivity, SPORT_ACTIVITIES } from './constants/sportActivities';
import { SPORT_ROLES, SUPPORTED_SPORTS } from './constants/sportRoles';

const API_BASE = 'https://ai-sportsvision-backend-2026.onrender.com/api';
const defaultPlayer = {
  name: 'Aarav Singh',
  age: 21,
  gender: 'Male',
  sport: 'Cricket',
  role: 'Batter',
  experience_level: 'Intermediate',
  preferred_activity: 'Batting',
  training_goals: 'Improve head stability and balance during the swing phase.',
  previous_performance: 74,
};

function App() {
  const [player, setPlayer] = useState(defaultPlayer);
  const [sport, setSport] = useState('Cricket');
  const [activity, setActivity] = useState('Batting');
  const [selectedPlayerId, setSelectedPlayerId] = useState('');
  const [file, setFile] = useState(null);
  const [players, setPlayers] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [status, setStatus] = useState('Ready for video upload');
  const [analysisMode, setAnalysisMode] = useState('upload');
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraStatus, setCameraStatus] = useState('Camera idle');
  const [cameraError, setCameraError] = useState('');
  const [liveMetrics, setLiveMetrics] = useState({ technique: 0, balance: 0, movement: 0, consistency: 0, stability: 0, overall: 0 });
  const [liveInsight, setLiveInsight] = useState('Waiting for live pose detection.');
  const [liveWeaknesses, setLiveWeaknesses] = useState([]);
  const [sessionSeconds, setSessionSeconds] = useState(0);
  const [cameraReady, setCameraReady] = useState(false);
  const [isSessionRunning, setIsSessionRunning] = useState(false);
  const [cameraFacing, setCameraFacing] = useState('user');
  const [isSwitchingCamera, setIsSwitchingCamera] = useState(false);

  const activeSport = player.sport || sport;
  const activeActivity = getValidActivity(activeSport, player.preferred_activity)
    || getValidActivity(activeSport, activity);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const landmarkerRef = useRef(null);
  const animationRef = useRef(null);
  const historyRef = useRef([]);
  const sessionStartRef = useRef(null);

  useEffect(() => {
    loadPlayers();
  }, []);

  useEffect(() => {
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!isSessionRunning) return;
    const interval = setInterval(() => {
      setSessionSeconds(Math.floor((Date.now() - (sessionStartRef.current || Date.now())) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [isSessionRunning]);

  const clamp = (value, min = 0, max = 100) => Math.min(Math.max(value, min), max);

  const updateLiveFromPose = (landmarks) => {
    if (!landmarks || !landmarks.length) {
      setLiveInsight('No reliable pose detected. Improve lighting and keep the athlete fully in frame.');
      setLiveMetrics((prev) => ({ ...prev, technique: 0, balance: 0, movement: 0, consistency: 0, stability: 0, overall: 0 }));
      setLiveWeaknesses([]);
      return;
    }

    const pose = landmarks[0];
    const getPoint = (index) => pose[index] || null;
    const nose = getPoint(0);
    const leftShoulder = getPoint(11);
    const rightShoulder = getPoint(12);
    const leftHip = getPoint(23);
    const rightHip = getPoint(24);
    const leftAnkle = getPoint(27);
    const rightAnkle = getPoint(28);

    let shoulderAlignment = 100;
    let hipAlignment = 100;
    let headStability = 100;

    if (leftShoulder && rightShoulder) {
      shoulderAlignment = clamp(100 - Math.abs(leftShoulder.x - rightShoulder.x) * 220);
    }
    if (leftHip && rightHip) {
      hipAlignment = clamp(100 - Math.abs(leftHip.x - rightHip.x) * 220);
    }
    if (nose) {
      historyRef.current.push({ x: nose.x, y: nose.y });
      if (historyRef.current.length > 18) historyRef.current.shift();
      const recent = historyRef.current;
      const avgX = recent.reduce((sum, item) => sum + item.x, 0) / recent.length;
      const avgY = recent.reduce((sum, item) => sum + item.y, 0) / recent.length;
      const varianceX = recent.reduce((sum, item) => sum + Math.abs(item.x - avgX), 0) / recent.length;
      const varianceY = recent.reduce((sum, item) => sum + Math.abs(item.y - avgY), 0) / recent.length;
      headStability = clamp(100 - (varianceX * 180 + varianceY * 120));
    }

    const balanceScore = clamp((shoulderAlignment + hipAlignment + (leftAnkle && rightAnkle ? clamp(100 - Math.abs(leftAnkle.x - rightAnkle.x) * 200) : 100)) / 3);
    const movementScore = clamp(60 + (Math.abs((leftShoulder?.x ?? 0) - (rightShoulder?.x ?? 0)) * 60) + (leftAnkle && rightAnkle ? clamp(100 - Math.abs(leftAnkle.x - rightAnkle.x) * 120) : 50));
    const consistencyScore = clamp(50 + (100 - Math.abs(shoulderAlignment - hipAlignment)) / 2);
    const stabilityScore = clamp((headStability + balanceScore + consistencyScore) / 3);
    const techniqueScore = clamp((shoulderAlignment * 0.45) + (headStability * 0.3) + (hipAlignment * 0.25));
    const overall = clamp((techniqueScore * 0.3) + (balanceScore * 0.25) + (movementScore * 0.2) + (consistencyScore * 0.15) + (stabilityScore * 0.1));

    const nextMetrics = {
      technique: Number(techniqueScore.toFixed(1)),
      balance: Number(balanceScore.toFixed(1)),
      movement: Number(movementScore.toFixed(1)),
      consistency: Number(consistencyScore.toFixed(1)),
      stability: Number(stabilityScore.toFixed(1)),
      overall: Number(overall.toFixed(1)),
    };

    const weaknessList = [];
    if (headStability < 72) {
      weaknessList.push({ feature: 'Head stability', severity: 'Medium', evidence: 'Head position varies noticeably through the motion cycle.', suggested_improvement: 'Keep the head still and eyes level during the swing setup.' });
    }
    if (shoulderAlignment < 78) {
      weaknessList.push({ feature: 'Shoulder alignment', severity: 'Medium', evidence: 'Shoulder positions are uneven during movement.', suggested_improvement: 'Keep shoulders level and aligned during the stance and preparation phase.' });
    }
    if (balanceScore < 74) {
      weaknessList.push({ feature: 'Balance instability', severity: 'High', evidence: 'Body alignment shifts while the athlete is in motion.', suggested_improvement: 'Focus on stable lower-body posture and controlled foot placement.' });
    }

    setLiveMetrics(nextMetrics);
    setLiveWeaknesses(weaknessList);
    setLiveInsight(
      weaknessList.length
        ? `Main focus: ${weaknessList[0].feature}. Maintain a more stable body line during the movement phase.`
        : 'Technique is stable. Continue tracking posture and lower-body alignment.'
    );
  };

  const stopCameraStream = () => {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    setCameraReady(false);
    setCameraStatus('Camera stopped');
    setCameraFacing('user');
    setIsSessionRunning(false);
  };

  const attachVideoStream = async (stream, facingMode) => {
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      videoRef.current.style.transform = facingMode === 'user' ? 'scaleX(-1)' : 'scaleX(1)';
      try {
        await videoRef.current.play();
      } catch (error) {
        console.warn('Video playback could not start immediately:', error);
      }
    }
    setCameraFacing(facingMode);
    setCameraActive(true);
    setCameraReady(true);
    setCameraStatus(facingMode === 'user' ? 'Front Camera' : 'Back Camera');
  };

  const requestCameraStream = async (facingMode) => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError('Camera API is not supported in this browser.');
      return null;
    }

    const constraints = {
      video: {
        facingMode: facingMode === 'user' ? 'user' : { exact: 'environment' },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    };

    try {
      setCameraError('');
      setCameraStatus(facingMode === 'user' ? 'Requesting front camera...' : 'Requesting back camera...');
      return await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      console.error(error);
      const isPermissionDenied = ['NotAllowedError', 'PermissionDeniedError'].includes(error?.name) || /permission|denied/i.test(error?.message || '');
      const isBackCameraUnavailable = ['NotFoundError', 'OverconstrainedError'].includes(error?.name) || /environment|facingMode/i.test(error?.message || '');

      if (isPermissionDenied) {
        setCameraError('Camera permission is required to use Live Camera.');
        setCameraStatus('Camera access failed');
      } else if (facingMode === 'environment' && isBackCameraUnavailable) {
        setCameraError('Back camera is not available on this device.');
        setCameraStatus('Back camera unavailable');
      } else {
        setCameraError('Camera permission is required to use Live Camera.');
        setCameraStatus('Camera access failed');
      }
      return null;
    }
  };

  const startCamera = async () => {
    const stream = await requestCameraStream('user');
    if (!stream) return;

    await attachVideoStream(stream, 'user');

    if (!landmarkerRef.current) {
      const { FilesetResolver, PoseLandmarker } = await import('@mediapipe/tasks-vision');
      const vision = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm');
      landmarkerRef.current = await PoseLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numPoses: 1,
      });
    }

    setCameraStatus('Live pose detection ready');
    const drawLoop = () => {
      if (!videoRef.current) return;
      if (videoRef.current.readyState >= 2 && landmarkerRef.current) {
        const now = performance.now();
        const result = landmarkerRef.current.detectForVideo(videoRef.current, now);
        const canvas = canvasRef.current;
        const ctx = canvas?.getContext('2d');
        if (canvas && ctx) {
          canvas.width = videoRef.current.videoWidth || 640;
          canvas.height = videoRef.current.videoHeight || 480;
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          if (result.landmarks && result.landmarks.length) {
            const pose = result.landmarks[0];
            const connections = [
              [0, 1], [1, 2], [2, 3], [3, 7], [0, 4], [4, 5], [5, 6], [6, 8], [9, 10], [11, 12], [11, 13], [13, 15], [15, 17], [17, 19], [19, 21], [12, 14], [14, 16], [16, 18], [18, 20], [20, 22], [11, 23], [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28], [27, 29], [28, 30], [29, 31], [30, 32], [27, 28]
            ];

            ctx.strokeStyle = '#49d39a';
            ctx.lineWidth = 3;
            connections.forEach(([start, end]) => {
              const startPoint = pose[start];
              const endPoint = pose[end];
              if (startPoint && endPoint) {
                ctx.beginPath();
                ctx.moveTo(startPoint.x * canvas.width, startPoint.y * canvas.height);
                ctx.lineTo(endPoint.x * canvas.width, endPoint.y * canvas.height);
                ctx.stroke();
              }
            });

            ctx.fillStyle = '#6be0ff';
            pose.forEach((point) => {
              if (point && point.visibility > 0.2) {
                ctx.beginPath();
                ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, Math.PI * 2);
                ctx.fill();
              }
            });
          }
        }

        updateLiveFromPose(result.landmarks);
      }
      animationRef.current = requestAnimationFrame(drawLoop);
    };
    animationRef.current = requestAnimationFrame(drawLoop);
  };

  const switchCamera = async () => {
    if (!cameraActive || isSwitchingCamera) return;

    const nextFacing = cameraFacing === 'user' ? 'environment' : 'user';
    setIsSwitchingCamera(true);
    setCameraError('');
    setCameraStatus(nextFacing === 'user' ? 'Switching to Front Camera...' : 'Switching to Back Camera...');

    const oldStream = streamRef.current;
    if (oldStream) {
      oldStream.getTracks().forEach((track) => track.stop());
    }

    const stream = await requestCameraStream(nextFacing);
    if (!stream) {
      setIsSwitchingCamera(false);
      return;
    }

    await attachVideoStream(stream, nextFacing);
    setIsSwitchingCamera(false);
    setCameraStatus(`${nextFacing === 'user' ? 'Front Camera' : 'Back Camera'}`);
  };

  const saveLiveSession = async (payload) => {
    try {
      const response = await fetch(`${API_BASE}/live-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save live session');
      }

      const savedSession = await response.json();
      const historyResponse = await fetch(`${API_BASE}/history/${payload.player_id}`);
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setSessions(historyData);
      }
      return savedSession;
    } catch (error) {
      console.error(error);
      setStatus(error.message || 'Failed to save live session.');
      return null;
    }
  };

  const startLiveSession = async () => {
    const selected = await saveProfile();
    if (!selected) return;
    setIsSessionRunning(true);
    sessionStartRef.current = Date.now() - (sessionSeconds * 1000);
    setCameraStatus(`${cameraFacing === 'user' ? 'Front Camera' : 'Back Camera'} active`);
    setStatus('Live AI analysis in progress.');
  };

  const pauseLiveSession = () => {
    setIsSessionRunning(false);
    setStatus('Live AI analysis paused.');
    setCameraStatus(`${cameraFacing === 'user' ? 'Front Camera' : 'Back Camera'} paused`);
  };

  const endLiveSession = async () => {
    const durationSeconds = Math.max(1, Math.round((Date.now() - (sessionStartRef.current || Date.now())) / 1000));
    const selectedPlayer = players.find((item) => item.id === selectedPlayerId) || (await saveProfile());
    if (!selectedPlayer) return;
    const finalMetrics = {
      ...liveMetrics,
      overall: liveMetrics.overall || 75,
      durationSeconds,
      source: 'LIVE CAMERA',
      id: `live-${Date.now()}`,
    };

    const summary = {
      id: finalMetrics.id,
      date: new Date().toISOString(),
      sport: activeSport,
      activity: activeActivity,
      overall_score: Number(finalMetrics.overall),
      technique_score: Number(finalMetrics.technique),
      balance_score: Number(finalMetrics.balance),
      movement_score: Number(finalMetrics.movement),
      consistency_score: Number(finalMetrics.consistency),
      stability_score: Number(finalMetrics.stability),
      weaknesses: liveWeaknesses,
      recommendations: liveWeaknesses.length ? [{ title: 'Live coaching focus', description: liveInsight, reason: 'Based on live movement metrics and detected instability.' }] : [{ title: 'Technique stable', description: 'Continue the current movement pattern and monitor consistency.', reason: 'No major live weakness detected.' }],
      source: 'LIVE CAMERA',
      duration: durationSeconds,
    };

    const liveSessionPayload = {
      player_id: selectedPlayer.id,
      sport: activeSport,
      activity: activeActivity,
      duration_seconds: durationSeconds,
      overall_score: Number(finalMetrics.overall),
      technique_score: Number(finalMetrics.technique),
      balance_score: Number(finalMetrics.balance),
      movement_score: Number(finalMetrics.movement),
      consistency_score: Number(finalMetrics.consistency),
      stability_score: Number(finalMetrics.stability),
      weaknesses: liveWeaknesses,
      recommendations: summary.recommendations,
      ai_insight: liveInsight,
    };

    setSessions((prev) => [summary, ...prev]);
    setAnalysis({
      session_id: summary.id,
      player: player.name,
      sport: activeSport,
      activity: activeActivity,
      analysis: {
        overall_score: summary.overall_score,
        component_scores: {
          technique: summary.technique_score,
          balance: summary.balance_score,
          movement: summary.movement_score,
          consistency: summary.consistency_score,
          stability: summary.stability_score,
        },
      },
      weaknesses: summary.weaknesses,
      recommendations: summary.recommendations,
      prediction: { current_performance: summary.overall_score, predicted_future_performance: 'More sessions are required for reliable prediction.' },
      repeated_mistakes: liveWeaknesses.length ? [{ feature: liveWeaknesses[0].feature, sessions_affected: 1, trend: 'Detected in current live session' }] : [],
    });

    await saveLiveSession(liveSessionPayload);
    setStatus('Live session saved to performance history.');
    setIsSessionRunning(false);
    stopCameraStream();
  };

  const loadPlayers = async () => {
    try {
      const response = await fetch(`${API_BASE}/players`);
      if (response.ok) {
        const data = await response.json();
        setPlayers(data);
        if (data.length) {
          const activePlayerId = localStorage.getItem('sportsvision.activePlayerId');
          const saved = data.find((item) => item.id === activePlayerId) || data[0];
          const savedRoles = SPORT_ROLES[saved.sport] || [];
          const savedRole = savedRoles.find((role) => role.toLowerCase() === saved.role?.toLowerCase()) || '';
          const savedActivity = getValidActivity(saved.sport, saved.preferred_activity);
          setSelectedPlayerId(saved.id);
          localStorage.setItem('sportsvision.activePlayerId', saved.id);
          setPlayer({ ...defaultPlayer, ...saved, role: savedRole, preferred_activity: savedActivity });
          setSport(saved.sport);
          setActivity(savedActivity);
        } else {
          localStorage.removeItem('sportsvision.activePlayerId');
        }
      }
    } catch (error) {
      console.error(error);
    }
  };

  const validateProfile = () => {
    if (!SPORT_ROLES[player.sport]) {
      setStatus('Please select a sport.');
      return false;
    }
    if (!player.role) {
      setStatus('Please select a role.');
      return false;
    }
    if (!SPORT_ROLES[player.sport].includes(player.role)) {
      setStatus('Please select a valid role for the selected sport.');
      return false;
    }
    if (!getValidActivity(player.sport, player.preferred_activity)) {
      setStatus('Please select a preferred activity for the selected sport.');
      return false;
    }
    return true;
  };

  const saveProfile = async () => {
    if (!validateProfile()) return null;
    setSavingProfile(true);

    const payload = {
      ...player,
      sport: activeSport,
      preferred_activity: activeActivity,
    };

    try {
      const response = await fetch(selectedPlayerId ? `${API_BASE}/players/${selectedPlayerId}` : `${API_BASE}/players`, {
        method: selectedPlayerId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const saved = await response.json();
      if (!response.ok) throw new Error(saved.detail || 'Failed to save profile.');

      setSelectedPlayerId(saved.id);
      localStorage.setItem('sportsvision.activePlayerId', saved.id);
      setPlayers((prev) => selectedPlayerId
        ? prev.map((item) => item.id === saved.id ? saved : item)
        : [...prev, saved]);
      setStatus('Profile saved.');
      return saved;
    } catch (error) {
      setStatus(error.message || 'Failed to save profile.');
      return null;
    } finally {
      setSavingProfile(false);
    }
  };

  const selectProfile = (playerId) => {
    setSelectedPlayerId(playerId);
    if (playerId) localStorage.setItem('sportsvision.activePlayerId', playerId);
    else localStorage.removeItem('sportsvision.activePlayerId');
    const saved = players.find((item) => item.id === playerId);
    if (!saved) {
      setPlayer(defaultPlayer);
      setSport(defaultPlayer.sport);
      setActivity(defaultPlayer.preferred_activity);
      return;
    }

    const savedRoles = SPORT_ROLES[saved.sport] || [];
    const savedRole = savedRoles.find((role) => role.toLowerCase() === saved.role?.toLowerCase()) || '';
    const savedActivity = getValidActivity(saved.sport, saved.preferred_activity);
    setPlayer({ ...defaultPlayer, ...saved, role: savedRole, preferred_activity: savedActivity });
    setSport(saved.sport);
    setActivity(savedActivity);
  };

  const handleUploadAndAnalyze = async () => {
    if (!validateProfile()) return;
    if (!file) {
      setStatus('Please select a valid MP4, MOV, or AVI file.');
      return;
    }

    const selectedPlayer = await saveProfile();
    if (!selectedPlayer) return;

    setLoading(true);
    setStatus('Uploading and validating video...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      const requestSport = selectedPlayer.sport;
      const requestRole = selectedPlayer.role;
      const requestActivity = selectedPlayer.preferred_activity || activeActivity;

      const uploadResponse = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        const error = await uploadResponse.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const uploadData = await uploadResponse.json();
      setStatus('Processing video and extracting pose data...');

      const analyzeResponse = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: selectedPlayer.id,
          sport: requestSport,
          role: requestRole,
          activity: requestActivity,
          video_path: uploadData.path,
        }),
      });

      if (!analyzeResponse.ok) {
        const errorData = await analyzeResponse.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const result = await analyzeResponse.json();
      setAnalysis(result);
      setStatus('Analysis complete with coaching insights generated.');

      const historyResponse = await fetch(`${API_BASE}/history/${selectedPlayer.id}`);
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setSessions(historyData);
      }
    } catch (error) {
      setStatus(error.message || 'AI processing failed.');
    } finally {
      setLoading(false);
    }
  };

  const weaknesses = analysis?.weaknesses || [
    {
      feature: 'Low head stability',
      severity: 'Medium',
      evidence: 'head_stability=0.68',
      suggested_improvement: 'Practice controlled batting drills while maintaining a stable head position.',
    },
  ];
  const recommendations = analysis?.recommendations || [
    {
      title: 'Controlled batting drill',
      description: 'Practice controlled lower-body movement and repeat the stance-to-shot drill.',
      reason: 'Generated from detected setback in movement consistency and balance.',
    },
  ];
  const statusTone = /failed|please select|invalid|unavailable|unable/i.test(status) ? 'is-error' : /saved|complete/i.test(status) ? 'is-success' : '';

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">AI SportsVision</div>
        <div className="header-meta">
          <span className="chip">Player: {player.name}</span>
          <span className="chip">Sport: {activeSport}</span>
          <span className="chip">Session: {analysis?.session_id ? 'Live' : 'Ready'}</span>
        </div>
      </header>

      <main className="page">
        <section className="hero">
          <div className="panel">
            <div className="card-row" style={{ marginBottom: '16px' }}>
              <h2 style={{ margin: 0 }}>Performance overview</h2>
              <span className="badge">{activeSport} · {player.role || 'Role not selected'} · {activeActivity || 'Activity not selected'}</span>
            </div>

            <div className="metric-card overall-score-card">
              <div className="metric-label">Overall score</div>
              <div className="metric-value">{analysis?.analysis?.overall_score ?? 75.4}</div>
            </div>

            <div className={`analysis-status ${statusTone}`} role="status" aria-live="polite">
              <span className="status-marker" aria-hidden="true">●</span>
              <span>{status}</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: loading ? '72%' : analysis ? '100%' : '30%' }} />
            </div>
          </div>

          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Athlete profile</h3>
            <p className="panel-intro">Set the active athlete and choose the focus for this analysis.</p>
            <div className="form-group">
              <label htmlFor="saved-profile">Saved profile</label>
              <select id="saved-profile" value={selectedPlayerId} onChange={(e) => selectProfile(e.target.value)}>
                <option value="">New profile</option>
                {players.map((saved) => <option key={saved.id} value={saved.id}>{saved.name} ({saved.sport})</option>)}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="player-name">Player name</label>
              <input id="player-name" value={player.name} onChange={(e) => setPlayer({ ...player, name: e.target.value })} />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="player-age">Age</label>
                <input id="player-age" type="number" value={player.age} onChange={(e) => setPlayer({ ...player, age: Number(e.target.value) })} />
              </div>
              <div className="form-group">
                <label htmlFor="player-gender">Gender</label>
                <select id="player-gender" value={player.gender} onChange={(e) => setPlayer({ ...player, gender: e.target.value })}>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Prefer not to say</option>
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="player-sport">Sport</label>
                <select id="player-sport" value={activeSport} onChange={(e) => {
                  const nextSport = e.target.value;
                  const nextActivity = getValidActivity(nextSport, player.preferred_activity);
                  setSport(nextSport);
                  setActivity(nextActivity);
                  setPlayer((prev) => ({
                    ...prev,
                    sport: nextSport,
                    role: SPORT_ROLES[nextSport]?.includes(prev.role) ? prev.role : '',
                    preferred_activity: nextActivity,
                  }));
                }}>
                  <option value="">Select Sport</option>
                  {SUPPORTED_SPORTS.map((item) => <option key={item}>{item}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="player-role">Role</label>
                <select id="player-role" value={player.role} onChange={(e) => setPlayer((prev) => ({ ...prev, role: e.target.value }))}>
                  <option value="">Select Role</option>
                  {(SPORT_ROLES[activeSport] || []).map((role) => <option key={role}>{role}</option>)}
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="player-experience">Experience</label>
                <select id="player-experience" value={player.experience_level} onChange={(e) => setPlayer({ ...player, experience_level: e.target.value })}>
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="player-activity">Preferred activity</label>
                <select id="player-activity" value={activeActivity} onChange={(e) => {
                  const nextActivity = e.target.value;
                  setActivity(nextActivity);
                  setPlayer((prev) => ({ ...prev, preferred_activity: nextActivity }));
                }}>
                  <option value="">Select Activity</option>
                  {(SPORT_ACTIVITIES[activeSport] || []).map((item) => <option key={item}>{item}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="training-goals">Training goals</label>
              <textarea id="training-goals" rows="3" value={player.training_goals} onChange={(e) => setPlayer({ ...player, training_goals: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Analysis mode</label>
              <div className="mode-toggle">
                <button
                  type="button"
                  className={analysisMode === 'upload' ? 'mode-btn active' : 'mode-btn'}
                  onClick={() => setAnalysisMode('upload')}
                >
                  Upload Video
                </button>
                <button
                  type="button"
                  className={analysisMode === 'live' ? 'mode-btn active' : 'mode-btn'}
                  onClick={() => setAnalysisMode('live')}
                >
                  Live Camera
                </button>
              </div>
            </div>

            {analysisMode === 'live' ? (
              <div className="live-panel">
                <div className="camera-stage">
                  <video ref={videoRef} className="camera-video" autoPlay muted playsInline />
                  <canvas ref={canvasRef} className="camera-canvas" />
                </div>

                <div className="live-status-block">
                  <span className="badge live-badge">{cameraFacing === 'user' ? 'Front Camera' : 'Back Camera'}</span>
                  <span className="status-subtext">{cameraStatus}</span>
                  <span className="status-subtext">{isSessionRunning ? `Session ${sessionSeconds}s` : cameraReady ? 'Camera ready' : 'Waiting for camera activation'}</span>
                </div>

                <div className="live-metrics">
                  <div className="metric-chip"><span>Overall</span><strong>{liveMetrics.overall || 0}</strong></div>
                  <div className="metric-chip"><span>Technique</span><strong>{liveMetrics.technique || 0}</strong></div>
                  <div className="metric-chip"><span>Balance</span><strong>{liveMetrics.balance || 0}</strong></div>
                </div>

                {cameraError && <div className="live-error">{cameraError}</div>}
                <div className="card-row camera-actions">
                  <button
                    className="btn primary"
                    onClick={cameraActive ? startLiveSession : startCamera}
                    disabled={loading}
                  >
                    {cameraActive ? 'Start' : 'Start'}
                  </button>
                  <button className="btn secondary" onClick={pauseLiveSession} disabled={!cameraActive || !isSessionRunning}>
                    Pause
                  </button>
                  <button className="btn secondary" onClick={isSessionRunning ? endLiveSession : stopCameraStream}>
                    {isSessionRunning ? 'Stop' : 'Stop'}
                  </button>
                  <button className="btn switch-btn" onClick={switchCamera} disabled={!cameraActive || isSwitchingCamera}>
                    {isSwitchingCamera && <span className="loading-spinner" aria-hidden="true" />}
                    {isSwitchingCamera ? 'Switching Camera...' : '🔄 Switch Camera'}
                  </button>
                </div>

                <div className="live-insight">{liveInsight}</div>
                {liveWeaknesses.length > 0 && (
                  <div className="live-list">
                    {liveWeaknesses.map((item, idx) => (
                      <div className="list-item" key={`${item.feature}-${idx}`}>
                        <div style={{ fontWeight: 700 }}>{item.feature}</div>
                        <div className="detail-copy" style={{ marginTop: '4px' }}>{item.suggested_improvement}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label htmlFor="video-upload">Video upload</label>
                  <input id="video-upload" type="file" accept=".mp4,.mov,.avi,.webm" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                  <span className="field-help">MP4, MOV, AVI, and WebM files are supported.</span>
                </div>
                <div className="card-row action-row">
                  <button className="btn primary" onClick={handleUploadAndAnalyze} disabled={loading}>
                    {loading && <span className="loading-spinner" aria-hidden="true" />}
                    {loading ? 'Analyzing...' : 'Start AI analysis'}
                  </button>
                  <button className="btn secondary" onClick={saveProfile} aria-busy={savingProfile}>
                    {savingProfile && <span className="loading-spinner" aria-hidden="true" />}
                    Save profile
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        <section className="grid-2">
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Weakness analysis</h3>
            <div className="list">
              {weaknesses.map((weakness, index) => (
                <div className="list-item" key={`${weakness.feature}-${index}`}>
                  <div className={`severity ${weakness.severity?.toLowerCase() || 'medium'}`}>{weakness.severity || 'Medium'}</div>
                  <div style={{ fontWeight: 700, marginBottom: '6px' }}>{weakness.feature}</div>
                  <div className="detail-copy" style={{ marginBottom: '6px' }}>{weakness.issue}</div>
                  <div className="muted-copy" style={{ fontSize: '0.8rem' }}>{weakness.evidence}</div>
                  <div className="detail-copy" style={{ marginTop: '8px' }}>{weakness.suggested_improvement}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3 style={{ marginTop: 0 }}>AI coaching</h3>
            <div className="list">
              {recommendations.map((item, index) => (
                <div className="list-item" key={`${item.title}-${index}`}>
                  <div style={{ fontWeight: 700, marginBottom: '6px' }}>{item.title}</div>
                  <div className="detail-copy" style={{ marginBottom: '6px' }}>{item.description}</div>
                  <div className="muted-copy" style={{ fontSize: '0.8rem' }}>{item.reason}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid-2">
          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Repeated mistakes</h3>
            <div className="list">
              {(analysis?.repeated_mistakes || [{ feature: 'Head stability', sessions_affected: 4, trend: 'Repeated pattern detected' }]).map((mistake, idx) => (
                <div className="list-item" key={`${mistake.feature}-${idx}`}>
                  <div style={{ fontWeight: 700 }}>{mistake.feature}</div>
                  <div className="detail-copy" style={{ marginTop: '6px' }}>Affected sessions: {mistake.sessions_affected || 4}</div>
                  <div className="muted-copy" style={{ marginTop: '6px' }}>{mistake.trend}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3 style={{ marginTop: 0 }}>Prediction</h3>
            <div className="list-item">
              <div style={{ fontWeight: 700 }}>Current performance</div>
              <div className="detail-copy" style={{ marginTop: '6px' }}>{analysis?.prediction?.current_performance ?? 75.4}</div>
            </div>
            <div className="list-item" style={{ marginTop: '12px' }}>
              <div style={{ fontWeight: 700 }}>Predicted future performance</div>
              <div className="detail-copy" style={{ marginTop: '6px' }}>{analysis?.prediction?.predicted_future_performance ?? 'Insufficient historical sessions for prediction.'}</div>
            </div>
          </div>
        </section>

        <section className="panel">
          <h3 style={{ marginTop: 0 }}>Session history</h3>
          <div className="list">
            {(sessions.length ? sessions : [{ id: 'sample', overall_score: 76.2, activity: 'Batting', sport: 'Cricket' }]).map((session, index) => (
              <div className="list-item" key={session.id || index}>
                <div className="card-row">
                  <strong>{session.activity || 'Batting'}</strong>
                  <span className="badge">{session.overall_score ?? 76.2}</span>
                </div>
                <div className="muted-copy" style={{ marginTop: '8px' }}>{session.sport || 'Cricket'}</div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
