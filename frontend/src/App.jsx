import { useState, useEffect } from 'react'
import './App.css'

// API CONFIGURATION
const API_URL = import.meta.env.DEV 
  ? "http://127.0.0.1:5000/" 
  : "https://4tmnmle654hfpiku73chw3p7ia0tbyjg.lambda-url.eu-west-1.on.aws/";

function App() {
  const [stats, setStats] = useState({ 
    total_km: 0, 
    matches_found: 0,
    last_5_act: [], // Inicializamos la lista vacía
    config: { goal_km: 500, filter_word: 'Run' } 
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- WIDGET DETECTION ---
  const searchParams = new URLSearchParams(window.location.search);
  const isWidget = searchParams.get('mode') === 'widget';

  useEffect(() => {
    fetch(API_URL)
      .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text || 'Network response was not ok') })
        }
        return response.json();
      })
      .then(data => {
        if (typeof data.total_km === 'undefined') {
             throw new Error("Backend format error: Missing 'total_km'.");
        }
        setStats(data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching data:", error);
        setError(error.message);
        setLoading(false);
      });
  }, []);

  const goal = stats.config?.goal_km || 500;
  const percentage = Math.min(Math.max((stats.total_km / goal) * 100, 0), 100);

  // --- STYLES FOR WIDGET MODE ---
  const containerStyle = isWidget ? {
    padding: '0px',
    backgroundColor: 'transparent',
    maxWidth: '100%'
  } : {
    marginTop: '40px', 
    padding: '40px', 
    backgroundColor: '#2a2a2a', 
    borderRadius: '15px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
    maxWidth: '800px',
    marginLeft: 'auto',
    marginRight: 'auto'
  };

  if (loading) return <h2 style={{color: isWidget ? '#333' : '#fff'}}>⏳ Loading...</h2>;
  if (error) return <div style={{color: 'red'}}>❌ Error: {error}</div>;

  return (
    <div style={{ 
        padding: isWidget ? '10px' : '40px', 
        fontFamily: 'Arial, sans-serif' 
    }}>
      {!isWidget && <h1>🏃‍♂️ Almas Inquietas Challenge</h1>}
      
      <div style={containerStyle}>
        
        {/* --- CONTADOR PRINCIPAL --- */}
        <h2 style={{ 
            fontSize: isWidget ? '1.2rem' : '1.8rem', 
            color: isWidget ? '#333' : '#ccc',
            margin: 0,
            textAlign: isWidget ? 'left' : 'center'
        }}>
          Total Distance
        </h2>
        
        <div style={{ 
            fontSize: isWidget ? '3.5rem' : '6rem',
            fontWeight: 'bold', 
            color: '#fc4c02', 
            margin: isWidget ? '10px 0' : '20px 0',
            lineHeight: 1,
            textAlign: isWidget ? 'left' : 'center'
        }}>
          {stats.total_km.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} 
          <span style={{fontSize: '1.5rem', color: isWidget ? '#555' : '#fff', marginLeft: '10px'}}>km</span>
        </div>

        {/* --- PROGRESS BAR SECTION --- */}
        <div style={{ marginTop: '30px', marginBottom: '20px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: isWidget ? '#666' : '#888', marginBottom: '10px', fontSize: '0.8rem', fontWeight: 'bold' }}>
                <span>0 km</span>
                <span>GOAL: {goal.toLocaleString()} km</span>
            </div>

            <div style={{ 
                height: '16px', 
                backgroundColor: isWidget ? '#e0e0e0' : '#444',
                borderRadius: '8px', 
                width: '100%',
                position: 'relative'
            }}>
                <div style={{ 
                    width: `${percentage}%`, 
                    height: '100%', 
                    backgroundColor: '#fc4c02', 
                    borderRadius: '8px',
                    transition: 'width 1s ease-in-out'
                }}></div>

                <div style={{ 
                    position: 'absolute', 
                    left: `${percentage}%`, 
                    top: '-30px', 
                    transform: 'translateX(-50%) scaleX(-1)', 
                    fontSize: '2rem',
                    transition: 'left 1s ease-in-out',
                    lineHeight: 1
                }}>
                    🏃
                </div>
            </div>

            <p style={{ marginTop: '10px', color: isWidget ? '#666' : '#aaa', fontSize: '0.9rem' }}>
                Progress: <strong style={{color: isWidget ? '#000' : '#fff'}}>{percentage.toFixed(1)}%</strong>
            </p>
        </div>
        
        {!isWidget && (
            <p style={{ fontSize: '1rem', color: '#666', marginTop: '30px' }}>
            Data collected from <strong style={{color: '#888'}}>{stats.matches_found}</strong> activities containing "<strong style={{color: '#fff'}}>{stats.config.filter_word}</strong>"
            </p>
        )}

        {/* --- ÚLTIMAS 5 ACTIVIDADES --- */}
        {stats.last_5_act && stats.last_5_act.length > 0 && (
          <div style={{ marginTop: '40px', textAlign: 'left' }}>
            <h3 style={{ 
                color: isWidget ? '#333' : '#ccc', 
                borderBottom: `1px solid ${isWidget ? '#ddd' : '#555'}`, 
                paddingBottom: '10px',
                fontSize: '1.2rem'
            }}>
              Últimas aportaciones
            </h3>
            
            <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
              {stats.last_5_act.map((act, index) => {
                // Formateamos la fecha para que se lea mejor (ej. 15/10/2023)
                const dateObj = new Date(act.date);
                const formattedDate = isNaN(dateObj) ? '' : dateObj.toLocaleDateString('es-ES');

                return (
                  <li key={index} style={{
                    backgroundColor: isWidget ? '#f9f9f9' : '#333',
                    padding: '15px',
                    borderRadius: '8px',
                    marginTop: '10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}>
                    <div style={{ paddingRight: '15px' }}>
                      <strong style={{ 
                          color: isWidget ? '#000' : '#fff', 
                          fontSize: '1rem', 
                          display: 'block', 
                          marginBottom: '4px' 
                      }}>
                        {act.title}
                      </strong>
                      <div style={{ color: '#888', fontSize: '0.85rem' }}>
                        {formattedDate} {act.athlete ? ` • 👤 ${act.athlete}` : ''}
                      </div>
                    </div>
                    <div style={{ 
                        fontWeight: 'bold', 
                        color: '#fc4c02', 
                        fontSize: '1.2rem',
                        whiteSpace: 'nowrap'
                    }}>
                      +{act.distance_km.toFixed(2)} km
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

      </div>
    </div>
  )
}

export default App