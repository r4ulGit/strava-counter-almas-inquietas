import { useState, useEffect, useCallback } from 'react'
import './App.css'
import { API_URL } from './config.js'
import { getAuthHeader } from './apiAuth.js'
import ActivityCarousel from './components/ActivityCarousel.jsx'

// ---------------------------------------------------------------------------
// Medal helper
// ---------------------------------------------------------------------------
function getMedal(rank) {
  if (rank === 1) return { emoji: '🥇', cls: 'medal top-1' };
  if (rank === 2) return { emoji: '🥈', cls: 'medal top-2' };
  if (rank === 3) return { emoji: '🥉', cls: 'medal top-3' };
  return { emoji: String(rank), cls: '' };
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------
function LoadingSkeleton() {
  return (
    <div className="stagger">
      <div className="glass-card counter-section">
        <div className="skeleton skeleton-block" style={{ width: '40%', margin: '0 auto 12px' }} />
        <div className="skeleton skeleton-large" style={{ width: '70%', margin: '0 auto 16px' }} />
        <div className="skeleton skeleton-block" style={{ width: '100%' }} />
      </div>
      <div className="glass-card leaderboard-section">
        <div className="skeleton skeleton-block" style={{ width: '50%', marginBottom: 20 }} />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton skeleton-block" style={{ marginBottom: 10 }} />
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const authHeader = await getAuthHeader(API_URL);
      const headers = { 'Content-Type': 'application/json' };
      if (authHeader) headers['Authorization'] = authHeader;

      const response = await fetch(API_URL, { headers });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Error ${response.status}: ${text || response.statusText}`);
      }

      const json = await response.json();

      if (typeof json.total_km === 'undefined') {
        throw new Error("Respuesta inesperada del servidor.");
      }

      setData(json);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // --- Loading state ---
  if (loading) return (
    <div id="root">
      <header className="dashboard-header">
        <div className="logo-badge">
          <span className="live-dot" />
          ACTIVUM
        </div>
        <h1>ACTIVUM Rides the Wave</h1>
        <p className="subtitle">Cargando datos...</p>
      </header>
      <LoadingSkeleton />
    </div>
  );

  // --- Error state ---
  if (error) return (
    <div id="root">
      <header className="dashboard-header">
        <div className="logo-badge">⚠️ Error</div>
        <h1>ACTIVUM Rides the Wave</h1>
      </header>
      <div className="glass-card error-state">
        <h2>No se pudieron cargar los datos</h2>
        <p>{error}</p>
        <button className="btn-retry" onClick={fetchData} id="btn-retry">
          🔄 Reintentar
        </button>
      </div>
    </div>
  );

  // --- Data ---
  const goalKm = data.config?.goal_km ?? 500;
  const totalKm = data.total_km ?? 0;
  const percentage = Math.min(Math.max((totalKm / goalKm) * 100, 0), 100);
  const topAthletes = data.top_athletes ?? [];
  const lastActivities = data.last_activities ?? [];

  return (
    <div id="root">
      {/* ---- Header ---- */}
      <header className="dashboard-header">
        <div className="logo-badge">
          <span className="live-dot" />
          ACTIVUM
        </div>
        <h1>ACTIVUM Rides the Wave</h1>
        <p className="subtitle">
          Cada kilómetro recorrido cuenta. Juntos llegamos más lejos.
        </p>
      </header>

      <div className="stagger">

        {/* ---- KM Counter + Progress ---- */}
        <div className="glass-card counter-section">
          <div className="counter-label">Kilómetros recorridos</div>

          <div>
            <span className="counter-number" id="total-km-counter">
              {totalKm.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}
            </span>
            <span className="counter-unit">km</span>
          </div>

          <div className="progress-section">
            <div className="progress-labels">
              <span>0 km</span>
              <span className="goal-label">META: {goalKm.toLocaleString('es-ES')} km</span>
            </div>
            <div className="progress-track" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
              <div className="progress-fill" style={{ width: `${percentage}%` }} />
            </div>
            <p className="progress-pct">
              Progreso: <strong>{percentage.toFixed(1)}%</strong>
              {' '}·{' '}
              <span style={{ color: 'var(--text-muted)' }}>
                {data.total_activities} actividades registradas
              </span>
            </p>
          </div>
        </div>

        {/* ---- Leaderboard ---- */}
        <div className="glass-card leaderboard-section">
          <div className="section-title">
            <span className="section-icon">🏆</span>
            Ranking de atletas
            <span style={{
              marginLeft: 'auto',
              fontSize: '0.75rem',
              fontWeight: 400,
              color: 'var(--text-muted)',
            }}>
              Top 10
            </span>
          </div>

          {topAthletes.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Aún no hay atletas registrados.
            </p>
          ) : (
            <div className="athlete-list">
              {topAthletes.map((athlete, index) => {
                const rank = index + 1;
                const medal = getMedal(rank);
                return (
                  <div
                    key={athlete.athlete_name}
                    className={`athlete-row ${rank <= 3 ? `top-${rank}` : ''}`}
                    id={`athlete-row-${rank}`}
                  >
                    <div className={`athlete-rank ${medal.cls}`}>
                      {medal.emoji}
                    </div>

                    <div className="athlete-info">
                      <div className="athlete-name">{athlete.athlete_name}</div>
                      {athlete.lastIncrement > 0 && (
                        <div className="athlete-increment">
                          Última: <span>+{athlete.lastIncrement.toFixed(2)} km</span>
                        </div>
                      )}
                    </div>

                    <div>
                      <span className="athlete-km">
                        {athlete.currentKm.toLocaleString('es-ES', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                      <span className="athlete-km-unit">km</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ---- Activity Carousel ---- */}
        <ActivityCarousel activities={lastActivities} />

      </div>
    </div>
  );
}

export default App