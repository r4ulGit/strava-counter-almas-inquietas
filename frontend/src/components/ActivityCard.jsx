import React from 'react';
import { getSportConfig } from '../config.js';

/**
 * ActivityCard — A single activity card in the carousel.
 * Displays: sport type badge, title, athlete name, distance, and date.
 * NO map/polyline — club API does not provide route data.
 */
function ActivityCard({ activity }) {
  const sport = getSportConfig(activity.sport_type || activity.type);

  const formattedDate = activity.date
    ? new Date(activity.date).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '—';

  return (
    <div className="activity-card">
      <div className="activity-card-type">
        <span>{sport.icon}</span>
        <span>{sport.label}</span>
      </div>

      <div className="activity-card-title" title={activity.title}>
        {activity.title || 'Actividad'}
      </div>

      <div className="activity-card-athlete">
        👤 {activity.athlete || '—'}
      </div>

      <div>
        <span className="activity-card-distance">
          {activity.distance_km?.toFixed(2) ?? '0.00'}
        </span>
        <span className="activity-card-distance-unit">km</span>
      </div>

      <div className="activity-card-date">{formattedDate}</div>
    </div>
  );
}

export default ActivityCard;
