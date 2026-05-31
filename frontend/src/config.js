// API base URL — set via Vite env vars
// .env.development → http://127.0.0.1:5000/
// .env.production  → <Lambda Function URL>
export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/';

// Sport type display config
export const SPORT_CONFIG = {
  Run:        { icon: '🏃', label: 'Carrera' },
  Ride:       { icon: '🚴', label: 'Ciclismo' },
  Swim:       { icon: '🏊', label: 'Natación' },
  Hike:       { icon: '🥾', label: 'Senderismo' },
  Walk:       { icon: '🚶', label: 'Caminata' },
  Workout:    { icon: '💪', label: 'Entreno' },
  Yoga:       { icon: '🧘', label: 'Yoga' },
  VirtualRun: { icon: '🖥️', label: 'Virtual' },
  default:    { icon: '⚡', label: 'Actividad' },
};

export function getSportConfig(sportType) {
  return SPORT_CONFIG[sportType] || SPORT_CONFIG.default;
}
