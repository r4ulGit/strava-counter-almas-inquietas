import React from 'react';
import ActivityCard from './ActivityCard.jsx';

/**
 * ActivityCarousel — Horizontally scrollable list of recent activity cards.
 * All activities received from the backend are shown (count controlled by LAST_ACT on server).
 */
function ActivityCarousel({ activities }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="carousel-section">
        <div className="section-title">
          <span className="section-icon">🏃</span>
          Últimas aportaciones
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Aún no hay actividades registradas.
        </p>
      </div>
    );
  }

  return (
    <div className="carousel-section">
      <div className="section-title">
        <span className="section-icon">🏃</span>
        Últimas aportaciones
        <span style={{
          marginLeft: 'auto',
          fontSize: '0.75rem',
          fontWeight: 400,
          color: 'var(--text-muted)',
        }}>
          {activities.length} actividades
        </span>
      </div>

      <div className="carousel-track">
        {activities.map((activity, index) => (
          <ActivityCard key={activity.id || index} activity={activity} />
        ))}
      </div>
    </div>
  );
}

export default ActivityCarousel;
