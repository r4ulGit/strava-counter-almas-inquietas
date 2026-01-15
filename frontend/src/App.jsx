import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css'

// ⚠️ PASTE YOUR LAMBDA BACKEND URL HERE (Function URL)
const API_URL = "https://4tmnmle654hfpiku73chw3p7ia0tbyjg.lambda-url.eu-west-1.on.aws/";

function App() {
  const [data, setData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(API_URL)
      .then(response => {
        if (!response.ok) {
            // Try to read the error message from the backend if possible
            return response.text().then(text => { throw new Error(text || 'Network response was not ok') })
        }
        return response.json();
      })
      .then(stravaData => {
        console.log("Data received from Backend:", stravaData); // Debugging line

        // Safety check: Ensure we received an Array
        if (!Array.isArray(stravaData)) {
            throw new Error("Backend format error: Expected a list of activities.");
        }

        setData(stravaData); 
        processDataForChart(stravaData); 
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching data:", error);
        setError(error.message);
        setLoading(false);
      });
  }, []);

  const processDataForChart = (items) => {
    // Safety check inside the function too
    if (!items || !Array.isArray(items)) return;

    const counts = {};
    items.forEach(item => {
      const type = item.type || 'Other';
      counts[type] = (counts[type] || 0) + 1;
    });

    const processed = Object.keys(counts).map(key => ({
      name: key,
      count: counts[key]
    }));
    
    setChartData(processed);
  }

  if (loading) return <h2>⏳ Loading Strava data...</h2>;
  if (error) return (
    <div style={{color: 'red', padding: '20px', border: '1px solid red'}}>
        <h2>❌ Error detected:</h2>
        <p>{error}</p>
        <p><small>Check the console (F12) for more details.</small></p>
    </div>
  );

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>📊 CONTADOR ALMAS INQUETAS</h1>
      
      <div style={{ marginBottom: '30px' }}>
        <h2>Total Activities: <span style={{ color: '#fc4c02' }}>{data.length}</span></h2>
      </div>

      <div style={{ width: '100%', height: 400 }}>
        <h3>Breakdown by Sport</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#ccc"/>
            <YAxis allowDecimals={false} stroke="#ccc"/> 
            <Tooltip cursor={false} contentStyle={{ border: '1px solid #ccc', borderRadius: 4, padding: 12 }}/>
            <Legend verticalAlign="top" height={36}/>
            <Bar dataKey="count" fill="#fc4c02" name="Activities" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h3>Recent Activities</h3>
      <ul>
        {data.slice(0, 5).map(act => (
          <li key={act.activity_id || act.strava_activities_id}>
             {act.type}: {act.name} ({act.distance_km} km)
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App